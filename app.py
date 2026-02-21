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

# --- 4. SIDEBAR ---
st.sidebar.header("Birth Details")
name = st.sidebar.text_input("Name", "User")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))
timezone = st.sidebar.text_input("Timezone (Offset)", "+05:30")

st.sidebar.header("Location (Current)")
# Ensure these are forced to float for the C# engine bridge
lat = float(st.sidebar.number_input("Latitude", value=12.97, format="%.4f"))
lon = float(st.sidebar.number_input("Longitude", value=77.59, format="%.4f"))

# --- 5. ENGINE CORE ---
# Format the birth string precisely
birth_dt_str = f"{birth_time_input.strftime('%H:%M')} {birth_date.strftime('%d/%m/%Y')} {timezone}"
location = GeoLocation(name, lon, lat)
birth_time = Time(birth_dt_str, location)

def get_cosmic_data():
    # 1. Setup Current Time
    now = datetime.datetime.now()
    now_str = now.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # 2. Precision Timing (Rahu/Gulika)
    # We use the calculator directly with the location-synced time
    try:
        rahu_range = PanchangaCalculator.GetRahuKaalRange(current_time)
        rahu_txt = f"{rahu_range.Start.GetFormattedTime()} - {rahu_range.End.GetFormattedTime()}"
        
        gulika_range = PanchangaCalculator.GetGulikaKaalRange(current_time)
        gulika_txt = f"{gulika_range.Start.GetFormattedTime()} - {gulika_range.End.GetFormattedTime()}"
    except:
        rahu_txt = "Calculating... (Check Lat/Lon)"
        gulika_txt = "Calculating... (Check Lat/Lon)"

    # 3. Deep Metrics (Planets & Houses)
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    metrics = []
    for p in planets:
        try:
            # Calculate House transit relative to Birth Time
            house_obj = Calculate.PlanetTransitHouse(p, birth_time, current_time)
            sign_obj = Calculate.PlanetTransitSign(p, current_time)
            
            metrics.append({
                "Planet": str(p),
                "House": str(house_obj),
                "Sign": str(sign_obj)
            })
        except:
            continue

    # 4. Tara Bala & Tithi
    try:
        tara = int(PanchangaCalculator.GetTaraBala(birth_time, current_time).value__)
        tithi_obj = PanchangaCalculator.GetTithi(current_time)
        tithi_name = str(tithi_obj.TithiName.name)
    except:
        tara = 1
        tithi_name = "Unknown"

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
    data = get_cosmic_data()
    
    # 1. TOP METRICS
    score = 40 + (45 if data['tara'] in [2,4,6,8,9] else 10)
    st.metric("Daily Power Score", f"{score}/100")
    st.progress(score / 100)

    # 2. PRECISION TIMING
    st.subheader("⏳ Precision Timing")
    c1, c2 = st.columns(2)
    c1.error(f"🚫 **Rahu Kaal (Avoid):**\n\n{data['rahu']}")
    c2.success(f"✅ **Gulika Kaal (Good):**\n\n{data['gulika']}")

    # 3. LIFE CATEGORIES
    st.divider()
    st.subheader("🔮 Life Category Forecast")
    colA, colB, colC, colD = st.columns(4)
    
    # Logic based on Deep Metrics
    moon_house = next((m['House'] for m in data['metrics'] if m['Planet'] == 'Moon'), "1")
    
    colA.info(f"💼 **Work**\n\n{'Peak' if any(x in moon_house for x in ['10','6','11']) else 'Routine'}")
    colB.info(f"💰 **Wealth**\n\n{'Gain Potential' if any(x in moon_house for x in ['2','11']) else 'Neutral'}")
    colC.info(f"🧘 **Health**\n\n{'Vitality High' if data['tara'] in [4,8,9] else 'Rest'}")
    colD.info(f"❤️ **Relations**\n\n{'Harmony' if '7' in moon_house else 'Average'}")

    # 4. DEEP METRICS TABLE
    st.divider()
    st.subheader("📊 Deep Astrological Metrics")
    if data['metrics']:
        st.table(data['metrics'])
    else:
        st.warning("Deep metrics are initializing. Please ensure Latitude/Longitude are correct.")

    # 5. TECHNICAL EXPLAINER
    with st.expander("📝 Technical Explainer"):
        st.write(f"**Current Tithi:** {data['tithi']}")
        st.write(f"**Tara Bala:** {data['tara']}/9")
        st.write("**House System:** Calculated using the *Janma Rashi* (Birth Moon) as the 1st House.")
        st.write("**Calculation Engine:** VedAstro (C# Bridge)")

except Exception as e:
    st.error(f"Synchronizing... {e}")

st.caption("Optimized for iPhone Home Screen. Data: VedAstro Engine.")
