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

# --- 2. SIGN MAPPING LOGIC ---
SIGN_MAP = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4, 
    "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8, 
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12
}

def get_sign_int(sign_input):
    """Converts various VedAstro return types into a 1-12 integer."""
    if hasattr(sign_input, 'value__'): return int(sign_input.value__)
    if hasattr(sign_input, 'Name'): name = str(sign_input.Name)
    else: name = str(sign_input)
    return SIGN_MAP.get(name.split('.')[-1], 1)

# --- 3. GEOCODING ENGINE ---
def get_coords_from_city(city_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        res = requests.get(url, headers={'User-Agent': 'VedicApp'}).json()
        if res: return float(res[0]['lat']), float(res[0]['lon'])
    except: return None, None

# --- 4. APP CONFIG ---
st.set_page_config(page_title="Vedic Daily Engine", page_icon="☸️", layout="wide")

# --- 5. SIDEBAR ---
st.sidebar.header("📍 Birth & Current Locations")
view_mode = st.sidebar.radio("View", ["Daily Dashboard", "Weekly Forecast"])

# Birth Location
with st.sidebar.expander("Birth Details (Soul Blueprint)", expanded=True):
    b_city = st.text_input("Birth City", "Bangalore")
    if st.button("Calculate Birth Coords"):
        lat, lon = get_coords_from_city(b_city)
        if lat: st.session_state.b_lat, st.session_state.b_lon = lat, lon

    b_lat = st.number_input("B-Lat", value=st.session_state.get('b_lat', 12.97))
    b_lon = st.number_input("B-Lon", value=st.session_state.get('b_lon', 77.59))
    b_date = st.date_input("Birth Date", datetime.date(1990, 5, 15))
    b_time = st.time_input("Birth Time", datetime.time(10, 30))
    b_tz = st.text_input("TZ", "+05:30")

# Current Location
with st.sidebar.expander("Current City (Local Timing)", expanded=True):
    c_city = st.text_input("Current City", "London")
    if st.button("Calculate Current Coords"):
        lat, lon = get_coords_from_city(c_city)
        if lat: st.session_state.c_lat, st.session_state.c_lon = lat, lon

    c_lat = st.number_input("C-Lat", value=st.session_state.get('c_lat', 51.50))
    c_lon = st.number_input("C-Lon", value=st.session_state.get('c_lon', -0.12))

# --- 6. CORE ENGINE ---
def run_vedic_engine(target_date):
    # Setup Objects
    b_loc = GeoLocation("Birth", b_lon, b_lat)
    c_loc = GeoLocation("Current", c_lon, c_lat)
    b_time_obj = Time(f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}", b_loc)
    c_time_obj = Time(f"{target_date.strftime('%H:%M %d/%m/%Y')} +00:00", c_loc)

    # 1. FIND BIRTH MOON SIGN (Chandra Lagna)
    moon_raw = Calculate.PlanetSignName(PlanetName.Moon, b_time_obj)
    birth_moon_val = get_sign_int(moon_raw)
    
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu]
    
    planet_table = []
    houses = []

    for p in planets:
        # Get Current Transit Sign
        cur_sign_raw = Calculate.PlanetSignName(p, c_time_obj)
        cur_sign_val = get_sign_int(cur_sign_raw)
        cur_sign_name = str(cur_sign_raw).split('.')[-1]
        
        # Chandra Lagna Math: (Current - Birth + 12) % 12 + 1
        rel_house = (cur_sign_val - birth_moon_val + 12) % 12 + 1
        houses.append(rel_house)
        
        # Transit Status
        status = "Direct"
        if p.name in ["Rahu", "Ketu"]: status = "Retrograde"
        elif hasattr(Calculate, "IsPlanetRetrograde"):
            if Calculate.IsPlanetRetrograde(p, c_time_obj): status = "Retrograde"

        planet_table.append({
            "Planet": p.name,
            "House Position": f"House {rel_house}",
            "Zodiac Sign": cur_sign_name,
            "Transit Status": status
        })

    # 2. PILLAR MAPPING
    pillars = {
        "Work": "Action" if rel_house in [1, 10, 11] else "Routine",
        "Wealth": "Gain" if rel_house in [2, 5, 9, 11] else "Stable",
        "Health": "High Vitality" if rel_house in [1, 5, 9] else "Conserve",
        "Relationships": "Social" if rel_house in [3, 7, 11] else "Neutral"
    }

    return {"table": planet_table, "pillars": pillars, "date": target_date}

# --- 7. UI DISPLAY ---
st.title("☸️ Chandra Lagna Engine")

try:
    if view_mode == "Daily Dashboard":
        data = run_vedic_engine(datetime.datetime.now())
        
        # Life Pillars
        st.subheader("🔮 Life Pillars")
        c1, c2, c3, c4 = st.columns(4)
        c1.info(f"💼 **Work**\n\n{data['pillars']['Work']}")
        c2.info(f"💰 **Wealth**\n\n{data['pillars']['Wealth']}")
        c3.info(f"🧘 **Health**\n\n{data['pillars']['Health']}")
        c4.info(f"❤️ **Relations**\n\n{data['pillars']['Relationships']}")

        # Deep Metrics Table
        st.subheader("📊 Full Astronomical Data")
        st.table(pd.DataFrame(data['table']))
        
    else:
        st.subheader("📅 Weekly Forecast Table")
        week_list = []
        for i in range(7):
            d = run_vedic_engine(datetime.datetime.now() + datetime.timedelta(days=i))
            row = {"Date": d['date'].strftime("%a %d %b")}
            row.update(d['pillars'])
            week_list.append(row)
        st.dataframe(pd.DataFrame(week_list), use_container_width=True)

except Exception as e:
    st.error(f"Engine Alignment Error: {e}")
