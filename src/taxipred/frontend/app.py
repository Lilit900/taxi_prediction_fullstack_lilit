import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api/taxi/v1"

st.set_page_config(page_title="Manual Taxi Predictor", page_icon="🚖")
st.title("🚖 Taxi Price Prediction")

with st.sidebar:
    st.subheader("Backend status")
    try:
        health = requests.get(f"{API_URL}/health", timeout=3)
        if health.status_code == 200:
            st.success("✅ Backend is running")
        else:
            st.warning(f"⚠️ Backend responded: {health.status_code}")
    except Exception:
        st.error("❌ Backend not reachable")

    st.divider()
    st.header("Trip Parameters")

    with st.form("predict_form"):
        dist = st.number_input("Distance (km)", min_value=0.1, value=5.0, step=0.1)
        dur = st.number_input("Duration (min)", min_value=1.0, value=15.0, step=1.0)

        time_of_day = st.selectbox(
            "Time of Day", ["Morning", "Afternoon", "Evening", "Night"]
        )
        day_of_week = st.selectbox("Day of Week", ["Weekday", "Weekend"])
        traffic = st.selectbox("Traffic", ["Low", "Medium", "High"])
        weather = st.selectbox("Weather", ["Clear", "Rain", "Snow"])

        submitted = st.form_submit_button("Predict Fare")

    if st.button("Reset"):
        st.rerun()


if submitted:
    payload = {
        "Trip_Distance_km": float(dist),
        "Trip_Duration_Minutes": float(dur),
        "Time_of_Day": time_of_day,
        "Day_of_Week": day_of_week,
        "Traffic_Conditions": traffic,
        "Weather": weather,
    }

    try:
        response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
        if response.status_code == 200:
            st.session_state["last_prediction"] = response.json()
        else:
            st.error(f"Prediction failed: {response.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend. Start FastAPI first (uvicorn).")
    except requests.exceptions.Timeout:
        st.error("Backend took too long to respond (timeout).")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

if "last_prediction" in st.session_state:
    res = st.session_state["last_prediction"]
    st.divider()
    st.markdown(
        f"""
    <div style='background-color:#1e293b; padding:25px; border-radius:15px; border:2px solid #3b82f6; text-align:center;'>
        <h2 style='color:white; margin:0; font-size:1.5rem;'>💳 Estimated Fare</h2>
        <h1 style='color:#60a5fa; margin:10px 0; font-size:3rem;'>{res["estimated_price"]:.2f} {res["currency"]}</h1>
        <p style='color:#94a3b8; margin:0;'>Confidence Level (Log): {res["predicted_price_log"]:.4f}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
