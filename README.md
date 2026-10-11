# Sàng lọc nguy cơ trễ hạn thanh toán thẻ tín dụng

Project 08: nền tảng tái lập được để kiểm tra dữ liệu UCI, đóng băng train/validation/test, EDA trên train, baseline, thí nghiệm Logistic Regression, đánh giá test một lần và FastAPI/web. Đây là công cụ hỗ trợ chăm sóc khách hàng trong học tập, không dùng để tự động từ chối cấp tín dụng, xử phạt hoặc định giá cá nhân.

## Phạm vi hiện tại

- Tải dữ liệu chính thức UCI và lưu URL, ngày tải, giấy phép, SHA-256 cục bộ.
- Kiểm tra schema, kiểu, missing, ID/bản ghi trùng và mã giá trị chưa được tài liệu hóa; không âm thầm xóa hay recode dữ liệu.
- Chia stratified 60/20/20 với `random_state=42`, lưu CSV cùng manifest ID. Test được tạo nhưng **không được đọc** bởi train/evaluate của phase 1.
- EDA chỉ chạy trên `train.csv`.
- Baseline: luôn dự đoán không-default; Logistic Regression không `class_weight`, với median imputation + scaling cho biến liên tục và one-hot encoding cho biến phân loại. Toàn bộ preprocessing được fit trong Pipeline trên train.
- Phase 2: so sánh Logistic Regression không trọng số và `class_weight="balanced"`; chọn `C` bằng Stratified 5-fold CV trên train với cùng fold (`random_state=42`), sau đó thực hiện calibration, ngưỡng/chi phí và audit nhóm trên validation.
- Phase 3: đóng băng pipeline và checksum trước test; đánh giá test một lần; FastAPI và giao diện tiếng Việt chỉ nạp pipeline đã lưu để dự đoán.

## Cài đặt

Yêu cầu Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Chạy lại từ máy mới

```powershell
# 1. Tải, kiểm tra và đóng băng split (không commit dữ liệu thô)
python -m src.data prepare

# 2. EDA chỉ từ tập train
python -m src.eda

# 3. Fit baseline Phase 1 trên train và lưu pipeline
python -m src.train

# 4. Đánh giá baseline Phase 1 trên validation
python -m src.evaluate

# 5. Chạy toàn bộ thí nghiệm Phase 2: CV train + validation-only
python -m src.experiments

# 6. Chỉ sau khi đã duyệt lựa chọn Phase 2: đóng băng rồi đánh giá test một lần
python -m src.final_evaluation freeze
python -m src.final_evaluation evaluate

# 7. Tạo số liệu dashboard đã tổng hợp và mở web
python -m src.build_web_data
uvicorn app.main:app --reload
```

Nếu mạng không truy cập được UCI, xem cách đặt tệp chính thức vào `data/raw/` trong [data/README.md](data/README.md). Không dùng dữ liệu giả.

## Artefact sinh ra

- `data/raw/source_metadata.json`: URL, license, ngày tải và SHA-256.
- `reports/data_quality.json`: audit schema/chất lượng và cách xử lý.
- `data/processed/{train,validation,test}.csv` và `split_manifest.json`: split đóng băng; bị Git ignore vì có dữ liệu gốc.
- `reports/figures/`: hai biểu đồ EDA train và confusion matrix validation.
- `models/logistic_baseline.joblib`: pipeline đã fit từ train; `models/logistic_baseline_metadata.json` mô tả training.
- `reports/validation_baseline_metrics.{csv,json}`: kết quả validation.
- `models/logistic_{unweighted,balanced}_phase2.joblib`: hai pipeline đã refit từ toàn bộ train sau CV.
- `models/selected_phase2_pipeline.joblib`: bản pipeline được chọn trên validation, dùng làm đầu vào cho serving ở giai đoạn sau.
- `models/phase2_selection_metadata.json`: mô hình/ngưỡng được chọn, cost matrix, phiên bản thư viện và xác nhận test chưa dùng.
- `reports/phase2_experiment_report.md`: báo cáo CV, calibration, ngưỡng và audit nhóm từ kết quả chạy thực.
- `reports/model_card_draft.md`: phạm vi học tập, nguồn dữ liệu, mục đích hỗ trợ nhắc thanh toán và giới hạn.
- `models/final_selection_freeze.json`: lựa chọn cuối trước test, checksum pipeline, threshold, cost matrix và phiên bản thư viện.
- `reports/pretest_freeze_review.md`: đối chiếu leakage và chi phí validation tốt nhất của từng ứng viên.
- `reports/final_test_report.md`, `reports/model_card.md`: kết quả test và model card cuối; `final_test_evaluation.json` chặn ghi đè lần test sau.
- `app/main.py`, `app/static/`: FastAPI và giao diện Giới thiệu, Mô phỏng, Dashboard/Model card.

## Đánh giá

`PR-AUC` trong báo cáo là `average_precision_score` của scikit-learn: average precision, tóm tắt đường precision–recall theo các ngưỡng. Precision/recall/F1 sử dụng lớp default là lớp dương (`1`); khi không có dự đoán dương, precision được đặt `0` (`zero_division=0`) và điều đó phải được diễn giải. ROC-AUC và PR-AUC được ghi `null` khi không xác định (ví dụ tập đánh giá chỉ có một lớp). Brier score đo trung bình bình phương sai số của xác suất dự đoán.

Ngưỡng 0.5 chỉ là ngưỡng baseline cố định. Trong Phase 2, `C` được chọn bằng CV trên train; mô hình, calibration và threshold được chọn trên validation rồi ghi trong `reports/phase2_experiment_report.md`. Kịch bản chi phí FP=1, FN=5 chỉ phục vụ thí nghiệm, không phải chi phí thực của ngân hàng. Giai đoạn 3 đã dùng test đúng một lần sau freeze; kết quả nằm trong `reports/final_test_report.md`.

## Giai đoạn 3 và API

Sau khi freeze, `python -m src.final_evaluation evaluate` chỉ cho phép tạo một bộ kết quả test. Chạy lại sẽ bị từ chối thay vì ghi đè. API nạp pipeline đúng một lần lúc khởi động, không huấn luyện theo request và không lưu input vào tệp, database hoặc local storage.

Mở `http://127.0.0.1:8000` sau lệnh `uvicorn app.main:app --reload`. Tài liệu API có ở [app/API.md](app/API.md). Endpoint chính là `POST /api/risk-score`; chỉ nhận 23 đặc trưng, từ chối `ID`, target, trường thiếu, sai kiểu hoặc mã không hợp lệ. Giá trị hợp lệ nhưng ngoài miền train được trả về trong `outside_training_range`, không bị thay thế âm thầm.

## Kiểm tra web trên máy mới

Sau khi khởi động `uvicorn`, mở địa chỉ trên bằng trình duyệt laptop và thu hẹp cửa sổ đến kích thước điện thoại. Kiểm tra lần lượt:

- Giới thiệu: nguồn UCI, phạm vi học tập và giải thích PAY_*.
- Mô phỏng: form, lỗi nhập liệu, đơn vị tiền tệ theo bộ dữ liệu, cảnh báo ngoài miền train và kết quả dự đoán.
- Dashboard: validation/test hiển thị tách biệt; thanh trượt chỉ cập nhật bảng minh họa từ validation.

Chạy kiểm thử API tự động:

```powershell
python -m unittest tests.test_api
```

Các test bao phủ request hợp lệ, request có dữ liệu bị cấm/không hợp lệ và model không khả dụng. API không lưu input vào database, tệp, log ứng dụng hoặc local storage.

## Hồ sơ bàn giao giai đoạn 4

Thư mục [deliverables/](deliverables/) có báo cáo DOCX/PDF, deck 11 slide, kịch bản demo, hướng dẫn tái lập an toàn, mẫu nhật ký 6 tuần, bảng phân công hai thành viên, tự đánh giá, câu hỏi vấn đáp, danh sách sản phẩm và đối chiếu rubric. Các mẫu có trường trống `[BỔ SUNG]` vì dự án không tự suy đoán tên, giờ làm, phân công hay lịch sử công việc.

Không chạy lại `python -m src.final_evaluation evaluate` trong bản bàn giao: `reports/final_test_evaluation.json` là lần test chính thức duy nhất và chương trình sẽ từ chối ghi đè. Nếu cần diễn tập toàn bộ luồng, sao chép dự án sang thư mục khác rồi làm việc ở bản sao. Xem [deliverables/reproducibility.md](deliverables/reproducibility.md).

## Cấu trúc

```text
data/README.md                 # nguồn, license, dictionary, hướng dẫn tái tạo
src/data.py                    # download, audit, split đóng băng
src/features.py                # feature list và preprocessing
src/eda.py                     # EDA train-only
src/train.py                   # train Logistic Regression offline
src/evaluate.py                # validation-only baseline metrics
src/experiments.py             # CV trên train và thí nghiệm validation-only Phase 2
src/final_evaluation.py        # pre-test freeze và final test một lần
src/build_web_data.py          # dashboard aggregate và miền giá trị train
app/main.py                    # FastAPI chỉ serving pipeline đã đóng băng
models/                        # pipeline local, ignored
reports/figures/               # chart local, ignored
app/                           # sẽ dành cho FastAPI và giao diện giai đoạn sau
```
