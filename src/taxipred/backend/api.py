from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

app = FastAPI(title="Taxi Price Prediction API", version="1.0")

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "random_forest_model.joblib"
DATA_PATH = BASE_DIR.parent / "data" / "df_train.csv"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Training data not found at {DATA_PATH}")

model = joblib.load(MODEL_PATH)
df_train = pd.read_csv(DATA_PATH)

FEATURE_COLUMNS = [
    "Trip_Distance_km",
    "Trip_Duration_Minutes",
    "Time_of_Day_Evening",
    "Time_of_Day_Morning",
    "Time_of_Day_Night",
    "Time_of_Day_Unknown",
    "Day_of_Week_Weekday",
    "Day_of_Week_Weekend",
    "Traffic_Conditions_Low",
    "Traffic_Conditions_Medium",
    "Traffic_Conditions_Unknown",
    "Weather_Rain",
    "Weather_Snow",
    "Weather_Unknown",
]


class TripInput(BaseModel):
    Trip_Distance_km: float
    Trip_Duration_Minutes: float
    Time_of_Day: str
    Day_of_Week: str
    Traffic_Conditions: str
    Weather: str


def build_features(trip: TripInput) -> pd.DataFrame:
    """
    Convert user-friendly categories into the exact one-hot encoded feature vector
    used during model training.
    Baselines (all zeros):
      - Time_of_Day: Afternoon
      - Traffic_Conditions: High
      - Weather: Clear
      - Day_of_Week: Unknown (no dummy column)
    """

    features = {
        "Trip_Distance_km": float(trip.Trip_Distance_km),
        "Trip_Duration_Minutes": float(trip.Trip_Duration_Minutes),
        "Time_of_Day_Evening": 0.0,
        "Time_of_Day_Morning": 0.0,
        "Time_of_Day_Night": 0.0,
        "Time_of_Day_Unknown": 0.0,
        "Day_of_Week_Weekday": 0.0,
        "Day_of_Week_Weekend": 0.0,
        "Traffic_Conditions_Low": 0.0,
        "Traffic_Conditions_Medium": 0.0,
        "Traffic_Conditions_Unknown": 0.0,
        "Weather_Rain": 0.0,
        "Weather_Snow": 0.0,
        "Weather_Unknown": 0.0,
    }

    if trip.Time_of_Day in ["Evening", "Morning", "Night", "Unknown"]:
        features[f"Time_of_Day_{trip.Time_of_Day}"] = 1.0

    if trip.Day_of_Week in ["Weekday", "Weekend"]:
        features[f"Day_of_Week_{trip.Day_of_Week}"] = 1.0

    if trip.Traffic_Conditions in ["Low", "Medium", "Unknown"]:
        features[f"Traffic_Conditions_{trip.Traffic_Conditions}"] = 1.0

    if trip.Weather in ["Rain", "Snow", "Unknown"]:
        features[f"Weather_{trip.Weather}"] = 1.0

    X = pd.DataFrame([features])[FEATURE_COLUMNS]
    return X


@app.get("/")
def home():
    return {"message": "Taxi Price Prediction API is online", "version": "1.0"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "train_rows": int(df_train.shape[0]),
    }


@app.get("/data/sample")
def get_data_sample(rows: int = 5):
    """Return a few rows from the cleaned training data."""
    return df_train.head(rows).to_dict(orient="records")


@app.post("/predict")
def predict(trip: TripInput):
    """Predict taxi price from user inputs."""
    try:
        X_in = build_features(trip)

        pred_log = float(model.predict(X_in)[0])

        pred_price = float(np.expm1(pred_log))

        return {
            "status": "success",
            "predicted_price": round(pred_price, 2),
            "predicted_price_log": pred_log,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
