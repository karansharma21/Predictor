import streamlit as st
import sys

# --- 1. PYTHON 3.13 POLYFILL ---
try:
    import pkg_resources
except ImportError:
    try:
        import pip._vendor.pkg_resources as pkg_resources
        sys.modules["pkg_resources"] = pkg_resources
    except:
        pass

# --- 2. IMPORTS ---
from vedastro import *
import datetime

# --- 3. APP CONFIG ---
st.set_page_config(page_title="Vedic Daily Engine", page_icon="☸️", layout="wide")

# --- 4. SAFE DATA EXTRACTORS ---
def get_safe_attr(obj, attr_name, default="Unknown"):
    """Forcefully extracts attributes from VedAstro objects or dicts"""
    if obj is None: return default
    # Try standard attribute
    if hasattr(obj, attr_name):
        return getattr(obj, attr_name)
    # Try internal data dictionary (common in Python wrappers)
    if hasattr(obj, '_data') and attr_name in obj._data:
        return obj._data[attr_name]
    # Try dictionary access
    if isinstance(obj, dict) and attr_name in obj:
        return obj[attr_name]
    return default

@st.cache_data
def get_geo_details(city_name):
    """Fetches Geo details safely and handles list returns"""
    try:
        results = GeoLocation.GetGeoLocation(city_name)
        if isinstance(results, list) and len(results) > 0:
            return results[0]
        return results
    except:
        return None

# --- 5. SIDEBAR & LOCATION ---
st.sidebar.header("📍 Current Location")
st.sidebar.caption("For Rahu Kaal & Daily Timing")
curr_city_input = st.sidebar.text_input("Current City", "London")
geo_curr = get_geo_details(curr_city_input) or GeoLocation("London", -0.1278, 51.5074)

# Safely display location info
curr_name = get_safe_attr(geo_curr, 'Name', 'London')
curr_tz = get_safe_attr(geo_curr, 'TimezoneStr', '+00:00')
st.sidebar.write(f"🌐 {curr_name} ({curr_tz})")

st.sidebar.divider()

st.sidebar.header("👶 Birth Details")
st.sidebar.caption("For your Soul's Score")
birth_city_input = st.sidebar.text_input("Birth City", "Mumbai")
geo_birth = get_geo_details(birth_city_input) or GeoLocation("Mumbai", 72.8777, 19.0760)

birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))
birth_name = get_safe_attr(geo_birth, 'Name', 'Mumbai')
st.sidebar.write(f"🕉️ Born in: {birth_name}")

# --- 6. ENGINE CORE ---
def get_cosmic_data(g_birth, g_curr, b_date, b_time_in, target_dt=None):
    if target_dt is None:
        target_dt = datetime.datetime.now()
        
    tz_birth = get_safe_attr(g_birth, 'TimezoneStr', '+05:30')
    tz_curr = get_safe_attr(g_curr, 'TimezoneStr', '+00:00')
    
    # Setup Times
    birth_dt_str = f"{b_time_in.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {tz_birth}"
    b_time = Time(birth_dt_str, g_birth)
    
    now_str = target_dt.strftime("%H:%M %d/%m/%Y ") + tz_curr
    c_time = Time(now_str, g_curr)
    
    # Timing
    try:
        rahu = PanchangaCalculator.GetRahuKaalRange(c_time)
        rahu_txt = f"{rahu.Start.GetFormattedTime()} - {rahu.End.GetFormattedTime()}"
        gulika = PanchangaCalculator.GetGulikaKaalRange(c_time)
        gulika_txt = f"{gulika.Start.GetFormattedTime()} - {gulika.End.GetFormattedTime()}"
    except:
        rahu_txt = gulika_txt = "Calculating..."

    # Planets & Houses
    metrics = []
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    for p in planets:
        try:
            h = Calculate.PlanetTransitHouse(p, b_time, c_time)
            s = Calculate.PlanetTransitSign(p, c_time)
            metrics.append({"Planet": str(p), "House": str(h), "Sign": str(s)})
        except: continue

    # Score
    try:
        tara = int(PanchangaCalculator.GetTaraBala(b_time, c_time).value__)
        tithi = str(PanchangaCalculator.GetTithi(c_time).TithiName.name)
    except:
        tara, tithi = 1, "Neutral"

    score = 40 + (45 if tara in [2,4,6,8,9] else 10)
    return {"score": score, "rahu": rahu_txt, "gulika": gulika_txt, "metrics": metrics, "tara": tara, "tithi": tithi}

# --- 7. UI DISPLAY ---
st.title("☸️ Your Cosmic Dashboard")

try:
    data = get_cosmic_data(geo_birth, geo_curr, birth_date, birth_time_input)
    
    st.metric("Daily Power Score", f"{data['score']}/100")
    st.progress(data['score'] / 100)

    st.subheader("⏳ Precision Timing")
    st.caption(f"Calculated for **{curr_name}**")
    c1, c2 = st.columns(2)
    c1.error(f"🚫 **Rahu Kaal (Avoid):**\n\n{data['rahu']}")
    c2.success(f"✅ **Gulika Kaal (Good):**\n\n{data['gulika']}")

    st.divider()
    st.subheader("🔮 Life Categories")
    colA, colB, colC, colD = st.columns(4)
    m_house = next((m['House'] for m in data['metrics'] if m['Planet'] == 'Moon'), "1")
    
    colA.info(f"💼 **Work**\n\n{'High' if '10' in m_house or '6' in m_house else 'Neutral'}")
    colB.info(f"💰 **Wealth**\n\n{'Gain' if '2' in m_house or '11' in m_house else 'Neutral'}")
    colC.info(f"🧘 **Health**\n\n{'Strong' if data['tara'] in [4,8,9] else 'Rest'}")
    colD.info(f"❤️ **Relations**\n\n{'Harmony' if '7' in m_house else 'Average'}")

    st.divider()
    st.subheader("📅 7-Day Forecast")
    forecast_list = []
    for i in range(7):
        f_dt = datetime.datetime.now() + datetime.timedelta(days=i)
        f_d = get_cosmic_data(geo_birth, geo_curr, birth_date, birth_time_input, f_dt)
        forecast_list.append({"Date": f_dt.strftime("%a, %d %b"), "Power Score": f_d['score'], "Condition": "Positive" if f_d['score'] > 60 else "Neutral"})
    st.dataframe(forecast_list, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📊 Deep Astrological Metrics (Today)")
    st.table(data['metrics'])

except Exception as e:
    st.error(f"Synchronizing engine... {e}")

st.caption("Optimized for iPhone. Data: VedAstro Engine.")
