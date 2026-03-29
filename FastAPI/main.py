import joblib
import pandas as pd
from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
load_dotenv()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



mydb = mysql.connector.connect(
    host="mysql",
    user=os.environ.get("MYSQL_USER"),
    passwd=os.environ.get("MYSQL_PASSWORD"),
    database=os.environ.get("MYSQL_DATABASE"),
)

mycursor = mydb.cursor()
@app.get("/")
async def get_data():
    url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol=IBM&apikey={os.getenv("API_KEY")}'
    return requests.get(url).json()

@app.post("/sync-data")
async def sync_data():
    try:
        data = await get_data()
        rows = []

        for item in data.get("quarterlyEarnings", []):
            rows.append((
                data.get("symbol"),
                item.get("fiscalDateEnding"),
                item.get("reportedDate"),
                float(item.get("reportedEPS")) if item.get("reportedEPS") else None,
                float(item.get("estimatedEPS")) if item.get("estimatedEPS") else None,
                float(item.get("surprise")) if item.get("surprise") else None,
                float(item.get("surprisePercentage")) if item.get("surprisePercentage") else None,
                item.get("reportTime"),
            ))

        sql = """
        INSERT INTO earnings
        (symbol, fiscal_date_ending, reported_date, reported_eps, estimated_eps, surprise, surprise_percentage, report_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        mycursor.executemany(sql, rows)
        mydb.commit()
        return {"status": "synced", "rows_inserted": len(rows)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/forecast/{quarters}")
def forecast(quarters: int = 1):
    model = joblib.load("model.joblib")
    # Get LAST quarter from MySQL (most recent data)
    df = pd.read_sql("SELECT * FROM earnings ORDER BY fiscal_date_ending DESC LIMIT 1", mydb)
    last_row = df.iloc[0]

    # Use real features from that row
    features = [[
        last_row['reported_eps'],  # lag1_eps = last EPS
        last_row['surprise_percentage'],  # actual surprise
        pd.to_datetime(last_row['fiscal_date_ending']).quarter  # next quarter
    ]]

    predictions = []
    current_features = [
        last_row['reported_eps'],
        last_row['surprise_percentage'],
        pd.to_datetime(last_row['fiscal_date_ending']).quarter + 1
    ]

    for i in range(quarters):
        pred = model.predict([current_features])[0]
        predictions.append(pred)

        # Update for next prediction
        current_features[0] = pred  # Last EPS = this prediction
        current_features[2] = (current_features[2] % 4) + 1  # Next quarter
    return {
        "quarters": quarters,
        "predictions": {"base": [round(p, 2) for p in predictions],
                        "upside": [round(p*1.15, 2) for p in predictions],  # +15% optimistic
        "downside": [round(p*0.85, 2) for p in predictions]}  # -15% pessimistic
    }
