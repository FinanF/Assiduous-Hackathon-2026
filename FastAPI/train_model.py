import pandas as pd
import joblib
import requests
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import mysql.connector
import os
from dotenv import load_dotenv
import time

load_dotenv()


def retry_sync(max_attempts=30, delay=3):
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}/{max_attempts}")
            response = requests.post("http://host.docker.internal:8000/sync-data", timeout=10)
            if response.status_code == 200:
                print("Data synced, connecting to MySQL")
                mydb = mysql.connector.connect(
                    host="mysql",
                    user=os.getenv("MYSQL_USER"),
                    password=os.getenv("MYSQL_PASSWORD"),  # Fixed: password not passwd
                    database=os.getenv("MYSQL_DATABASE")
                )
                df = pd.read_sql("SELECT * FROM earnings ORDER BY fiscal_date_ending", mydb)
                mydb.close()
                if len(df) > 10:
                    print(f"Loaded {len(df)} rows")
                    return df
                else:
                    print("Not enough data")
            time.sleep(delay)
        except Exception as e:
            print(f"Retry {attempt + 1}: {e}")
            time.sleep(delay)
    raise Exception("Failed to sync data after retries")


def train_model(df):
    print(f"Training on {len(df)} rows")

    # Features + target
    df['lag1_eps'] = df['reported_eps'].shift(1)
    df['quarter'] = pd.to_datetime(df['fiscal_date_ending']).dt.quarter
    df['next_eps'] = df['reported_eps'].shift(-1)

    # One-line filter + drop NaN
    X = df[['lag1_eps', 'quarter', 'surprise_percentage']].dropna()
    y = df['next_eps'].dropna()

    # Align lengths
    min_len = min(len(X), len(y))
    X, y = X.iloc[:min_len], y.iloc[:min_len]
    X, y = X.dropna(), y.dropna()

    if len(X) < 5:
        raise Exception(f"Not enough data: {len(X)} samples")

    # Train & save
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/rf_model.joblib")
    print("Model saved!")

if __name__ == "__main__":
    df = retry_sync()
    train_model(df)
    print("Training complete")