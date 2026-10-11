# Đối chiếu rubric 100 điểm

| Nhóm yêu cầu | Minh chứng hiện có | Tình trạng |
|---|---|---|
| Nguồn dữ liệu, schema, dictionary | data/README.md, src/data.py, reports/data_quality.json | Có |
| Split cố định và chống leakage | data/processed/split_manifest.json, src/features.py, src/experiments.py, reports/pretest_freeze_review.md | Có |
| EDA train-only | src/eda.py, reports/figures/train_target_distribution.png | Có |
| Baseline và metric validation | src/train.py, src/evaluate.py, reports/validation_baseline_metrics.csv | Có |
| CV, class_weight, calibration, ngưỡng, audit | src/experiments.py, reports/phase2_experiment_report.md, reports/phase2_validation_* | Có |
| Freeze và test một lần | models/final_selection_freeze.json, src/final_evaluation.py, reports/final_test_evaluation.json | Có |
| API và giao diện | app/main.py, app/static/, tests/test_api.py, app/API.md | Có, cần chạy trên máy nộp |
| Báo cáo/slide/demo | deliverables/Project_08_bao_cao_ban_giao.*, deliverables/Project_08_trinh_bay.pptx, deliverables/demo_script.md | Có sau khi tạo |
| Nhật ký, phân công, tự đánh giá | deliverables/*_template.md | Mẫu trống, cần người dùng điền bằng chứng |

## Phần còn thiếu cần người nộp bổ sung

- Tên thành viên, vai trò thực tế, nhật ký thời gian và bằng chứng làm việc.
- Tên môn học, giảng viên/lớp và yêu cầu định dạng bìa nếu có.
- Xác nhận kiểm tra giao diện trên laptop/điện thoại của máy nộp. Môi trường Codex hiện không cho trình duyệt kết nối localhost.
- Điểm rubric cụ thể nếu đề gốc chia điểm khác bảng đối chiếu này. Không tự gán điểm 100/100.
