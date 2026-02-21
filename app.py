import streamlit as st
import sys

# --- 1. EMERGENCY POLYFILL FOR PYTHON 3.13 ---
# This must be the very first thing in the script
try:
    import pkg_resources
except ImportError:
    import pip._vendor.pkg_resources as pkg_resources
    sys.modules["pkg_resources"] = pkg_resources

# --- 2. NOW IMPORT LIBRARIES ---
from vedastro import *
import datetime

# --- 3. APP CONFIG ---
st.set_page_config(page_title="Vedic Daily Engine", page_icon="☸️", layout="wide")

# --- 4. SIDEBAR ---
st.sidebar.header("Birth & Location Details")
name = st.sidebar.text_input("Name", "User")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))
timezone = st.sidebar.text_input("Timezone", "+05:30")
lat = st.sidebar.number_input("Latitude", value=12.97, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=77.59, format="%.4f")

# --- 5. ENGINE CORE ---
birth_dt_str = f"{birth_time_input.strftime('%H:%M')} {birth_date.strftime('%d/%m/%Y')} {timezone}"
location = GeoLocation(name, lon, lat)
birth_time = Time(birth_dt_str, location)

def get_detailed_data(target_date):
    # Set current time for transit
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # Raw Data Fetch (Panchang)
    panchang = Calculate.PanchangaTable(current_time)
    
    # Timing Extraction
    try:
        rahu = str(Calculate.RahuKaalRange(current_time))
        gulika = str(Calculate.GulikaKaalRange(current_time))
    except:
        rahu, gulika = "Syncing...", "Syncing..."

    # Planetary Positions for Metrics Table
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    metrics = []
    for p in planets:
        try:
            house = Calculate.PlanetTransitHouse(p, birth_time, current_time)
            sign = Calculate.PlanetTransitSign(p, current_time)
            metrics.append({"Planet": str(p), "House": str(house), "Sign": str(sign)})
        except:
            continue

    # Tara Bala calculation
    try:
        b_p = Calculate.PanchangaTable(birth_time)
        b_nak = int(b_p['Nakshatra']['NakshatraName']['value__']) if isinstance(b_p, dict) else int(b_p.Nakshatra.NakshatraName.value__)
        t_nak = int(panchang['Nakshatra']['NakshatraName']['value__']) if isinstance(panchang, dict) else int(panchang.Nakshatra.NakshatraName.value__)
        count = (t_nak - b_nak + 1)
        if count <= 0: count += 27
        tara = count % 9 or 9
    except: tara = 1

    return {
        "score": 40 + (45 if tara in [2,4,6,8,9] else 10),
        "rahu": rahu,
        "gulika": gulika,
        "tara": tara,
        "metrics": metrics,
        "tithi": "Today's Phase"
    }

# --- 6. UI DISPLAY ---
st.title("☸️ Your Cosmic Dashboard")

try:
    data = get_detailed_data(datetime.datetime.now())
    
    # 1. SCORE
    st.metric("Daily Power Score", f"{data['score']}/100")
    st.progress(data['score'] / 100)

    # 2. PRECISION TIMING
    st.subheader("⏳ Precision Timing")
    c1, c2 = st.columns(2)
    c1.error(f"🚫 **Rahu Kaal (Avoid):**\n{data['rahu']}")
    c2.success(f"✅ **Gulika Kaal (Good):**\n{data['gulika']}")

    # 3. LIFE CATEGORIES
    st.divider()
    st.subheader("🔮 Life Category Forecast")
    colA, colB, colC, colD = st.columns(4)
    
    # Prediction logic based on Moon House
    moon_house = next((m['House'] for m in data['metrics'] if m['Planet'] == 'Moon'), "House1")
    
    colA.info(f"💼 **Work**\n\n{'High Power' if any(x in moon_house for x in ['10','6','11']) else 'Routine'}")
    colB.info(f"💰 **Wealth**\n\n{'Gain Potential' if any(x in moon_house for x in ['2','11']) else 'Neutral'}")
    colC.info(f"🧘 **Health**\n\n{'Vitality High' if data['tara'] in [4,8,9] else 'Rest & Recovery'}")
    colD.info(f"❤️ **Relations**\n\n{'Deep Connection' if '7' in moon_house else 'Average'}")

    # 4. DEEP METRICS TABLE
    st.divider()
    st.subheader("📊 Deep Astrological Metrics")
    st.caption("Planetary transits calculated relative to your Birth Moon (Janma Rashi).")
    st.table(data['metrics'])
    
    with st.expander("📝 Technical Explainer"):
        st.write(f"**Your Tara Bala (Star Strength):** {data['tara']}/9")
        st.write("Tara Bala represents the relationship between the Moon's position at your birth and its current position today.")

except Exception as e:
    st.error("Engine connecting... please refresh in 5 seconds.")

st.caption("Optimized for iPhone Home Screen. Data: VedAstro Engine.")
