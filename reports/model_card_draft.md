# Model card nháp

## Mục đích và phạm vi

Mô hình hỗ trợ học tập cho việc ưu tiên nhắc thanh toán hoặc tư vấn tài chính. Nó không dùng để tự động từ chối tín dụng, xử phạt, định giá cá nhân hay đưa ra quyết định tín dụng.

## Dữ liệu

Huấn luyện từ `data/raw/default of credit card clients.xls`, tải từ UCI Default of Credit Card Clients. Tệp CSV Kaggle do người dùng cung cấp đã được đối chiếu nội dung và chỉ dùng để đối chiếu; không phải nguồn huấn luyện. Target là `default_payment_next_month`.

## Mô hình và quyết định hiện tại

`logistic_unweighted` với Pipeline imputation, scaling/one-hot encoding và Logistic Regression. C được chọn bằng CV trên train. Không hiệu chỉnh xác suất. Ngưỡng `0.150` tối thiểu hóa kịch bản chi phí giả định FP=1, FN=5 trên validation; đó không phải chi phí của ngân hàng.

## Giới hạn

- Dữ liệu lịch sử, phạm vi một bộ dữ liệu học tập; có thể không đại diện cho khách hàng hoặc thời gian khác.
- Một số mã EDUCATION/MARRIAGE chưa được tài liệu nguồn giải thích và được giữ nguyên.
- Calibration, sai số theo nhóm và ngưỡng có thể dịch chuyển ngoài validation.
- Chưa dùng tập test; mọi kết quả test phải chờ lựa chọn hiện tại được khóa.
