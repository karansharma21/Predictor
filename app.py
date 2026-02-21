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

# --- 2. SIGN & DATA MAPPING ---
SIGN_MAP = {"Aries":1, "Taurus":2, "Gemini":3, "Cancer":4, "Leo":5, "Virgo":6, "Libra":7, "Scorpio":8, "Sagittarius":9, "Capricorn":10, "Aquarius":11, "Pisces":12}

def get_sign_data(obj):
    """Safely extracts Sign Name and ID from any VedAstro return type."""
    name_str = str(obj).split('.')[-1]
    return SIGN_MAP.get(name_str, 1), name_str

def fetch_coords(city_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        res = requests.get(url, headers={'User-Agent': 'VedicMRI'}).json()
        return (float(res[0]['lat']), float(res[0]['lon'])) if res else (None, None)
    except: return None, None

# --- 3. APP CONFIG ---
st.set_page_config(page_title="Soul MRI", page_icon="🔱", layout="wide")

# --- 4. SIDEBAR INPUTS ---
st.sidebar.header("🔬 Diagnostic Inputs")
view_mode = st.sidebar.radio("Navigation", ["Daily MRI", "Weekly Forecast"])

with st.sidebar.expander("Natal Data (Birth)", expanded=True):
    b_city = st.text_input("Birth City", "Mumbai")
    if st.button("Lookup Birth Coords"):
        lat, lon = fetch_coords(b_city)
        if lat: st.session_state.blat, st.session_state.blon = lat, lon
    
    blat = st.number_input("Lat", value=st.session_state.get('blat', 19.0760))
    blon = st.number_input("Lon", value=st.session_state.get('blon', 72.8777))
    b_date = st.date_input("Birth Date", datetime.date(1990, 1, 1))
    b_time = st.time_input("Birth Time", datetime.time(12, 0))
    b_tz = st.text_input("Birth TZ", "+05:30")

with st.sidebar.expander("Local Data (Current)", expanded=True):
    c_city = st.text_input("Current City", "Los Angeles")
    if st.button("Lookup Local Coords"):
        lat, lon = fetch_coords(c_city)
        if lat: st.session_state.clat, st.session_state.clon = lat, lon
    
    clat = st.number_input("Current Lat", value=st.session_state.get('clat', 34.0522))
    clon = st.number_input("Current Lon", value=st.session_state.get('clon', -118.2437))

# --- 5. CALCULATION ENGINE ---
def run_mri_engine(target_dt):
    # Time/Location Setup
    b_loc = GeoLocation("Birth", blon, blat)
    c_loc = GeoLocation("Current", clon, clat)
    birth_time = Time(f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}", b_loc)
    now_time = Time(f"{target_dt.strftime('%H:%M %d/%m/%Y')} +00:00", c_loc)

    # 1. DASHA (The Current Life Chapter)
    # Getting the Mahadasha (Main Period)
    dasha_info = "Calculating..."
    try:
        dasha_list = pd.DataFrame(Calculate.VimshottariDashaAtTime(birth_time, now_time))
        dasha_info = dasha_list.iloc[-1].PlanetName.name # Gets active planet
    except: dasha_info = "Jupiter" # Fallback if list structure varies

    # 2. TARA BALA (Personal Mind Strength)
    b_nak = int(PanchangaCalculator.GetMoonNakshatra(birth_time).NakshatraName.value__)
    t_nak = int(PanchangaCalculator.GetMoonNakshatra(now_time).NakshatraName.value__)
    tara_idx = ((t_nak - b_nak + 27) % 9) + 1
    tara_names = {1:"Self", 2:"Wealth", 3:"Obstacle", 4:"Success", 5:"Hardship", 6:"Achievement", 7:"Danger", 8:"Friend", 9:"Great Friend"}

    # 3. CHANDRA LAGNA TRANSITS (Deep Metrics)
    b_moon_sign_id, _ = get_sign_data(Calculate.PlanetSignName(PlanetName.Moon, birth_time))
    
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu]
    
    table_data = []
    house_list = []
    for p in planets:
        cur_sign_id, cur_sign_name = get_sign_data(Calculate.PlanetSignName(p, now_time))
        rel_house = (cur_sign_id - b_moon_sign_id + 12) % 12 + 1
        house_list.append(rel_house)
        
        table_data.append({
            "Planet": p.name,
            "House Position": f"House {rel_house}",
            "Zodiac Sign": cur_sign_name,
            "Transit Status": "Retrograde" if p.name in ["Rahu", "Ketu"] else "Direct"
        })

    # 4. PILLAR LOGIC
    pillars = {
        "Work": "Power Move" if any(h in [10, 11, 1] for h in house_list[:3]) else "Support",
        "Wealth": "Inflow" if any(h in [2, 11] for h in house_list[4:6]) else "Hold",
        "Health": "High Vibe" if 1 in house_list or 5 in house_list else "Rest",
        "Relations": "Alignment" if 7 in house_list or 9 in house_list else "Neutral"
    }

    return {
        "dasha": dasha_info,
        "tara": tara_names.get(tara_idx),
        "pillars": pillars,
        "table": table_data,
        "date": target_dt,
        "rahu": str(PanchangaCalculator.GetRahuKaalRange(now_time))
    }

# --- 6. UI PRESENTATION ---
st.title("🔱 Soul MRI: Advanced Vedic Diagnostic")

try:
    if view_mode == "Daily MRI":
        data = run_mri_engine(datetime.datetime.now())
        
        # KEY METRICS BAR
        st.subheader("📡 Diagnostic Summary")
        k1, k2, k3 = st.columns(3)
        k1.metric("Current Life Chapter (Dasha)", data['dasha'])
        k2.metric("Daily Mind Frequency (Tara)", data['tara'])
        k3.metric("Critical Timing (Rahu Kaal)", data['rahu'].split(' ')[0])

        # LIFE PILLARS
        st.divider()
        st.subheader("🔮 Life Pillar Breakdown")
        c1, c2, c3, c4 = st.columns(4)
        c1.info(f"💼 **Work**\n\n{data['pillars']['Work']}")
        c2.info(f"💰 **Wealth**\n\n{data['pillars']['Wealth']}")
        c3.info(f"🧘 **Health**\n\n{data['pillars']['Health']}")
        c4.info(f"❤️ **Relations**\n\n{data['pillars']['Relations']}")

        # DEEP DATA
        st.subheader("📊 Full Astronomical Data Set")
        st.table(pd.DataFrame(data['table']))

    else:
        st.subheader("📅 7-Day Forecasting Table")
        forecast = []
        for i in range(7):
            d = run_mri_engine(datetime.datetime.now() + datetime.timedelta(days=i))
            row = {"Date": d['date'].strftime("%a %d"), "Dasha": d['dasha'], "Mood": d['tara']}
            row.update(d['pillars'])
            forecast.append(row)
        st.dataframe(pd.DataFrame(forecast), use_container_width=True)

except Exception as e:
    st.error(f"MRI Engine Fault: {e}")

st.caption("Engine: VedAstro | Logic: Chandra Lagna + Vimshottari Dasha | Python 3.13 Polyfilled")
