# Dữ liệu

Nguồn chính thức: UCI Machine Learning Repository, **Default of Credit Card Clients** (ID 350), https://archive.ics.uci.edu/dataset/350/default%2Bof%2Bcredit%2Bcard%2Bclients. DOI: https://doi.org/10.24432/C55S3H. Giấy phép: CC BY 4.0.

Không đưa dữ liệu thô vào Git. Chạy `python -m src.data download` để tải archive chính thức, rồi `python -m src.data prepare` để kiểm tra và tạo split. Script lưu ngày tải và SHA-256 của archive/tệp dữ liệu trong `data/raw/source_metadata.json`.

## Nguồn gốc tệp và tệp dùng để huấn luyện

- **Tệp đã dùng để tạo split và huấn luyện hiện tại:** `data/raw/default of credit card clients.xls`. Script đã tải tệp này từ archive chính thức của UCI và lưu nguồn, thời điểm tải cùng SHA-256 trong `data/raw/source_metadata.json`.
- **Tệp đối chiếu do người dùng cung cấp:** `UCI_Credit_Card (2).csv`, được người dùng cho biết đã tải từ Kaggle. Tệp này chỉ được dùng để đối chiếu, không thay thế tệp UCI trong pipeline và không được ghi là tải trực tiếp từ UCI.
- **Kết quả đối chiếu ngày 2026-10-08:** sau khi chuẩn hóa nhãn target CSV `default.payment.next.month` thành `default_payment_next_month`, hai tệp có cùng 30.000 ID, cùng 25 cột và không có giá trị khác biệt ở bất kỳ cột nào, gồm target. CSV biểu diễn `LIMIT_BAL`, `BILL_AMT*` và `PAY_AMT*` là số thực, trong khi XLS UCI biểu diễn các giá trị tương đương là số nguyên; đây là khác biệt định dạng, không phải khác biệt nội dung.
- Không suy đoán giấy phép, chủ sở hữu hoặc URL của trang Kaggle vì các thông tin đó không được cung cấp cùng tệp CSV.

Nếu máy không tải được: tải archive từ URL UCI ở trên, giải nén đúng một tệp `.xls`, `.xlsx`, hoặc `.csv` vào `data/raw/`, sau đó chạy `python -m src.data prepare`. Không thay thế bằng dữ liệu tổng hợp.

## Data dictionary

| Nhóm | Biến | Kiểu/vai trò | Diễn giải |
|---|---|---|---|
| Định danh | `ID` | ID, không dùng làm feature | Mã khách hàng; chỉ dùng để kiểm tra trùng và đóng băng split. |
| Nhân khẩu | `LIMIT_BAL`, `SEX`, `EDUCATION`, `MARRIAGE`, `AGE` | Feature | Hạn mức (NT$); giới tính (1 nam, 2 nữ); học vấn (1 cao học, 2 đại học, 3 trung học, 4 khác); hôn nhân (1 đã kết hôn, 2 độc thân, 3 khác); tuổi (năm). |
| Lịch sử trả nợ | `PAY_0`, `PAY_2`…`PAY_6` | Feature phân loại | Trạng thái trả nợ từ tháng 9 đến tháng 4/2005. Theo mô tả UCI: `-2` không tiêu dùng, `-1` trả đúng hạn, `0` dùng tín dụng quay vòng, `1` trễ 1 tháng … `9` trễ từ 9 tháng trở lên. Các mã quan sát được được báo cáo, không tự chuyển đổi. |
| Sao kê | `BILL_AMT1`…`BILL_AMT6` | Feature số | Số dư sao kê tháng 9 đến tháng 4/2005 (NT$). |
| Thanh toán | `PAY_AMT1`…`PAY_AMT6` | Feature số | Số tiền thanh toán trước đó, tháng 9 đến tháng 4/2005 (NT$). |
| Nhãn | `default_payment_next_month` | Target nhị phân | Có default tháng sau (1) hoặc không (0). |

`EDUCATION=0,5,6` và `MARRIAGE=0` không nằm trong tập mã mô tả chính thức; phase 1 chỉ ghi nhận và giữ nguyên các dòng này. Không xóa hàng, không điền thay hay oversample. Các imputer/encoder/scaler được fit trong Pipeline trên train.
