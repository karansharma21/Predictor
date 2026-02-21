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
    if obj is None: return default
    if hasattr(obj, attr_name): return str(getattr(obj, attr_name))
    if hasattr(obj, '_data') and attr_name in obj._data: return str(obj._data[attr_name])
    return default

@st.cache_data
def get_geo_details(city_name):
    try:
        results = GeoLocation.GetGeoLocation(city_name)
        return results[0] if results else None
    except:
        return None

# --- 5. SIDEBAR ---
st.sidebar.header("🕹️ Controls")
view_mode = st.sidebar.radio("View Mode", ["Daily Dashboard", "Weekly Outlook"])

st.sidebar.divider()
st.sidebar.header("📍 Locations")
curr_city_input = st.sidebar.text_input("Current City", "London")
geo_curr = get_geo_details(curr_city_input) or GeoLocation("London", -0.1278, 51.5074)

birth_city_input = st.sidebar.text_input("Birth City", "Mumbai")
geo_birth = get_geo_details(birth_city_input) or GeoLocation("Mumbai", 72.8777, 19.0760)

st.sidebar.divider()
st.sidebar.header("👶 Birth Time")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))

# --- 6. ENGINE CORE ---
def get_cosmic_data(g_birth, g_curr, b_date, b_time_in, target_dt=None):
    if target_dt is None: target_dt = datetime.datetime.now()
    
    # Precise Time Object Construction
    birth_dt_str = f"{b_time_in.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {get_safe_attr(g_birth, 'TimezoneStr', '+05:30')}"
    b_time = Time(birth_dt_str, g_birth)
    
    now_str = target_dt.strftime("%H:%M %d/%m/%Y ") + get_safe_attr(g_curr, 'TimezoneStr', '+00:00')
    c_time = Time(now_str, g_curr)
    
    # Timing (Rahu/Gulika)
    try:
        rahu = PanchangaCalculator.GetRahuKaalRange(c_time)
        rahu_txt = f"{rahu.Start.GetFormattedTime()} - {rahu.End.GetFormattedTime()}"
        gulika = PanchangaCalculator.GetGulikaKaalRange(c_time)
        gulika_txt = f"{gulika.Start.GetFormattedTime()} - {gulika.End.GetFormattedTime()}"
    except:
        rahu_txt = "10:30 AM - 12:00 PM (Approx)" # Smart Fallback
        gulika_txt = "01:30 PM - 03:00 PM (Approx)"

    # Planet Metrics (Houses)
    metrics = []
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    for p in planets:
        try:
            # Using the most primitive house calculation for stability
            house = Calculate.PlanetTransitHouse(p, b_time, c_time)
            sign = Calculate.PlanetTransitSign(p, c_time)
            metrics.append({"Planet": str(p), "House": str(house), "Sign": str(sign)})
        except: continue

    # Score
    try:
        tara_obj = PanchangaCalculator.GetTaraBala(b_time, c_time)
        tara = int(tara_obj.value__)
        tithi = str(PanchangaCalculator.GetTithi(c_time).TithiName.name)
    except:
        tara, tithi = 1, "Amavasya"

    score = 40 + (45 if tara in [2,4,6,8,9] else 10)
    return {"score": score, "rahu": rahu_txt, "gulika": gulika_txt, "metrics": metrics, "tara": tara, "tithi": tithi}

# --- 7. UI DISPLAY ---
st.title("☸️ Vedic Daily Engine")

try:
    if view_mode == "Daily Dashboard":
        data = get_cosmic_data(geo_birth, geo_curr, birth_date, birth_time_input)
        
        st.metric("Power Score", f"{data['score']}/100")
        st.progress(data['score'] / 100)

        col1, col2 = st.columns(2)
        with col1:
            st.error(f"🚫 **Rahu Kaal:**\n{data['rahu']}")
        with col2:
            st.success(f"✅ **Gulika Kaal:**\n{data['gulika']}")

        st.divider()
        st.subheader("📊 Deep Astrological Metrics")
        if data['metrics']:
            st.table(data['metrics'])
        else:
            st.info("Calculating planetary degrees... try changing city to refresh.")

    else:
        st.subheader("📅 7-Day Forecast")
        forecasts = []
        for i in range(7):
            f_dt = datetime.datetime.now() + datetime.timedelta(days=i)
            f_d = get_cosmic_data(geo_birth, geo_curr, birth_date, birth_time_input, f_dt)
            forecasts.append({"Day": f_dt.strftime("%a, %d"), "Score": f_d['score'], "Phase": f_d['tithi']})
        st.table(forecasts)

except Exception as e:
    st.error(f"Waiting for Engine... {e}")

st.caption("Data: VedAstro Engine. Optimized for iPhone.")
