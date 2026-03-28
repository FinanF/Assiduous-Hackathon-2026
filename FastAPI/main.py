from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv
import mysql.connector
app = FastAPI()
load_dotenv()

mydb = mysql.connector.connect(
    host="mysql",
    user="root",
    passwd="password",
    database="ibm_db"
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