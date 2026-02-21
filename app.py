import sys

# --- 1. CRITICAL PYTHON 3.13 FIX ---
# This fixes the 'ModuleNotFoundError: pkg_resources' issue
try:
    import pkg_resources
except ImportError:
    try:
        from pip._vendor import pkg_resources
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
        import pkg_resources
    sys.modules["pkg_resources"] = pkg_resources

import streamlit as st
from vedastro import *
import datetime

# --- 2. CONFIG ---
st.set_page_config(page_title="Vedic Daily", page_icon="☸️", layout="wide")

# --- 3. GEO-FETCH ---
@st.cache_data
def get_geo(city):
    try:
        res = GeoLocation.GetGeoLocation(city)
        return res[0] if res else None
    except:
        return None

# --- 4. SIDEBAR ---
st.sidebar.header("📍 Settings")
curr_city_name = st.sidebar.text_input("Current City", "London")
birth_city_name = st.sidebar.text_input("Birth City", "Mumbai")

geo_curr = get_geo(curr_city_name) or GeoLocation("London", -0.1278, 51.5074)
geo_birth = get_geo(birth_city_name) or GeoLocation("Mumbai", 72.8777, 19.0760)

st.sidebar.divider()
st.sidebar.header("👶 Birth Details")
b_date = st.sidebar.date_input("Date", datetime.date(1990, 5, 15))
b_time = st.sidebar.time_input("Time", datetime.time(10, 30))

# --- 5. CALCULATION ENGINE ---
def fetch_all_data(g_birth, g_curr, b_d, b_t):
    # Standardize offsets
    birth_str = f"{b_t.strftime('%H:%M')} {b_d.strftime('%d/%m/%Y')} +05:30"
    now_str = datetime.datetime.now().strftime("%H:%M %d/%m/%Y +00:00")
    
    time_birth = Time(birth_str, g_birth)
    time_now = Time(now_str, g_curr)
    
    results = {
        "score": 50,
        "pillars": {"Work": "Stable", "Wealth": "Neutral", "Health": "Good", "Relations": "Average"},
        "planets": [],
        "times": {"Rahu": "Syncing...", "Gulika": "Syncing..."}
    }

    try:
        # A. Timing
        rahu = PanchangaCalculator.GetRahuKaalRange(time_now)
        gulika = PanchangaCalculator.GetGulikaKaalRange(time_now)
        results["times"]["Rahu"] = f"{rahu.Start.GetFormattedTime()} - {rahu.End.GetFormattedTime()}"
        results["times"]["Gulika"] = f"{gulika.Start.GetFormattedTime()} - {gulika.End.GetFormattedTime()}"
        
        # B. Score
        tara = int(PanchangaCalculator.GetTaraBala(time_birth, time_now).value__)
        results["score"] = 40 + (45 if tara in [2,4,6,8,9] else 10)

        # C. Planets & Pillars
        # Get Birth Moon Sign as the starting point (Chandra Lagna)
        birth_moon_sign = int(Calculate.PlanetTransitSign(PlanetName.Moon, time_birth).GetSignName().value__)
        
        plist = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
                 PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
        
        for p in plist:
            curr_sign = Calculate.PlanetTransitSign(p, time_now).GetSignName()
            s_num = int(curr_sign.value__)
            
            # Vedic House: (Current - Birth) + 1
            h_num = (s_num - birth_moon_sign + 1)
            if h_num <= 0: h_num += 12
            
            results["planets"].append({"Planet": str(p), "House": h_num, "Zodiac": str(curr_sign.name)})

            # Logic for Pillars
            if str(p) == "Moon":
                if h_num in [2, 11]: results["pillars"]["Wealth"] = "💹 High Potential"
                if h_num in [10, 6]: results["pillars"]["Work"] = "💼 Focus High"
                if h_num == 7: results["pillars"]["Relations"] = "❤️ Harmony"
            if str(p) == "Mars" and h_num in [6, 8, 12]:
                results["pillars"]["Health"] = "⚠️ Low Energy"
                
    except Exception as e:
        results["error"] = str(e)
        
    return results

# --- 6. UI ---
st.header("☸️ Your Cosmic Live Feed")

try:
    data = fetch_all_data(geo_birth, geo_curr, b_date, b_time)

    st.metric("Power Score", f"{data['score']}/100")
    st.progress(data['score'] / 100)

    col1, col2 = st.columns(2)
    col1.error(f"🚫 **Rahu Kaal**\n\n{data['times']['Rahu']}")
    col2.success(f"✅ **Gulika Kaal**\n\n{data['times']['Gulika']}")

    st.divider()
    st.subheader("🔮 Life Category Breakdown")
    p1, p2, p3, p4 = st.columns(4)
    p1.info(f"💼 **Work**\n\n{data['pillars']['Work']}")
    p2.info(f"💰 **Wealth**\n\n{data['pillars']['Wealth']}")
    p3.info(f"🧘 **Health**\n\n{data['pillars']['Health']}")
    p4.info(f"❤️ **Relations**\n\n{data['pillars']['Relations']}")

    st.divider()
    st.subheader("📊 Planetary Transit Data")
    if data["planets"]:
        st.table(data["planets"])
    else:
        st.warning("🔄 Calculating planetary positions...")

except Exception as e:
    st.error(f"Engine starting... please refresh in a moment.")
