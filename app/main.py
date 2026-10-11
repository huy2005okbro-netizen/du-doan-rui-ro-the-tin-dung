"""Serve the frozen risk-score pipeline without retaining request inputs."""
from __future__ import annotations

import hashlib
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
STATIC_DIR = APP_DIR / "static"
RANGES_PATH = APP_DIR / "training_ranges.json"
FREEZE_PATH = ROOT / "models" / "final_selection_freeze.json"
DEFAULT_MODEL_PATH = ROOT / "models" / "selected_phase2_pipeline.joblib"

StrictPositive = Annotated[int, Field(strict=True, gt=0)]
StrictNonNegative = Annotated[int, Field(strict=True, ge=0)]
StrictInteger = Annotated[int, Field(strict=True)]
PAY_COLUMNS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL_COLUMNS = ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]
PAYMENT_COLUMNS = ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]


class RiskInput(BaseModel):
    """Exactly the 23 pipeline features; unknown fields such as ID/target are rejected."""
    model_config = ConfigDict(extra="forbid", strict=True)
    LIMIT_BAL: StrictPositive
    SEX: StrictInteger
    EDUCATION: StrictInteger
    MARRIAGE: StrictInteger
    AGE: StrictPositive
    PAY_0: StrictInteger
    PAY_2: StrictInteger
    PAY_3: StrictInteger
    PAY_4: StrictInteger
    PAY_5: StrictInteger
    PAY_6: StrictInteger
    BILL_AMT1: StrictInteger
    BILL_AMT2: StrictInteger
    BILL_AMT3: StrictInteger
    BILL_AMT4: StrictInteger
    BILL_AMT5: StrictInteger
    BILL_AMT6: StrictInteger
    PAY_AMT1: StrictNonNegative
    PAY_AMT2: StrictNonNegative
    PAY_AMT3: StrictNonNegative
    PAY_AMT4: StrictNonNegative
    PAY_AMT5: StrictNonNegative
    PAY_AMT6: StrictNonNegative

    @field_validator("SEX")
    @classmethod
    def validate_sex(cls, value: int) -> int:
        if value not in {1, 2}:
            raise ValueError("SEX must be 1 or 2 according to the source coding.")
        return value

    @field_validator("EDUCATION")
    @classmethod
    def validate_education(cls, value: int) -> int:
        if value not in {0, 1, 2, 3, 4, 5, 6}:
            raise ValueError("EDUCATION must be one of 0, 1, 2, 3, 4, 5, 6.")
        return value

    @field_validator("MARRIAGE")
    @classmethod
    def validate_marriage(cls, value: int) -> int:
        if value not in {0, 1, 2, 3}:
            raise ValueError("MARRIAGE must be one of 0, 1, 2, 3.")
        return value

    @field_validator(*PAY_COLUMNS)
    @classmethod
    def validate_pay_status(cls, value: int) -> int:
        if value not in {-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9}:
            raise ValueError("PAY_* must be a documented status code from -2 to 9.")
        return value

    @model_validator(mode="after")
    def validate_age(self) -> "RiskInput":
        if self.AGE > 120:
            raise ValueError("AGE must be at most 120.")
        return self


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_app(model_path: Path | None = None) -> FastAPI:
    selected_path = model_path or DEFAULT_MODEL_PATH

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.pipeline = None
        app.state.model_error = None
        app.state.ranges = {}
        app.state.model_version = "unavailable"
        try:
            freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
            if sha256(selected_path) != freeze["pipeline_sha256"]:
                raise ValueError("Pipeline checksum does not match frozen selection.")
            app.state.pipeline = joblib.load(selected_path)  # loaded exactly once at startup
            app.state.ranges = json.loads(RANGES_PATH.read_text(encoding="utf-8"))
            app.state.model_version = freeze["pipeline_sha256"][:12]
            app.state.threshold = float(freeze["threshold"])
        except Exception as error:  # Deliberately do not expose filesystem details to clients.
            app.state.model_error = type(error).__name__
        yield
        app.state.pipeline = None

    app = FastAPI(title="Sàng lọc nguy cơ trễ hạn", version="1.0.0", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/reports", StaticFiles(directory=ROOT / "reports"), name="reports")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        """Avoid a harmless browser 404 when no custom tab icon is supplied."""
        return Response(status_code=204)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for error in exc.errors():
            safe = dict(error)
            if "ctx" in safe:
                safe["ctx"] = {key: str(value) if isinstance(value, Exception) else value for key, value in safe["ctx"].items()}
            errors.append(safe)
        return JSONResponse(status_code=422, content={"detail": "Dữ liệu đầu vào không hợp lệ hoặc thiếu trường.", "errors": errors})

    @app.get("/", include_in_schema=False)
    async def home() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    async def health(request: Request) -> dict:
        return {"status": "ok" if request.app.state.pipeline is not None else "model_unavailable", "model_version": request.app.state.model_version}

    @app.get("/api/dashboard")
    async def dashboard() -> dict:
        return json.loads((STATIC_DIR / "dashboard_data.json").read_text(encoding="utf-8"))

    @app.post("/api/risk-score")
    async def risk_score(payload: RiskInput, request: Request) -> dict:
        if request.app.state.pipeline is None:
            raise HTTPException(status_code=503, detail="Model is unavailable. Prediction cannot be performed.")
        values = payload.model_dump()
        outside = []
        for field, bounds in request.app.state.ranges["continuous"].items():
            if values[field] < bounds["min"] or values[field] > bounds["max"]:
                outside.append({"field": field, "value": values[field], "training_min": bounds["min"], "training_max": bounds["max"]})
        for field, observed in request.app.state.ranges["categorical_observed"].items():
            if values[field] not in observed:
                outside.append({"field": field, "value": values[field], "training_observed_values": observed})
        probability = float(request.app.state.pipeline.predict_proba(pd.DataFrame([values]))[:, 1][0])
        threshold = request.app.state.threshold
        alert = probability >= threshold
        return {"probability_default": probability, "threshold": threshold, "alert": alert, "alert_group": "canh_bao_uu_tien" if alert else "khong_canh_bao", "model_version": request.app.state.model_version, "outside_training_range": outside, "warning": "Có giá trị ngoài miền train; kết quả cần được diễn giải thận trọng." if outside else None}

    return app


app = create_app()
