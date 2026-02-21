import sys
import types
import requests

# --- 1. CRITICAL PYTHON 3.13 POLYFILL ---
if "pkg_resources" not in sys.modules:
    mock_pkg = types.ModuleType("pkg_resources")
    mock_pkg.declare_namespace = lambda name: None
    mock_pkg.get_distribution = lambda name: types.SimpleNamespace(version="0.0.0")
    sys.modules["pkg_resources"] = mock_pkg

import streamlit as st
import datetime
import pandas as pd
from vedastro import *

# --- 2. GEOCODING HELPER ---
def get_coords(city_name):
    """Fetch Lat/Lon from City Name using Nominatim (No API Key required)"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {'User-Agent': 'VedicEngineApp/1.0'}
        response = requests.get(url, headers=headers).json()
        if response:
            return float(response[0]['lat']), float(response[0]['lon'])
    except Exception:
        pass
    return None, None

# --- 3. APP CONFIG ---
st.set_page_config(page_title="Vedic Engine Pro", page_icon="🔱", layout="wide")

# --- 4. SIDEBAR - CITY INPUTS ---
st.sidebar.header("🌍 Location & Birth Data")
nav_mode = st.sidebar.radio("View Mode", ["Daily Dashboard", "Weekly Forecast"])

# Birth Details
st.sidebar.subheader("Birth (Soul Blueprint)")
b_city = st.sidebar.text_input("Birth City", "New Delhi")
if st.sidebar.button("Fetch Birth Coords"):
    lat, lon = get_coords(b_city)
    if lat:
        st.session_state.b_lat, st.session_state.b_lon = lat, lon
        st.sidebar.success(f"Found: {lat}, {lon}")

b_lat = st.sidebar.number_input("Birth Lat", value=st.session_state.get('b_lat', 28.6139))
b_lon = st.sidebar.number_input("Birth Lon", value=st.session_state.get('b_lon', 77.2090))
b_date = st.sidebar.date_input("Birth Date", datetime.date(1995, 1, 1))
b_time = st.sidebar.time_input("Birth Time", datetime.time(12, 0))
b_tz = st.sidebar.text_input("Birth TZ", "+05:30")

# Current Location
st.sidebar.subheader("Current Location")
c_city = st.sidebar.text_input("Current City", "New York")
if st.sidebar.button("Fetch Current Coords"):
    lat, lon = get_coords(c_city)
    if lat:
        st.session_state.c_lat, st.session_state.c_lon = lat, lon
        st.sidebar.success(f"Found: {lat}, {lon}")

c_lat = st.sidebar.number_input("Current Lat", value=st.session_state.get('c_lat', 40.7128))
c_lon = st.sidebar.number_input("Current Lon", value=st.session_state.get('c_lon', -74.0060))

# --- 5. CALCULATION ENGINE ---
def get_planet_sign_safe(planet, time):
    """Dynamic check for VedAstro's shifting API attributes"""
    for attr in ['PlanetSignName', 'PlanetSign', 'GetPlanetSignName']:
        if hasattr(Calculate, attr):
            func = getattr(Calculate, attr)
            res = func(planet, time)
            # Handle if the return is a Sign object or a SignName object
            return res.GetSignName() if hasattr(res, 'GetSignName') else res
    raise AttributeError("Could not find a valid Sign calculation method in VedAstro.")

def get_vibe_engine(target_date):
    birth_loc = GeoLocation("Birth", b_lon, b_lat)
    curr_loc = GeoLocation("Current", c_lon, c_lat)
    
    birth_time = Time(f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}", birth_loc)
    calc_time = Time(f"{target_date.strftime('%H:%M %d/%m/%Y')} +00:00", curr_loc)

    # 1. CHANDRA LAGNA
    b_moon_sign = get_planet_sign_safe(PlanetName.Moon, birth_time).value__
    
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury,
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu]
    
    planet_data = []
    houses_occupied = []

    for p in planets:
        cur_sign_obj = get_planet_sign_safe(p, calc_time)
        cur_sign_val = cur_sign_obj.value__
        
        # Relative House Logic
        rel_house = (cur_sign_val - b_moon_sign + 12) % 12 + 1
        houses_occupied.append(rel_house)
        
        planet_data.append({
            "Planet": p.name,
            "House": f"House {rel_house}",
            "Zodiac Sign": cur_sign_obj.name,
            "Status": "Direct" if p.name not in ["Rahu", "Ketu"] else "Retrograde"
        })

    # 2. PILLAR MAPPING
    pillars = {
        "Work": "Actionable" if any(h in [1, 10, 11] for h in houses_occupied[:3]) else "Routine",
        "Wealth": "Growth" if any(h in [2, 5, 9, 11] for h in houses_occupied[4:6]) else "Stable",
        "Health": "High Vitality" if any(h in [1, 5, 9] for h in houses_occupied) else "Conserve",
        "Relations": "Harmony" if any(h in [3, 7, 11] for h in houses_occupied) else "Neutral"
    }

    return {"metrics": planet_data, "pillars": pillars, "date": target_date}

# --- 6. UI RENDERING ---
st.title("🔱 Vedic Intelligence Dashboard")

try:
    if nav_mode == "Daily Dashboard":
        data = get_vibe_engine(datetime.datetime.now())
        
        st.subheader("🔮 Life Pillars (Chandra Lagna)")
        c1, c2, c3, c4 = st.columns(4)
        c1.info(f"💼 **Work**\n\n{data['pillars']['Work']}")
        c2.info(f"💰 **Wealth**\n\n{data['pillars']['Wealth']}")
        c3.info(f"🧘 **Health**\n\n{data['pillars']['Health']}")
        c4.info(f"❤️ **Relations**\n\n{data['pillars']['Relations']}")

        st.subheader("📊 Deep Metrics: Full Astronomical Data")
        st.table(pd.DataFrame(data['metrics']))

    else:
        st.subheader("📅 7-Day Weekly Forecast Table")
        week_list = []
        for i in range(7):
            d = get_vibe_engine(datetime.datetime.now() + datetime.timedelta(days=i))
            row = {"Date": d['date'].strftime("%a, %d %b")}
            row.update(d['pillars'])
            week_list.append(row)
        st.dataframe(pd.DataFrame(week_list), use_container_width=True)

except Exception as e:
    st.error(f"Engine Alignment Error: {e}")
    st.info("Check coordinates or ensure the library version is compatible.")

st.caption("Engine: VedAstro (3.13 Compatible) | System: Chandra Lagna")
