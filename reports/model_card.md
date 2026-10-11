# Model card

## Mục đích và giới hạn sử dụng
Mô hình chỉ phục vụ học tập và hỗ trợ ưu tiên nhắc thanh toán/tư vấn tài chính. Không dùng để tự động từ chối tín dụng, xử phạt, định giá cá nhân hoặc suy luận nguyên nhân cá nhân.

## Dữ liệu và target
Dữ liệu lịch sử UCI Default of Credit Card Clients; target `default_payment_next_month=1` là default tháng sau trong dữ liệu gốc.

## Pipeline đã đóng băng
Logistic Regression không `class_weight`, C=1.0; imputation/scaling/one-hot trong pipeline; không hiệu chỉnh xác suất. Ngưỡng `0.150` lấy từ validation, không từ test. Chi phí giả định FP=1, FN=5, TP=TN=0.

## Hiệu năng test
Accuracy 0.6452; precision 0.3542; recall 0.7340; F1 0.4778; AP 0.5254; ROC-AUC 0.7591; Brier 0.1388. Chi phí giả định 3541, hay 0.5902/khách hàng.

## Hạn chế
Dữ liệu lịch sử có thể không đại diện cho nơi/thời kỳ khác. Các mã EDUCATION/MARRIAGE chưa rõ nghĩa được giữ nguyên. Calibration và sai số theo nhóm có thể thay đổi ngoài dữ liệu này; không kết luận công bằng từ một chỉ số.
