# Kịch bản demo 5-7 phút

## Mục tiêu
Trình diễn quy trình dữ liệu đến cảnh báo, không trình bày hệ thống như công cụ quyết định tín dụng.

## Kịch bản

1. **0:00-0:45 - Bối cảnh.** Nêu target default tháng sau, nguồn UCI và mục tiêu hỗ trợ nhắc thanh toán.
2. **0:45-1:45 - Chống leakage.** Chỉ ra split 60/20/20, random_state=42, EDA train-only, Pipeline fit trong train/fold và test bị khóa.
3. **1:45-2:45 - Baseline và thí nghiệm.** So sánh accuracy với recall/AP, reliability, ngưỡng chi phí giả định và audit nhóm.
4. **2:45-3:45 - Dashboard.** Mở Dashboard, chỉ rõ validation và test tách biệt. Kéo ngưỡng minh họa: chỉ số đang thay đổi là validation, không phải chọn lại bằng test.
5. **3:45-5:15 - Mô phỏng.** Mở form, giải thích PAY_* và đơn vị tiền tệ. Nhập ví dụ synthetic, nhận xác suất, threshold 0.150 và cảnh báo. Cho một ví dụ ngoài miền train để thấy cảnh báo.
6. **5:15-6:15 - API và an toàn.** Minh họa request hợp lệ, request có ID bị từ chối. Nêu pipeline chỉ nạp một lần và input không được lưu.
7. **6:15-7:00 - Giới hạn.** Nhấn mạnh chi phí giả định, precision/recall trade-off, nhóm ít mẫu và không sử dụng cho quyết định cấp tín dụng.

## Phân bổ buổi trình bày 12-15 phút

- Bối cảnh, dữ liệu và leakage: 3 phút
- Phương pháp, baseline và bốn thí nghiệm: 4 phút
- Kết quả validation/test và giới hạn: 3 phút
- Demo web/API: 5-7 phút
- Tổng: 15 phút nếu demo 5 phút; có thể rút phần demo còn 2 phút để đạt 12 phút.
