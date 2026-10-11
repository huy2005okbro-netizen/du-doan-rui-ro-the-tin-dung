# Báo cáo thí nghiệm Giai đoạn 2

Ngày chạy (UTC): 2026-10-09T15:32:20.881569+00:00

## Thiết kế không rò rỉ

Tập train đóng băng được dùng cho Stratified 5-fold CV (`random_state=42`, shuffle). Mỗi candidate là một Pipeline gồm imputer, scaler/one-hot encoder và Logistic Regression; do đó mọi bước học dữ liệu được fit lại trong từng fold train. Validation chỉ dùng sau CV để so sánh mô hình, xác suất và ngưỡng. Tệp test không được mở bởi module này.

## Chọn C bằng CV trên train

| model | class_weight | C | mean_cv_average_precision | std_cv_average_precision | rank |
| --- | --- | --- | --- | --- | --- |
| logistic_balanced | balanced | 1.0000 | 0.5455 | 0.0216 | 1 |
| logistic_balanced | balanced | 10.0000 | 0.5435 | 0.0204 | 2 |
| logistic_balanced | balanced | 0.1000 | 0.5428 | 0.0243 | 3 |
| logistic_balanced | balanced | 0.0100 | 0.5351 | 0.0268 | 4 |
| logistic_unweighted | none | 1.0000 | 0.5482 | 0.0198 | 1 |
| logistic_unweighted | none | 10.0000 | 0.5461 | 0.0184 | 2 |
| logistic_unweighted | none | 0.1000 | 0.5443 | 0.0228 | 3 |
| logistic_unweighted | none | 0.0100 | 0.5360 | 0.0255 | 4 |

CV tối đa hóa `average_precision` của scikit-learn, không phải tích phân hình thang của đường precision-recall.

## Kết quả validation ở ngưỡng 0.5

| model | selected_C | accuracy | precision_default | recall_default | f1_default | pr_auc_average_precision | pr_auc_trapezoidal | roc_auc | brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_unweighted | 1.0000 | 0.8207 | 0.6882 | 0.3459 | 0.4604 | 0.5372 | 0.5367 | 0.7630 | 0.1368 |
| logistic_balanced | 1.0000 | 0.7780 | 0.4984 | 0.5727 | 0.5330 | 0.5369 | 0.5364 | 0.7628 | 0.1832 |

`pr_auc_average_precision` là Average Precision (`average_precision_score`). `pr_auc_trapezoidal` chỉ được ghi riêng để tránh đồng nhất nó với AP. Accuracy có thể cao khi lớp non-default chiếm đa số và mô hình bỏ sót nhiều default; vì vậy lựa chọn không dựa vào accuracy đơn lẻ.

## Calibration

Đã đánh giá reliability diagram và Brier score của **xác suất gốc** cho cả hai mô hình. Không áp dụng hiệu chỉnh xác suất ở giai đoạn này: không có phương án calibrated nào được dùng để chọn ngưỡng hay phục vụ. Xác suất từ `class_weight=balanced` không được mặc định là đã calibrated.

## Kịch bản chi phí và ngưỡng

Kịch bản giả định phục vụ bài tập, **không phải chi phí thực của ngân hàng**: TN=0, FP=1, FN=5, TP=0. Nếu xác suất được calibrated, ngưỡng lý thuyết là FP / (FP + FN) = 0.166667. Ngưỡng validation được chọn bằng cách tối thiểu hóa tổng chi phí giả định trên lưới 0.001, chỉ cho mô hình đã chọn.

| threshold_role | threshold | tn | fp | fn | tp | precision_default | recall_default | f1_default | total_assumed_cost | assumed_cost_per_customer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fixed_0.5 | 0.5000 | 4465 | 208 | 868 | 459 | 0.6882 | 0.3459 | 0.4604 | 4548 | 0.7580 |
| cost_theoretical | 0.1667 | 3290 | 1383 | 419 | 908 | 0.3963 | 0.6843 | 0.5019 | 3478 | 0.5797 |
| validation_cost_minimum | 0.1500 | 2938 | 1735 | 334 | 993 | 0.3640 | 0.7483 | 0.4898 | 3405 | 0.5675 |

Giảm ngưỡng thường tăng recall và giảm FN, nhưng có thể tăng FP, số cảnh báo nhầm và chi phí FP. Ngưỡng được chọn là 0.150; kết quả này chỉ hợp lệ cho validation hiện tại và phải được đóng băng trước khi dùng test.

## Audit theo nhóm trên validation

| group_column | group_value | sample_count | default_count | recall_tpr | fnr | fpr | precision | brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEX | 1 | 2385 | 607 | 0.7941 | 0.2059 | 0.4353 | 0.3838 | 0.1541 |
| SEX | 2 | 3615 | 720 | 0.7097 | 0.2903 | 0.3320 | 0.3471 | 0.1254 |
| EDUCATION | 0 | 1 | 0 | undefined | undefined | 0.0000 | undefined | 0.0043 |
| EDUCATION | 1 | 2084 | 416 | 0.6995 | 0.3005 | 0.3333 | 0.3436 | 0.1329 |
| EDUCATION | 2 | 2838 | 663 | 0.7753 | 0.2247 | 0.4005 | 0.3711 | 0.1387 |
| EDUCATION | 3 | 977 | 241 | 0.7676 | 0.2324 | 0.4090 | 0.3807 | 0.1470 |
| EDUCATION | 4 | 29 | 1 | 0.0000 | 1.0000 | 0.0357 | 0.0000 | 0.0346 |
| EDUCATION | 5 | 62 | 4 | 0.5000 | 0.5000 | 0.0862 | 0.2857 | 0.0605 |
| EDUCATION | 6 | 9 | 2 | 0.5000 | 0.5000 | 0.1429 | 0.5000 | 0.2105 |
| MARRIAGE | 0 | 17 | 1 | 0.0000 | 1.0000 | 0.1875 | 0.0000 | 0.0746 |
| MARRIAGE | 1 | 2755 | 667 | 0.7811 | 0.2189 | 0.4042 | 0.3817 | 0.1454 |
| MARRIAGE | 2 | 3161 | 639 | 0.7105 | 0.2895 | 0.3386 | 0.3471 | 0.1291 |
| MARRIAGE | 3 | 67 | 20 | 0.9000 | 0.1000 | 0.7234 | 0.3462 | 0.1630 |

Các mã `EDUCATION` và `MARRIAGE` không được tài liệu nguồn diễn giải vẫn được giữ là nhóm mã riêng. `undefined` nghĩa là mẫu nhóm không có mẫu số cần thiết (ví dụ không có default hoặc không có dự đoán dương). Nhóm nhỏ cần được diễn giải thận trọng. Audit này không chứng minh công bằng, không xác lập quan hệ nhân quả và không đủ để quyết định sử dụng trên cá nhân.

## Lựa chọn đã đóng băng cho giai đoạn sau

- Model: `logistic_unweighted`.
- Calibration: không áp dụng; dùng xác suất gốc và đã báo cáo Brier/reliability.
- Threshold: `0.150`, được chọn trên validation theo kịch bản chi phí giả định.
- Test: chưa chạy.
