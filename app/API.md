# API risk score

Khởi động từ thư mục dự án:

```powershell
python -m src.build_web_data
uvicorn app.main:app --reload
```

`POST /api/risk-score` nhận đúng 23 feature của pipeline. Không gửi `ID` hoặc `default_payment_next_month`.

```json
{
  "LIMIT_BAL": 50000,
  "SEX": 2,
  "EDUCATION": 2,
  "MARRIAGE": 1,
  "AGE": 30,
  "PAY_0": 0,
  "PAY_2": 0,
  "PAY_3": 0,
  "PAY_4": 0,
  "PAY_5": 0,
  "PAY_6": 0,
  "BILL_AMT1": 12000,
  "BILL_AMT2": 11000,
  "BILL_AMT3": 10000,
  "BILL_AMT4": 9000,
  "BILL_AMT5": 8000,
  "BILL_AMT6": 7000,
  "PAY_AMT1": 3000,
  "PAY_AMT2": 3000,
  "PAY_AMT3": 3000,
  "PAY_AMT4": 3000,
  "PAY_AMT5": 3000,
  "PAY_AMT6": 3000
}
```

Ví dụ response thành công:

```json
{
  "probability_default": 0.12,
  "threshold": 0.15,
  "alert": false,
  "alert_group": "khong_canh_bao",
  "model_version": "804df95a7065",
  "outside_training_range": [],
  "warning": null
}
```

- `422`: thiếu trường, kiểu không phải số nguyên, mã `SEX`/`EDUCATION`/`MARRIAGE`/`PAY_*` sai, giá trị âm ở hạn mức hoặc khoản thanh toán, hay gửi thêm `ID`/target.
- `503`: pipeline đóng băng không sẵn sàng hoặc checksum không khớp.
- `GET /api/health`: trạng thái model.
- `GET /api/dashboard`: chỉ trả số liệu đánh giá tổng hợp phục vụ giao diện.

Các giá trị hợp lệ nhưng nằm ngoài min/max hoặc ngoài tập mã đã quan sát trên train không bị từ chối; response ghi rõ chúng trong `outside_training_range` để người dùng không coi dự đoán là trong miền dữ liệu học.
