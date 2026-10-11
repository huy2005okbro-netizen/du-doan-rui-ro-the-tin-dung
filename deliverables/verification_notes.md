# Ghi nhận kiểm tra bàn giao

## Bất biến mô hình/test

- `models/final_selection_freeze.json` vẫn có timestamp `2026-10-08T14:19:41.066752+00:00`, threshold `0.150` và pipeline SHA-256 `804df95a7065bee41c11cbae479962e6b8bf912c6bfe252cae09a5fbb74b914a`.
- `reports/final_test_evaluation.json` vẫn có timestamp `2026-10-08T14:20:49.313125+00:00` và `test_evaluation_count: 1`.
- Không gọi lại lệnh đánh giá test trong giai đoạn bàn giao.

## Kiểm tra đã thực hiện

- `py_compile` cho `app/main.py`, `src/final_evaluation.py` và trình tạo bàn giao thành công.
- Kiểm tra cấu trúc: PDF có 18 trang; DOCX chứa `[Content_Types].xml`; PPTX có 11 slide XML.
- Rà soát mã giao diện xác nhận có responsive breakpoint 720px, bảng bọc `overflow:auto`, dashboard dùng dữ liệu validation cho thanh trượt, và endpoint phản hồi cảnh báo `outside_training_range`.
- Trước giai đoạn này, bộ `tests.test_api` đã chạy thành công 3 test: request hợp lệ/cảnh báo ngoài miền, input không hợp lệ và model không khả dụng.

## Giới hạn môi trường cần chạy lại trên máy nộp

- Trình duyệt của môi trường Codex không kết nối được localhost (`ERR_CONNECTION_REFUSED`) và lời gọi HTTP nội bộ bị chặn quyền socket, nên không thể thao tác trực tiếp cả ba màn hình ở đây.
- Renderer DOCX yêu cầu LibreOffice (`soffice.exe`) nhưng môi trường thiếu công cụ này. Poppler cũng không có. PDF được tạo bằng ReportLab và xác nhận cấu trúc/số trang, nhưng ảnh raster từng trang không thể sinh tại đây.
- Bộ finalizer PPTX bị sandbox chặn tại `realpath`; deck vẫn được xuất từ Artifact Tool và có kiểm tra cấu trúc 11 slide. Mở/kiểm tra trực quan PPTX và DOCX/PDF trên máy nộp trước khi nộp là bước còn lại.
