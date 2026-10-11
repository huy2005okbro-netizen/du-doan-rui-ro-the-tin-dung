# Ôn vấn đáp

## Leakage là gì?
Leakage là khi mô hình hoặc quyết định nhận thông tin không thể có tại thời điểm dự đoán, ví dụ fit scaler trên toàn dữ liệu hoặc chọn ngưỡng theo test. Nó làm hiệu năng ước lượng quá lạc quan.

## Vì sao không oversample trước split?
Bản sao/tổng hợp từ một quan sát có thể rơi vào cả train và validation/test, làm rò rỉ thông tin. Nếu dùng resampling, nó chỉ được thực hiện trong train/fold. Dự án này không dùng oversampling.

## Calibration khác discrimination thế nào?
Discrimination đo thứ tự xếp hạng, thường xem AP/ROC-AUC. Calibration xem xác suất ước lượng có phù hợp tần suất thực không, xem reliability diagram/Brier. Mô hình có thể xếp hạng tốt nhưng xác suất chưa tốt.

## AP và ROC-AUC khác nhau thế nào?
AP tóm tắt precision-recall, nhạy với lớp dương hiếm và là average precision trong báo cáo. ROC-AUC so sánh TPR-FPR qua ngưỡng. Không nên coi hai chỉ số là cùng một đại lượng.

## Vì sao ngưỡng 0.150?
Nó tối thiểu hóa chi phí validation theo kịch bản FP=1, FN=5 cho pipeline được chọn. Nó được khóa trước test. Kịch bản không phải chi phí ngân hàng thật.

## class_weight=balanced làm gì?
Nó tăng trọng số đóng góp của lớp hiếm trong hàm mất mát. Nó có thể tăng recall tại 0.5, nhưng không tự làm xác suất calibrated hay bảo đảm tốt hơn theo chi phí.

## Audit nhóm nói gì và không nói gì?
Audit báo performance theo nhóm SEX, EDUCATION, MARRIAGE. Nó cảnh báo chênh lệch hoặc nhóm nhỏ, nhưng không chứng minh công bằng hay quan hệ nhân quả.

## API dùng pipeline ra sao?
API nạp joblib đã freeze một lần khi startup, kiểm tra hash, xác thực 23 đầu vào rồi gọi predict_proba. Nó không train hoặc lưu input trong request.
