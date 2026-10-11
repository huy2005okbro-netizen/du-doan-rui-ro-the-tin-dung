# Tài liệu bổ sung Project 08

## 1. Kịch bản demo 5-7 phút

1. Nêu mục tiêu: dự đoán default tháng sau từ dữ liệu UCI, chỉ hỗ trợ nhắc thanh toán.
2. Nêu chống leakage: split 60/20/20, random_state 42, EDA train-only, Pipeline fit trong train/fold và test khóa.
3. Nêu baseline, thí nghiệm accuracy/recall/AP, calibration, ngưỡng chi phí và audit nhóm.
4. Mở Dashboard: validation và test tách biệt; thanh trượt chỉ minh họa validation.
5. Mở Mô phỏng: giải thích PAY_*, đơn vị tiền tệ, xác suất và ngưỡng 0.150.
6. Minh họa API hợp lệ và API từ chối ID/đầu vào sai; pipeline nạp một lần, input không lưu.
7. Kết thúc bằng giới hạn: chi phí giả định, trade-off precision/recall, nhóm ít mẫu, không dùng để quyết định tín dụng.

Phân bổ 12-15 phút: bối cảnh/dữ liệu/leakage 3 phút; phương pháp/thí nghiệm 4 phút; kết quả/giới hạn 3 phút; demo 2-5 phút.

## 2. Hỏi đáp vấn đáp

**Leakage là gì?** Là việc mô hình/ra quyết định nhận thông tin không có tại thời điểm dự đoán, ví dụ fit scaler trên toàn bộ dữ liệu hoặc chọn ngưỡng bằng test.

**Vì sao không oversample trước split?** Bản sao từ cùng quan sát có thể rơi vào train và validation/test, làm kết quả quá lạc quan. Nếu dùng resampling, chỉ dùng trong train/fold; dự án không dùng oversampling.

**Calibration khác discrimination?** Discrimination xem xếp hạng bằng AP/ROC-AUC; calibration xem xác suất có khớp tần suất thực bằng reliability diagram/Brier.

**AP và ROC-AUC?** AP tóm tắt precision-recall và phù hợp lớp dương hiếm; ROC-AUC so sánh TPR/FPR theo nhiều ngưỡng.

**Vì sao ngưỡng 0.150?** Nó tối thiểu chi phí validation với FP=1, FN=5 cho pipeline chọn; ngưỡng khóa trước test, không phải chi phí ngân hàng thật.

**class_weight=balanced?** Tăng trọng số lớp hiếm, có thể tăng recall tại 0.5 nhưng không tự đảm bảo calibration hay chi phí tốt hơn.

**Audit nhóm?** Báo hiệu năng theo SEX, EDUCATION, MARRIAGE; không chứng minh công bằng hay quan hệ nhân quả.

**API dùng pipeline ra sao?** API nạp joblib đã freeze lúc khởi động, kiểm tra 23 đầu vào rồi `predict_proba`; không train/lưu input.

## 3. Tái lập an toàn

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Đặt dữ liệu UCI theo `data/README.md`, sau đó chạy `python -m src.data prepare`, `python -m src.eda`, `python -m src.train`, `python -m src.evaluate`, `python -m src.experiments`.

Không chạy `python -m src.final_evaluation evaluate` trong bản bàn giao: test đã đóng băng trong `reports/final_test_evaluation.json`. Muốn thực hành đầy đủ, sao chép dự án sang thư mục khác.

```powershell
python -m src.build_web_data
uvicorn app.main:app --reload
python -m unittest tests.test_api
```

Mở `http://127.0.0.1:8000`.

## 4. Đối chiếu rubric

| Yêu cầu | Minh chứng | Trạng thái |
|---|---|---|
| Dữ liệu/schema/dictionary | `data/README.md`, `src/data.py`, báo cáo chất lượng | Có |
| Split/chống leakage | split manifest, `src/features.py`, `src/experiments.py` | Có |
| EDA train-only, baseline, metric | `src/eda.py`, `src/train.py`, `src/evaluate.py` | Có |
| CV, ngưỡng, audit, test freeze | `src/experiments.py`, freeze và final test JSON | Có |
| API/web | `app/main.py`, `app/static`, `tests/test_api.py` | Có |
| Nhật ký/phân công/tự đánh giá | Mẫu bên dưới | Cần điền bằng chứng thật |

## 5. Bảng phân công hai thành viên

| Hạng mục | Thành viên 1 | Thành viên 2 | Bằng chứng | Trạng thái |
|---|---|---|---|---|
| Dữ liệu, split, EDA | [BỔ SUNG] | [BỔ SUNG] |  |  |
| Mô hình và thí nghiệm | [BỔ SUNG] | [BỔ SUNG] |  |  |
| API/web | [BỔ SUNG] | [BỔ SUNG] |  |  |
| Báo cáo/slide/demo | [BỔ SUNG] | [BỔ SUNG] |  |  |
| Kiểm thử/bàn giao | [BỔ SUNG] | [BỔ SUNG] |  |  |

## 6. Nhật ký 6 tuần

| Tuần | Khoảng ngày | Mục tiêu | Việc đã làm | Bằng chứng/tệp/commit | Thời lượng | Vướng mắc | Người ghi |
|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |  |

## 7. Tự đánh giá

| Tiêu chí | Tự đánh giá | Dẫn chứng | Việc cần bổ sung |
|---|---|---|---|
| Hiểu dữ liệu và leakage |  |  |  |
| Thực hiện mô hình và đánh giá |  |  |  |
| Giải thích ngưỡng/chi phí |  |  |  |
| API/web và kiểm thử |  |  |  |
| Làm việc nhóm |  |  |  |
| Trình bày/vấn đáp |  |  |  |

## 8. Ghi nhận kiểm tra

Pipeline đã freeze: threshold 0.150; pipeline SHA-256 `804df95a7065bee41c11cbae479962e6b8bf912c6bfe252cae09a5fbb74b914a`. Test đã chạy một lần (`test_evaluation_count: 1`). Kiểm thử API trước bàn giao có request hợp lệ, input sai và model không khả dụng.

Trước khi nộp, mở lại Word/PDF/PPTX và chạy web trên máy nộp để kiểm tra hiển thị. Chỉ điền tên, giờ làm, phân công và commit có thật.
