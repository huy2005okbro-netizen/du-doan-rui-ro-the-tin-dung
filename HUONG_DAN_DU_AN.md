# Hướng dẫn dùng và bảo vệ Project 08

## 1. Mở và chạy web

Mở thư mục dự án trong VS Code, sau đó mở Terminal và chạy lần lượt:

```powershell
cd "C:\Users\trand\OneDrive\Documents\ChatGPT\Học máy cơ bản"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app
```

Mở trình duyệt tại `http://127.0.0.1:8000`. Khi Terminal hiện `(.venv)` là môi trường Python đã được kích hoạt đúng.

## 2. Kiểm thử an toàn

```powershell
python -m unittest tests.test_api
```

Lệnh này kiểm tra API. Không chạy `python -m src.final_evaluation evaluate` trong bản nộp vì test chính thức đã được đánh giá một lần và đóng băng.

## 3. Notebook và trình bày code

Mở `Rui_ro_the_tin_dung.ipynb` trong VS Code, chọn kernel `.venv`, sau đó chọn **Run All**. Notebook chỉ đọc dữ liệu/split/kết quả đã lưu; không train lại và không chạy lại test.

## 4. Luồng thuyết trình

1. Mở `deliverables/Project_08_trinh_bay.pptx`.
2. Nêu bài toán: ước lượng nguy cơ default tháng sau để hỗ trợ nhắc thanh toán, không quyết định cấp tín dụng.
3. Nêu dữ liệu UCI, split 60/20/20 và chống leakage.
4. Nêu baseline, Logistic Regression, C=1.0 và Pipeline.
5. Giải thích ngưỡng 0.150 được chọn bằng validation với chi phí FP=1/FN=5.
6. Nêu riêng kết quả test: recall 0.7340, AP 0.5254, ROC-AUC 0.7591.
7. Demo web: Giới thiệu, Mô phỏng, Dashboard. Thanh trượt dashboard chỉ minh họa validation.
8. Kết luận giới hạn: dữ liệu lịch sử, chi phí giả định, không suy luận nguyên nhân cá nhân và không tự động cấp/từ chối tín dụng.

## 5. Nộp bài

- Báo cáo: `deliverables/Project_08_bao_cao_ban_giao.docx` và `.pdf`.
- Slide: `deliverables/Project_08_trinh_bay.pptx`.
- Mã nguồn: `app/`, `src/`, `tests/`, `models/`, `reports/`.
- Điền thông tin thật trong `weekly_log_template.md`, `team_contribution_template.md` và `self_assessment_template.md` trước khi nộp.

## 6. GitHub

Sau khi hoàn thành phần việc thật, dùng `git status`, `git add .`, `git commit -m "..."` và `git push`. Không tạo commit lùi ngày hoặc nhật ký/đóng góp giả.
