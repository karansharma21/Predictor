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

# --- 2. GEOCODING ENGINE (City -> Lat/Lon) ---
def update_coords(city_type):
    city_name = st.session_state[f"{city_type}_city"]
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        res = requests.get(url, headers={'User-Agent': 'VedicApp'}).json()
        if res:
            st.session_state[f"{city_type}_lat"] = float(res[0]['lat'])
            st.session_state[f"{city_type}_lon"] = float(res[0]['lon'])
    except:
        pass

# --- 3. DYNAMIC API DISCOVERY ---
def get_planet_sign_name(planet, time):
    """Scans the library for whichever name they've given the Sign function today."""
    # List of known historical and current method names
    possible_methods = ['PlanetSignName', 'GetPlanetSignName', 'PlanetSign', 'GetSignName']
    
    for method in possible_methods:
        if hasattr(Calculate, method):
            func = getattr(Calculate, method)
            try:
                result = func(planet, time)
                # If it returns a Sign object, we need the .Name or .GetSignName()
                if hasattr(result, 'GetSignName'): return result.GetSignName()
                if hasattr(result, 'Name'): return result
                return result
            except:
                continue
    
    # Final fallback: Look for anything with 'Sign' in the name
    for attr in dir(Calculate):
        if "Sign" in attr and "Planet" in attr:
            try:
                return getattr(Calculate, attr)(planet, time)
            except:
                continue
    raise AttributeError("VedAstro API has changed. Please check library version.")

# --- 4. APP CONFIG ---
st.set_page_config(page_title="Vedic Daily Engine", page_icon="☸️", layout="wide")

# --- 5. SIDEBAR ---
st.sidebar.header("📍 Location & Birth Details")
view_mode = st.sidebar.radio("Display Mode", ["Daily Dashboard", "Weekly Forecast"])

# Initialize session states for coordinates
if 'birth_lat' not in st.session_state: st.session_state.birth_lat = 12.97
if 'birth_lon' not in st.session_state: st.session_state.birth_lon = 77.59
if 'curr_lat' not in st.session_state: st.session_state.curr_lat = 40.71
if 'curr_lon' not in st.session_state: st.session_state.curr_lon = -74.00

with st.sidebar.expander("Birth City (Soul Blueprint)", expanded=True):
    st.text_input("Birth City", value="Bangalore", key="birth_city", on_change=update_coords, args=('birth',))
    b_lat = st.number_input("Lat", value=st.session_state.birth_lat, key="b_lat_disp")
    b_lon = st.number_input("Lon", value=st.session_state.birth_lon, key="b_lon_disp")
    b_date = st.date_input("Birth Date", datetime.date(1990, 5, 15))
    b_time = st.time_input("Birth Time", datetime.time(10, 30))
    b_tz = st.text_input("Timezone", "+05:30")

with st.sidebar.expander("Current City (Local Timing)", expanded=False):
    st.text_input("Current City", value="New York", key="curr_city", on_change=update_coords, args=('curr',))
    c_lat = st.number_input("Lat", value=st.session_state.curr_lat, key="c_lat_disp")
    c_lon = st.number_input("Lon", value=st.session_state.curr_lon, key="c_lon_disp")

# --- 6. CORE ENGINE ---
def run_vedic_engine(target_date):
    b_loc = GeoLocation("Birth", b_lon, b_lat)
    c_loc = GeoLocation("Current", c_lon, c_lat)
    
    b_time_obj = Time(f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}", b_loc)
    c_time_obj = Time(f"{target_date.strftime('%H:%M %d/%m/%Y')} +00:00", c_loc)

    # Chandra Lagna Calculation
    birth_moon_sign = get_planet_sign_name(PlanetName.Moon, b_time_obj).value__
    
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu]
    
    planet_table = []
    houses = []
    
    for p in planets:
        cur_sign_obj = get_planet_sign_name(p, c_time_obj)
        cur_sign_val = cur_sign_obj.value__
        
        # House relative to Moon: (Current - Birth + 12) % 12 + 1
        rel_house = (cur_sign_val - birth_moon_sign + 12) % 12 + 1
        houses.append(rel_house)
        
        # Transit Status (Retrograde logic)
        is_retro = Calculate.IsPlanetRetrograde(p, c_time_obj) if hasattr(Calculate, 'IsPlanetRetrograde') else False
        
        planet_table.append({
            "Planet": p.name,
            "House Position": f"House {rel_house}",
            "Zodiac Sign": cur_sign_obj.name,
            "Transit Status": "Retrograde" if is_retro else "Direct"
        })

    # Pillar Logic
    pillars = {
        "Work": "Focus" if any(h in [1, 10, 11] for h in houses[:3]) else "Routine",
        "Wealth": "Growth" if any(h in [2, 5, 9, 11] for h in houses) else "Stable",
        "Health": "Vitality" if any(h in [1, 6, 8] for h in houses) else "Rest",
        "Relationships": "Social" if any(h in [3, 7, 11] for h in houses) else "Private"
    }

    return {"table": planet_table, "pillars": pillars, "date": target_date}

# --- 7. UI DISPLAY ---
st.title("☸️ Vedic Daily Engine")

try:
    if view_mode == "Daily Dashboard":
        data = run_vedic_engine(datetime.datetime.now())
        
        # 4-Column Pillars
        st.subheader("🔮 Life Pillars (Chandra Lagna)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💼 Work", data['pillars']['Work'])
        col2.metric("💰 Wealth", data['pillars']['Wealth'])
        col3.metric("🧘 Health", data['pillars']['Health'])
        col4.metric("❤️ Relationships", data['pillars']['Relationships'])

        # Deep Metrics
        st.subheader("📊 Deep Metrics: Full Data Set")
        st.table(pd.DataFrame(data['table']))
        
    else:
        st.subheader("📅 Weekly Forecast Table")
        week_data = []
        for i in range(7):
            day = datetime.datetime.now() + datetime.timedelta(days=i)
            d = run_vedic_engine(day)
            row = {"Date": day.strftime("%a %d %b")}
            row.update(d['pillars'])
            week_data.append(row)
        st.dataframe(pd.DataFrame(week_data), use_container_width=True)

except Exception as e:
    st.error(f"Engine Alignment Error: {e}")
    st.info("Check if city coordinates have loaded correctly in the sidebar.")
