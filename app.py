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

# --- 4. SIDEBAR & LOCATION DISCOVERY ---
@st.cache_data
def get_geo_details(city_name):
    """Fetches Geo details and handles the list return from VedAstro"""
    try:
        results = GeoLocation.GetGeoLocation(city_name)
        if results and len(results) > 0:
            return results[0]
    except:
        pass
    return None

st.sidebar.header("📍 Current Location")
st.sidebar.caption("For today's timing (Rahu Kaal)")
curr_city_input = st.sidebar.text_input("Current City", "London")
geo_curr = get_geo_details(curr_city_input) or GeoLocation("London", -0.1278, 51.5074)
st.sidebar.write(f"🌐 {geo_curr.Name} ({geo_curr.TimezoneStr})")

st.sidebar.divider()

st.sidebar.header("👶 Birth Details")
st.sidebar.caption("For your soul's blueprint")
birth_city_input = st.sidebar.text_input("Birth City", "Mumbai")
geo_birth = get_geo_details(birth_city_input) or GeoLocation("Mumbai", 72.8777, 19.0760)

birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))
st.sidebar.write(f"🕉️ Born in: {geo_birth.Name}")

# --- 5. ENGINE CORE ---
def get_cosmic_data(g_birth, g_curr, b_date, b_time_in):
    # A. Setup Birth Time (Fixed to Birth Location)
    birth_dt_str = f"{b_time_in.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {g_birth.TimezoneStr}"
    b_time = Time(birth_dt_str, g_birth)
    
    # B. Setup Current Time (Fixed to Current Location)
    now = datetime.datetime.now()
    now_str = now.strftime("%H:%M %d/%m/%Y ") + g_curr.TimezoneStr
    c_time = Time(now_str, g_curr)
    
    # 1. Precision Timing (Rahu/Gulika) - Uses Current Location
    try:
        rahu_range = PanchangaCalculator.GetRahuKaalRange(c_time)
        rahu_txt = f"{rahu_range.Start.GetFormattedTime()} - {rahu_range.End.GetFormattedTime()}"
        
        gulika_range = PanchangaCalculator.GetGulikaKaalRange(c_time)
        gulika_txt = f"{gulika_range.Start.GetFormattedTime()} - {gulika_range.End.GetFormattedTime()}"
    except:
        rahu_txt = "Calculating..."
        gulika_txt = "Calculating..."

    # 2. Deep Metrics (Planets & Houses)
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    metrics = []
    for p in planets:
        try:
            # Transit house relative to Birth Chart
            # Logic: Where is the planet NOW (c_time) vs where you were BORN (b_time)
            house_obj = Calculate.PlanetTransitHouse(p, b_time, c_time)
            sign_obj = Calculate.PlanetTransitSign(p, c_time)
            metrics.append({
                "Planet": str(p),
                "House": str(house_obj),
                "Sign": str(sign_obj)
            })
        except:
            continue

    # 3. Tara Bala & Tithi
    try:
        tara = int(PanchangaCalculator.GetTaraBala(b_time, c_time).value__)
        tithi_obj = PanchangaCalculator.GetTithi(c_time)
        tithi_name = str(tithi_obj.TithiName.name)
    except:
        tara = 1
        tithi_name = "Calculating..."

    return {
        "rahu": rahu_txt,
        "gulika": gulika_txt,
        "metrics": metrics,
        "tara": tara,
        "tithi": tithi_name
    }

# --- 6. UI DISPLAY ---
st.title("☸️ Your Cosmic Dashboard")

try:
    data = get_cosmic_data(geo_birth, geo_curr, birth_date, birth_time_input)
    
    # POWER SCORE
    score = 40 + (45 if data['tara'] in [2,4,6,8,9] else 10)
    st.metric("Daily Power Score", f"{score}/100")
    st.progress(score / 100)

    # PRECISION TIMING
    st.subheader("⏳ Precision Timing")
    st.caption(f"Calculated for your current location: **{geo_curr.Name}**")
    c1, c2 = st.columns(2)
    c1.error(f"🚫 **Rahu Kaal (Avoid):**\n\n{data['rahu']}")
    c2.success(f"✅ **Gulika Kaal (Good):**\n\n{data['gulika']}")

    # LIFE CATEGORIES
    st.divider()
    st.subheader("🔮 Life Category Forecast")
    colA, colB, colC, colD = st.columns(4)
    
    moon_house = next((m['House'] for m in data['metrics'] if m['Planet'] == 'Moon'), "1")
    
    colA.info(f"💼 **Work**\n\n{'High Power' if any(x in moon_house for x in ['10','6','11']) else 'Routine'}")
    colB.info(f"💰 **Wealth**\n\n{'Gain Potential' if any(x in moon_house for x in ['2','11']) else 'Neutral'}")
    colC.info(f"🧘 **Health**\n\n{'Vitality High' if data['tara'] in [4,8,9] else 'Rest'}")
    colD.info(f"❤️ **Relations**\n\n{'Harmony' if '7' in moon_house else 'Average'}")

    # DEEP METRICS TABLE
    st.divider()
    st.subheader("📊 Deep Astrological Metrics")
    st.caption(f"Planetary transits as seen from **{geo_curr.Name}** relative to your birth at **{geo_birth.Name}**.")
    if data['metrics']:
        st.table(data['metrics'])
    
    with st.expander("📝 Technical Explainer"):
        st.write(f"**Current Tithi:** {data['tithi']}")
        st.write(f"**Tara Bala:** {data['tara']}/9")
        st.write(f"**Janma Rashi Reference:** {geo_birth.Name}")

except Exception as e:
    st.error(f"Synchronizing... {e}")

st.caption("Optimized for iPhone Home Screen. Data: VedAstro.")
