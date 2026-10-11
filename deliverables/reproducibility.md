# Tái lập an toàn

## Môi trường mới

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Đặt tệp UCI chính thức theo hướng dẫn trong `data/README.md`, rồi chạy `python -m src.data prepare`, `python -m src.eda`, `python -m src.train`, `python -m src.evaluate`, `python -m src.experiments`.

## Bảo toàn đánh giá test chính thức

Bản bàn giao chứa `reports/final_test_evaluation.json` và `models/final_selection_freeze.json`. Không chạy lại `python -m src.final_evaluation evaluate` trong cùng thư mục vì mã chủ ý chặn ghi đè. Để thực hành đầy đủ, sao chép toàn bộ dự án sang thư mục mới hoặc clone vào thư mục riêng, sau đó tạo đầu ra mới ở bản sao. Không đổi threshold 0.150, pipeline hash hay cấu hình freeze nếu mục tiêu là đối chiếu kết quả đã báo cáo.

## Web/API

```powershell
python -m src.build_web_data
uvicorn app.main:app --reload
python -m unittest tests.test_api
```

Mở `http://127.0.0.1:8000`. Chỉ chạy các bước huấn luyện trên bản sao sạch có dữ liệu UCI hợp lệ.
