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

# --- 2. DATA MAPPING & HELPERS ---
SIGN_MAP = {"Aries":1, "Taurus":2, "Gemini":3, "Cancer":4, "Leo":5, "Virgo":6, "Libra":7, "Scorpio":8, "Sagittarius":9, "Capricorn":10, "Aquarius":11, "Pisces":12}

def get_sign_info(obj):
    name = str(obj).split('.')[-1]
    return SIGN_MAP.get(name, 1), name

def fetch_coords(city):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
        res = requests.get(url, headers={'User-Agent': 'VedicMRI'}).json()
        return (float(res[0]['lat']), float(res[0]['lon'])) if res else (None, None)
    except: return None, None

# --- 3. APP CONFIG ---
st.set_page_config(page_title="Soul MRI", page_icon="🔱", layout="wide")

# --- 4. SIDEBAR ---
st.sidebar.header("🔬 Diagnostic Inputs")
view_mode = st.sidebar.radio("View", ["Daily MRI", "Weekly Forecast"])

with st.sidebar.expander("Birth Details", expanded=True):
    b_city = st.text_input("Birth City", "New Delhi")
    if st.button("Lookup Birth"):
        lat, lon = fetch_coords(b_city)
        if lat: st.session_state.blat, st.session_state.blon = lat, lon
    blat = st.number_input("Lat", value=st.session_state.get('blat', 28.61))
    blon = st.number_input("Lon", value=st.session_state.get('blon', 77.20))
    b_date = st.date_input("Birth Date", datetime.date(1995, 1, 1))
    b_time = st.time_input("Birth Time", datetime.time(12, 0))
    b_tz = st.text_input("TZ", "+05:30")

with st.sidebar.expander("Current Location", expanded=True):
    c_city = st.text_input("Current City", "London")
    if st.button("Lookup Current"):
        lat, lon = fetch_coords(c_city)
        if lat: st.session_state.clat, st.session_state.clon = lat, lon
    clat = st.number_input("C-Lat", value=st.session_state.get('clat', 51.50))
    clon = st.number_input("C-Lon", value=st.session_state.get('clon', -0.12))

# --- 5. THE MRI ENGINE ---
def run_mri(target_dt):
    # Setup
    b_loc = GeoLocation("Birth", blon, blat)
    c_loc = GeoLocation("Current", clon, clat)
    b_time_obj = Time(f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}", b_loc)
    c_time_obj = Time(f"{target_dt.strftime('%H:%M %d/%m/%Y')} +00:00", c_loc)

    # A. PANCHANGA (Direct API Access)
    tithi = str(Calculate.Tithi(c_time_obj).GetTithiName())
    t_nak = Calculate.MoonNakshatra(c_time_obj).GetNakshatraName()
    
    # B. TARA BALA (Personal Soil)
    b_nak = Calculate.MoonNakshatra(b_time_obj).GetNakshatraName()
    tara_val = ((int(t_nak.value__) - int(b_nak.value__) + 27) % 9) + 1
    tara_names = {1:"Janma (Self)", 2:"Sampat (Wealth)", 3:"Vipat (Danger)", 4:"Kshema (Safety)", 
                  5:"Pratyak (Obstacles)", 6:"Sadhana (Success)", 7:"Naidhana (Crisis)", 
                  8:"Mitra (Friend)", 9:"Ati-Mitra (Best Friend)"}

    # C. TRANSITS (Chandra Lagna)
    b_moon_id, _ = get_sign_info(Calculate.PlanetSignName(PlanetName.Moon, b_time_obj))
    
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu]
    
    table_data = []
    house_list = []
    for p in planets:
        s_id, s_name = get_sign_info(Calculate.PlanetSignName(p, c_time_obj))
        rel_h = (s_id - b_moon_id + 12) % 12 + 1
        house_list.append(rel_h)
        table_data.append({"Planet": p.name, "House": f"House {rel_h}", "Sign": s_name, "Status": "Direct"})

    # D. DASHA (The Chapter)
    try:
        dasha = Calculate.VimshottariDashaAtTime(b_time_obj, c_time_obj)
        current_period = str(dasha[-1].PlanetName) if dasha else "Unknown"
    except: current_period = "Active"

    # E. PILLARS
    pillars = {
        "Work": "Strategic" if any(h in [10, 11] for h in house_list[:3]) else "Supportive",
        "Wealth": "Flow" if any(h in [2, 11] for h in house_list) else "Steady",
        "Health": "High Vibe" if 1 in house_list else "Rest",
        "Relations": "Harmony" if 7 in house_list else "Neutral"
    }

    return {"tara": tara_names.get(tara_val), "tithi": tithi, "dasha": current_period, "table": table_data, "pillars": pillars, "date": target_dt}

# --- 6. UI ---
st.title("🔱 Soul MRI: Comprehensive Vedic Diagnostic")

try:
    if view_mode == "Daily MRI":
        data = run_mri(datetime.datetime.now())
        
        # Summary Row
        col1, col2, col3 = st.columns(3)
        col1.metric("Life Chapter (Dasha)", data['dasha'])
        col2.metric("Daily Mindset (Tara)", data['tara'])
        col3.metric("Lunar Phase (Tithi)", data['tithi'])

        # Pillar Row
        st.divider()
        st.subheader("🔮 Life Pillar MRI")
        p1, p2, p3, p4 = st.columns(4)
        p1.info(f"💼 **Work**\n\n{data['pillars']['Work']}")
        p2.info(f"💰 **Wealth**\n\n{data['pillars']['Wealth']}")
        p3.info(f"🧘 **Health**\n\n{data['pillars']['Health']}")
        p4.info(f"❤️ **Relations**\n\n{data['pillars']['Relations']}")

        # Data Table
        st.subheader("📊 Deep Metric Table")
        st.table(pd.DataFrame(data['table']))

    else:
        st.subheader("📅 Weekly Soul Forecast")
        week_res = []
        for i in range(7):
            d = run_mri(datetime.datetime.now() + datetime.timedelta(days=i))
            row = {"Date": d['date'].strftime("%a %d"), "Tara": d['tara'], "Work": d['pillars']['Work'], "Wealth": d['pillars']['Wealth']}
            week_res.append(row)
        st.dataframe(pd.DataFrame(week_res), use_container_width=True)

except Exception as e:
    st.error(f"MRI Fault: {e}")

st.caption("Engine: VedAstro | Logic: Chandra Lagna + Tara Bala | Env: Python 3.13")
