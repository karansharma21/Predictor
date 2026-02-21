import streamlit as st
import sys
from vedastro import *
import datetime

# --- 1. PYTHON 3.13 FIX ---
try:
    import pkg_resources
except ImportError:
    try:
        import pip._vendor.pkg_resources as pkg_resources
    except ImportError:
        pkg_resources = None
    if pkg_resources:
        sys.modules["pkg_resources"] = pkg_resources

# --- 2. APP CONFIG ---
st.set_page_config(page_title="Vedic Daily Engine", page_icon="☸️", layout="wide")

# --- 3. SIDEBAR ---
st.sidebar.header("Birth & Location Details")
name = st.sidebar.text_input("Name", "User")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))
timezone = st.sidebar.text_input("Timezone", "+05:30")
lat = st.sidebar.number_input("Latitude", value=12.97, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=77.59, format="%.4f")

# --- 4. ENGINE CORE ---
birth_dt_str = f"{birth_time_input.strftime('%H:%M')} {birth_date.strftime('%d/%m/%Y')} {timezone}"
location = GeoLocation(name, lon, lat)
birth_time = Time(birth_dt_str, location)

def get_detailed_data(target_date):
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # Raw Data Fetch
    panchang = Calculate.PanchangaTable(current_time)
    
    # Timing Extraction
    try:
        rahu = str(Calculate.RahuKaalRange(current_time))
        gulika = str(Calculate.GulikaKaalRange(current_time))
    except:
        rahu = "Calculated at Sunrise" # Fallback
        gulika = "Calculated at Sunrise"

    # Planetary Positions (For Metrics Table)
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    metrics = []
    for p in planets:
        house = Calculate.PlanetTransitHouse(p, birth_time, current_time)
        sign = Calculate.PlanetTransitSign(p, current_time)
        metrics.append({"Planet": str(p), "House": str(house), "Sign": str(sign)})

    # Tara Bala
    try:
        b_nak = int(Calculate.PanchangaTable(birth_time)['Nakshatra']['NakshatraName']['value__'])
        t_nak = int(panchang['Nakshatra']['NakshatraName']['value__'])
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
        "tithi": str(panchang.get('Tithi', {}).get('TithiName', {}).get('name', 'Unknown'))
    }

# --- 5. UI DISPLAY ---
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
    
    # Dynamic Logic based on Metrics
    moon_house = next((m['House'] for m in data['metrics'] if m['Planet'] == 'Moon'), "House1")
    
    colA.info(f"💼 **Work**\n\n{'Peak' if '10' in moon_house or '6' in moon_house else 'Stable'}")
    colB.info(f"💰 **Wealth**\n\n{'Gain' if '2' in moon_house or '11' in moon_house else 'Neutral'}")
    colC.info(f"🧘 **Health**\n\n{'Strong' if data['tara'] in [4,8,9] else 'Rest'}")
    colD.info(f"❤️ **Relations**\n\n{'Harmony' if '7' in moon_house else 'Average'}")

    # 4. DEEP METRICS TABLE
    st.divider()
    st.subheader("📊 Deep Astrological Metrics")
    st.write("These calculations drive your daily score and life category forecasts:")
    st.table(data['metrics'])
    
    with st.expander("📝 Technical Explainer"):
        st.write(f"**Current Tithi:** {data['tithi']}")
        st.write(f"**Your Tara Bala:** {data['tara']}/9")
        st.caption("House transits are calculated relative to your Birth Moon (Janma Rashi).")

except Exception as e:
    st.error(f"Engine is syncing... {e}")

st.caption("Optimized for iPhone Home Screen. Data: VedAstro Engine.")
