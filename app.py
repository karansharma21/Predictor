import sys
import types
import requests
import streamlit as st
import datetime
import pandas as pd

# --- 1. CRITICAL PYTHON 3.13 POLYFILL ---
if "pkg_resources" not in sys.modules:
    mock_pkg = types.ModuleType("pkg_resources")
    mock_pkg.declare_namespace = lambda name: None
    mock_pkg.get_distribution = lambda name: types.SimpleNamespace(version="0.0.0")
    sys.modules["pkg_resources"] = mock_pkg

from vedastro import *

# --- 2. DYNAMIC DISCOVERY ENGINE ---
def get_vedastro_metric(method_base, *args):
    """
    Scans the library for method variants (e.g., Tithi, GetTithi, GetTithiName).
    This prevents 'AttributeError' when the library updates.
    """
    search_space = [Calculate, PanchangaCalculator] if 'PanchangaCalculator' in globals() else [Calculate]
    variants = [method_base, f"Get{method_base}", f"{method_base}Name", f"Get{method_base}Name"]
    
    for scope in search_space:
        for var in variants:
            if hasattr(scope, var):
                try:
                    func = getattr(scope, var)
                    result = func(*args)
                    # If the result is a complex object, try to extract its name/value
                    if hasattr(result, "Name"): return str(result.Name)
                    if hasattr(result, "ToString"): return str(result.ToString())
                    return str(result)
                except:
                    continue
    return "N/A"

# --- 3. APP CONFIG ---
st.set_page_config(page_title="Soul MRI", layout="wide")
st.title("🔱 Soul MRI: Advanced Diagnostic")

# Session State for Location
if 'lat' not in st.session_state: st.session_state.lat = 28.6139
if 'lon' not in st.session_state: st.session_state.lon = 77.2090

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("📍 Personal Parameters")
    city = st.text_input("City Name", "New Delhi")
    if st.button("Sync Coords"):
        res = requests.get(f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1").json()
        if res:
            st.session_state.lat = float(res[0]['lat'])
            st.session_state.lon = float(res[0]['lon'])
    
    lat = st.number_input("Lat", value=st.session_state.lat)
    lon = st.number_input("Lon", value=st.session_state.lon)
    b_date = st.date_input("Birth Date", datetime.date(1995, 1, 1))
    b_time = st.time_input("Birth Time", datetime.time(12, 0))
    b_tz = st.text_input("Timezone", "+05:30")

# --- 5. THE MRI SCAN ---
try:
    # Initialize Core Objects
    loc = GeoLocation("Location", lon, lat)
    # Correct Time String Format for VedAstro Parser
    time_str = f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}"
    birth_time = Time(time_str, loc)
    
    now_dt = datetime.datetime.now()
    now_str = f"{now_dt.strftime('%H:%M %d/%m/%Y')} +00:00"
    now_time = Time(now_str, loc)

    # UI Columns for the "MRI" Results
    st.subheader("📡 Diagnostic Frequency Scan")
    c1, c2, c3 = st.columns(3)

    # Metric 1: Lunar Phase (The Emotional MRI)
    tithi = get_vedastro_metric("Tithi", now_time)
    c1.metric("Current Tithi", tithi)

    # Metric 2: Mind Mansion (The Mental MRI)
    nakshatra = get_vedastro_metric("MoonNakshatra", now_time)
    c2.metric("Moon Nakshatra", nakshatra)

    # Metric 3: Yoga (The Vitality MRI)
    yoga = get_vedastro_metric("Yoga", now_time)
    c3.metric("Current Yoga", yoga)

    # Metric 4: Planet Positions
    st.divider()
    st.subheader("📊 The Soul Blueprint (Current Transits)")
    
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    mri_results = []
    for p in planets:
        sign = get_vedastro_metric("PlanetSign", p, now_time)
        mri_results.append({"Planet": p.name, "MRI Reading": sign})
    
    st.table(pd.DataFrame(mri_results))

except Exception as e:
    st.error(f"MRI Scanner Fault: {e}")
    st.info("Ensure all date and time fields are filled out correctly.")
