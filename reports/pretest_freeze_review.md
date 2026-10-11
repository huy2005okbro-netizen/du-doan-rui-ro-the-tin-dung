# Rà soát và đóng băng trước test

- Pipeline chứa toàn bộ preprocessing, vì vậy imputer/scaler/encoder chỉ fit trong train hoặc fold CV.
- CV Phase 2 là Stratified 5-fold trên train với `random_state=42`; validation chỉ dùng sau CV.
- Ngưỡng 0.150 đúng là chi phí validation tối thiểu theo kịch bản giả định FP=1, FN=5, TP=TN=0 trên lưới 0.001.
- Chênh lệch AP khoảng 0.0004 không là bằng chứng vượt trội rõ rệt. Mô hình không trọng số được giữ vì chi phí validation tốt hơn và Brier thấp hơn trong lựa chọn đã ghi.

## Chi phí validation tại ngưỡng tốt nhất của từng ứng viên

| model | validation_cost_minimum_threshold | total_assumed_cost | assumed_cost_per_customer | pr_auc_average_precision | brier_score | recall_default | precision_default |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_unweighted | 0.1500 | 3405 | 0.5675 | 0.5372 | 0.1368 | 0.7483 | 0.3640 |
| logistic_balanced | 0.3730 | 3430 | 0.5717 | 0.5369 | 0.1832 | 0.7604 | 0.3542 |

Pipeline đóng băng: `models/selected_phase2_pipeline.joblib`; SHA-256: `804df95a7065bee41c11cbae479962e6b8bf912c6bfe252cae09a5fbb74b914a`. Test chưa được mở khi tạo freeze.
