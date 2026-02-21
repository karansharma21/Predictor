import streamlit as st
import sys

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

# --- 2. IMPORT LIBRARIES ---
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

def get_engine_data(target_date):
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # A. Get Panchang (The 5 Pillars)
    # Using the most stable method: PanchangaCalculator
    try:
        t_nak_id = int(PanchangaCalculator.GetMoonNakshatra(current_time).NakshatraName.value__)
        t_nak_name = str(PanchangaCalculator.GetMoonNakshatra(current_time).NakshatraName.name)
        tithi = str(PanchangaCalculator.GetTithi(current_time).TithiName.name)
    except:
        t_nak_id, t_nak_name, tithi = 1, "Unknown", "Unknown"

    # B. Birth Nakshatra
    try:
        b_nak_id = int(PanchangaCalculator.GetMoonNakshatra(birth_time).NakshatraName.value__)
    except:
        b_nak_id = 1

    # C. Tara Bala Calculation
    count = (t_nak_id - b_nak_id + 1)
    if count <= 0: count += 27
    tara_num = count % 9 or 9
    
    # D. Precision Timing (Auspicious/Inauspicious)
    # Using the specific timing calculator to avoid 'AttributeError'
    try:
        rahu = str(PanchangaCalculator.GetRahuKaalRange(current_time))
        gulika = str(PanchangaCalculator.GetGulikaKaalRange(current_time))
    except:
        rahu, gulika = "Check Local Calendar", "Check Local Calendar"
    
    return {
        "tara": tara_num,
        "tithi": tithi,
        "nakshatra": t_nak_name,
        "rahu": rahu,
        "gulika": gulika,
        "day": target_date.strftime("%A")
    }

# --- 6. UI DISPLAY ---
st.title("☸️ Your Cosmic Dashboard")

try:
    data = get_engine_data(datetime.datetime.now())
    
    # POWER SCORE
    score = 40 + (45 if data['tara'] in [2,4,6,8,9] else 10)
    st.metric("Daily Power Score", f"{score}/100")
    st.progress(score / 100)

    # TIMING SECTION
    st.subheader("⏳ Precision Timing")
    col1, col2 = st.columns(2)
    with col1:
        st.error(f"🚫 **Avoid (Rahu Kaal):** \n{data['rahu']}")
    with col2:
        st.success(f"✅ **Good (Gulika Kaal):** \n{data['gulika']}")

    # LIFE CATEGORIES
    st.divider()
    st.subheader("🔮 Life Category Forecast")
    c1, c2, c3, c4 = st.columns(4)
    
    cat_logic = {
        "Work": "High Focus" if data['tara'] in [2,6,9] else "Routine",
        "Wealth": "Gain Potential" if data['tara'] in [2,4,9] else "Stable",
        "Health": "Vitality High" if data['tara'] in [4,8,9] else "Conserve Energy",
        "Relations": "Harmony" if data['tara'] in [3,8,9] else "Neutral"
    }
    
    c1.info(f"💼 **Work**\n\n{cat_logic['Work']}")
    c2.info(f"💰 **Wealth**\n\n{cat_logic['Wealth']}")
    c3.info(f"🧘 **Health**\n\n{cat_logic['Health']}")
    c4.info(f"❤️ **Relations**\n\n{cat_logic['Relations']}")

    # METRICS TABLE
    with st.expander("📊 View Detailed Metrics"):
        st.table([
            {"Metric": "Tara Bala", "Value": f"{data['tara']}/9", "Status": "Auspicious" if data['tara'] in [2,4,6,8,9] else "Average"},
            {"Metric": "Tithi", "Value": data['tithi'], "Status": "Current"},
            {"Metric": "Nakshatra", "Value": data['nakshatra'], "Status": "Current"}
        ])

except Exception as e:
    st.warning("Finalizing data...")
    st.caption(f"Waiting for engine: {e}")

st.caption("Optimized for iPhone Home Screen. Powered by VedAstro.")
