import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import ROOT, create_app

VALID_PAYLOAD = {
    "LIMIT_BAL": 50000, "SEX": 2, "EDUCATION": 2, "MARRIAGE": 1, "AGE": 30,
    "PAY_0": 0, "PAY_2": 0, "PAY_3": 0, "PAY_4": 0, "PAY_5": 0, "PAY_6": 0,
    "BILL_AMT1": 12000, "BILL_AMT2": 11000, "BILL_AMT3": 10000, "BILL_AMT4": 9000, "BILL_AMT5": 8000, "BILL_AMT6": 7000,
    "PAY_AMT1": 3000, "PAY_AMT2": 3000, "PAY_AMT3": 3000, "PAY_AMT4": 3000, "PAY_AMT5": 3000, "PAY_AMT6": 3000,
}


class ApiTests(unittest.TestCase):
    def test_success_and_outside_train_warning(self):
        payload = dict(VALID_PAYLOAD); payload["AGE"] = 120
        with TestClient(create_app()) as client:
            response = client.post("/api/risk-score", json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertIn("probability_default", response.json())
            self.assertNotIn("ID", response.json())
            self.assertTrue(any(item["field"] == "AGE" for item in response.json()["outside_training_range"]))

    def test_invalid_input_is_rejected(self):
        payload = dict(VALID_PAYLOAD); payload["SEX"] = 3; payload["ID"] = 99
        with TestClient(create_app()) as client:
            response = client.post("/api/risk-score", json=payload)
            self.assertEqual(response.status_code, 422)

    def test_model_unavailable(self):
        with TestClient(create_app(ROOT / "models" / "missing.joblib")) as client:
            response = client.post("/api/risk-score", json=VALID_PAYLOAD)
            self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
