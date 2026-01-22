import streamlit as st
import requests
import folium
from streamlit_folium import st_folium


API_URL = "http://127.0.0.1:8000/api/taxi/v1"

st.set_page_config(page_title="Resekollen Taxi Predictor", page_icon="🚖")
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

    st.divider()
    st.header("Route")
    from_address = st.text_input("From (Address A)", value="")
    to_address = st.text_input("To (Address B)", value="")
    show_route = st.button("Show Route")

    if st.button("Reset"):
        st.rerun()

if show_route:
    try:
        if not from_address or not to_address:
            st.warning("Please enter both Address A and Address B.")
        else:
            with st.spinner("Fetching route from backend..."):
                r = requests.post(
                    f"{API_URL}/route",
                    json={"from_address": from_address, "to_address": to_address},
                    timeout=90,
                )
                r.raise_for_status()
                st.session_state["route_result"] = r.json()
    except Exception as e:
        st.error(f"Route error: {e}")

if "route_result" in st.session_state:
    route = st.session_state["route_result"]

    st.session_state["route_dist_km"] = route["distance_km"]
    st.session_state["route_dur_min"] = route["duration_min"]

    st.success(
        f"Route distance: {route['distance_km']:.2f} km | ETA: {route['duration_min']:.1f} min"
    )

    center_lat = (route["start_lat"] + route["end_lat"]) / 2
    center_lon = (route["start_lon"] + route["end_lon"]) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    folium.Marker([route["start_lat"], route["start_lon"]], tooltip="Start").add_to(m)
    folium.Marker([route["end_lat"], route["end_lon"]], tooltip="End").add_to(m)
    folium.PolyLine(route["polyline_latlon"], weight=5).add_to(m)

    st_folium(m, width=700, height=400, key="route_map")

if submitted:
    dist_to_use = st.session_state.get("route_dist_km", dist)
    dur_to_use = st.session_state.get("route_dur_min", dur)
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
            # SAVE the result to session state so it stays visible
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
