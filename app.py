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
st.sidebar.header("📍 Location Discovery")
# Ask for Current City to calculate Rahu Kaal/Gulika Kaal
current_city = st.sidebar.text_input("Enter Current City", "London")

@st.cache_data
def get_geo_details(city_name):
    """Fetches Geo details from VedAstro API database"""
    try:
        # Search for location details
        search_results = GeoLocation.GetGeoLocation(city_name)
        if search_results:
            return search_results
    except:
        # Fallback to a default (London) if search fails
        return GeoLocation("London", -0.1278, 51.5074)

geo = get_geo_details(current_city)
st.sidebar.caption(f"Target: {geo.Name} (Lat: {geo.Latitude}, Lon: {geo.Longitude})")

st.sidebar.divider()
st.sidebar.header("👶 Birth Details")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))

# --- 5. ENGINE CORE ---
# Format Birth Time using the city's timezone automatically
birth_dt_str = f"{birth_time_input.strftime('%H:%M')} {birth_date.strftime('%d/%m/%Y')} {geo.TimezoneStr}"
birth_time = Time(birth_dt_str, geo)

def get_cosmic_data():
    # Setup Current Time at current location
    now = datetime.datetime.now()
    now_str = now.strftime("%H:%M %d/%m/%Y ") + geo.TimezoneStr
    current_time = Time(now_str, geo)
    
    # 1. Precision Timing (Rahu/Gulika)
    try:
        rahu_range = PanchangaCalculator.GetRahuKaalRange(current_time)
        rahu_txt = f"{rahu_range.Start.GetFormattedTime()} - {rahu_range.End.GetFormattedTime()}"
        
        gulika_range = PanchangaCalculator.GetGulikaKaalRange(current_time)
        gulika_txt = f"{gulika_range.Start.GetFormattedTime()} - {gulika_range.End.GetFormattedTime()}"
    except:
        rahu_txt = "Not available for this location"
        gulika_txt = "Not available for this location"

    # 2. Deep Metrics (Planets & Houses)
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    metrics = []
    for p in planets:
        try:
            # Transit house relative to Birth Chart
            house_obj = Calculate.PlanetTransitHouse(p, birth_time, current_time)
            sign_obj = Calculate.PlanetTransitSign(p, current_time)
            metrics.append({
                "Planet": str(p),
                "House": str(house_obj),
                "Sign": str(sign_obj)
            })
        except:
            continue

    # 3. Tara Bala & Tithi
    try:
        tara = int(PanchangaCalculator.GetTaraBala(birth_time, current_time).value__)
        tithi_obj = PanchangaCalculator.GetTithi(current_time)
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
    data = get_cosmic_data()
    
    # POWER SCORE
    score = 40 + (45 if data['tara'] in [2,4,6,8,9] else 10)
    st.metric("Daily Power Score", f"{score}/100")
    st.progress(score / 100)

    # PRECISION TIMING
    st.subheader("⏳ Precision Timing")
    st.info(f"Location: **{geo.Name}** | Timezone: **{geo.TimezoneStr}**")
    c1, c2 = st.columns(2)
    c1.error(f"🚫 **Rahu Kaal (Avoid):**\n\n{data['rahu']}")
    c2.success(f"✅ **Gulika Kaal (Good):**\n\n{data['gulika']}")

    # LIFE CATEGORIES
    st.divider()
    st.subheader("🔮 Life Category Forecast")
    colA, colB, colC, colD = st.columns(4)
    
    moon_house = next((m['House'] for m in data['metrics'] if m['Planet'] == 'Moon'), "1")
    
    colA.info(f"💼 **Work**\n\n{'Peak' if any(x in moon_house for x in ['10','6','11']) else 'Routine'}")
    colB.info(f"💰 **Wealth**\n\n{'Gain Potential' if any(x in moon_house for x in ['2','11']) else 'Neutral'}")
    colC.info(f"🧘 **Health**\n\n{'Vitality High' if data['tara'] in [4,8,9] else 'Rest'}")
    colD.info(f"❤️ **Relations**\n\n{'Harmony' if '7' in moon_house else 'Average'}")

    # DEEP METRICS TABLE
    st.divider()
    st.subheader("📊 Deep Astrological Metrics")
    if data['metrics']:
        st.table(data['metrics'])
    else:
        st.warning("Ensure the city name is recognized for planetary calculations.")

    # TECHNICAL EXPLAINER
    with st.expander("📝 Technical Explainer"):
        st.write(f"**Current Tithi:** {data['tithi']}")
        st.write(f"**Tara Bala:** {data['tara']}/9")
        st.write("**Method:** Calculations are based on *Gochar* (transits) using your Birth Moon as the reference point.")

except Exception as e:
    st.error(f"Synchronizing... {e}")

st.caption("Optimized for iPhone Home Screen. Data: VedAstro.")
