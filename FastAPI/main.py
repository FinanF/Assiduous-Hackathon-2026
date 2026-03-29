import joblib
import pandas as pd
from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(
    os.getenv("DATABASE_URL", "sqlite:///earnings.db"),
    connect_args={"check_same_thread": False}
)

def ensure_table():
    """Fixed table schema matching code"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                fiscal_date_ending TEXT,
                reported_date TEXT,
                reported_eps REAL,
                estimated_eps REAL,
                surprise REAL,
                surprise_percentage REAL,
                report_time TEXT
            )
        """))
        conn.commit()

@app.on_event("startup")
async def startup():
    ensure_table()

@app.get("/")
async def get_data():
    url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol=IBM&apikey={os.getenv("API_KEY")}'
    return requests.get(url).json()

@app.post("/sync-data")
async def sync_data():
    try:
        ensure_table()

        # Demo data (API key expired)
        earnings = [{
            "fiscalDateEnding": "2025-12-31", "reportedDate": "2026-01-28", "reportedEPS": "4.52",
            "estimatedEPS": "4.29", "surprise": "0.23", "surprisePercentage": "5.3613", "reportTime": "post-market"
        }, {
            "fiscalDateEnding": "2025-09-30", "reportedDate": "2025-10-22", "reportedEPS": "2.65",
            "estimatedEPS": "2.45", "surprise": "0.2", "surprisePercentage": "8.1633", "reportTime": "post-market"
        }, {
            "fiscalDateEnding": "2025-06-30", "reportedDate": "2025-07-23", "reportedEPS": "2.8",
            "estimatedEPS": "2.65", "surprise": "0.15", "surprisePercentage": "5.6604", "reportTime": "post-market"
        }, {
            "fiscalDateEnding": "2025-03-31", "reportedDate": "2025-04-23", "reportedEPS": "1.6",
            "estimatedEPS": "1.43", "surprise": "0.17", "surprisePercentage": "11.8881", "reportTime": "post-market"
        }, {
            "fiscalDateEnding": "2024-12-31", "reportedDate": "2025-01-29", "reportedEPS": "3.92",
            "estimatedEPS": "3.78", "surprise": "0.14", "surprisePercentage": "3.7037", "reportTime": "post-market"
        }]

        # Clear table
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM earnings"))
            conn.commit()

        # Row-by-row insert (FIXED column names)
        for item in earnings:
            row = {
                'symbol': 'IBM',
                'fiscal_date_ending': item['fiscalDateEnding'],  # FIXED: snake_case
                'reported_date': item['reportedDate'],
                'reported_eps': float(item['reportedEPS']),
                'estimated_eps': float(item['estimatedEPS']),
                'surprise': float(item['surprise']),
                'surprise_percentage': float(item['surprisePercentage']),
                'report_time': item['reportTime']
            }
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO earnings 
                    (symbol, fiscal_date_ending, reported_date, reported_eps, estimated_eps, 
                     surprise, surprise_percentage, report_time)
                    VALUES (:symbol, :fiscal_date_ending, :reported_date, :reported_eps, 
                            :estimated_eps, :surprise, :surprise_percentage, :report_time)
                """), row)
                conn.commit()

        return {"status": "synced", "rows_inserted": 5, "demo_data": True}
    except Exception as e:
        return {"error": str(e)}


@app.get("/forecast/{quarters}")
async def forecast(quarters: int = 1):
    try:
        model = joblib.load("./models/rf_model.joblib")
        features = joblib.load("./models/features.joblib")

        df = pd.read_sql("SELECT * FROM earnings ORDER BY fiscal_date_ending DESC LIMIT 1", engine)
        if df.empty:
            return {"error": "No data"}

        last_row = df.iloc[0]

        # **ORDER MATCHES TRAINING EXACTLY**
        feature_vector = [
            float(last_row['reported_eps']),  # lag1_eps
            float(last_row['surprise_percentage']),  # surprise_percentage
            float(pd.to_datetime(last_row['fiscal_date_ending']).quarter)  # quarter
        ]

        # Use numpy array WITHOUT column names to avoid sklearn validation
        import numpy as np
        input_data = np.array([feature_vector])

        base_pred = model.predict(input_data)[0]

        predictions = []
        current_eps = base_pred
        for i in range(quarters):
            predictions.append(round(current_eps, 2))
            current_eps *= 1.02

        return {
            "quarters": quarters,
            "predictions": {
                "base": predictions,
                "upside": [round(p * 1.15, 2) for p in predictions],
                "downside": [round(p * 0.85, 2) for p in predictions]
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/model-info")
async def model_info():
    try:
        with open("models/accuracy.txt", "r") as f:
            return {"r2_score": float(f.read())}
    except:
        return {"r2_score": "Model not trained yet"}

@app.get("/table-rows")
async def table_rows():
    ensure_table()
    df = pd.read_sql("SELECT * FROM earnings ORDER BY fiscal_date_ending", engine)
    # Return Python list directly (no pandas JSON issues)
    records = df.to_dict(orient='records')
    return records  # FastAPI auto-converts to clean JSON