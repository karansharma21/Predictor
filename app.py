import streamlit as st
import sys

# --- 1. PRE-EMPTIVE STRIKE FOR PYTHON 3.13 ---
# This MUST happen before 'from vedastro import *'
try:
    import pkg_resources
except ImportError:
    # We create a "fake" pkg_resources so the library doesn't crash
    from setuptools import fallback_version_string if 'setuptools' in sys.modules else None
    import pip._vendor.pkg_resources as pkg_resources
    sys.modules["pkg_resources"] = pkg_resources

# --- 2. NOW IMPORT LIBRARIES ---
from vedastro import *
import datetime

# --- THE REST OF YOUR CODE ---


# --- 1. EMERGENCY FIX FOR PYTHON 3.13 ---
try:
    import pkg_resources
except ImportError:
    try:
        import pip._vendor.pkg_resources as pkg_resources
    except ImportError:
        from setuptools import pkg_resources
    import sys
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

def get_engine_data(target_date):
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # 5-Limb Data (Panchang)
    p = Calculate.PanchangaTable(current_time)
    
    # Safely extract Nakshatra names and IDs
    try:
        if isinstance(p, dict):
            t_nak = str(p['Nakshatra']['NakshatraName']['name'])
            t_nak_id = int(p['Nakshatra']['NakshatraName']['value__'])
            tithi = str(p['Tithi']['TithiName']['name'])
        else:
            t_nak = str(p.Nakshatra.NakshatraName.name)
            t_nak_id = int(p.Nakshatra.NakshatraName.value__)
            tithi = str(p.Tithi.TithiName.name)
    except:
        t_nak, t_nak_id, tithi = "Unknown", 1, "Unknown"

    # Birth Nakshatra check
    try:
        b_p = Calculate.PanchangaTable(birth_time)
        b_nak_id = int(b_p['Nakshatra']['NakshatraName']['value__']) if isinstance(b_p, dict) else int(b_p.Nakshatra.NakshatraName.value__)
    except:
        b_nak_id = 1

    # Tara Bala calculation
    count = (t_nak_id - b_nak_id + 1)
    if count <= 0: count += 27
    tara_num = count % 9 or 9
    
    # Timing
    rahu = Calculate.RahuKaalRange(current_time)
    gulika = Calculate.GulikaKaalRange(current_time)
    
    return {
        "tara": tara_num,
        "tithi": tithi,
        "nakshatra": t_nak,
        "rahu": str(rahu),
        "gulika": str(gulika),
        "day": target_date.strftime("%A")
    }

# --- 5. UI DISPLAY ---
st.title("☸️ Your Cosmic Dashboard")

try:
    data = get_engine_data(datetime.datetime.now())
    
    # TOP METRICS
    score = 40 + (35 if data['tara'] in [2,4,6,8,9] else 10)
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
    
    categories = {
        "Work": ("💼", "High Focus" if data['tara'] in [2,6,9] else "Routine"),
        "Wealth": ("💰", "Gain Potential" if data['tara'] in [2,4,9] else "Stable"),
        "Health": ("🧘", "Vitality High" if data['tara'] in [4,8,9] else "Low Energy"),
        "Relations": ("❤️", "Harmony" if data['tara'] in [3,5,7] else "Average")
    }
    
    with c1: st.info(f"{categories['Work'][0]} **Work**\n\n{categories['Work'][1]}")
    with c2: st.info(f"{categories['Wealth'][0]} **Wealth**\n\n{categories['Wealth'][1]}")
    with c3: st.info(f"{categories['Health'][0]} **Health**\n\n{categories['Health'][1]}")
    with c4: st.info(f"{categories['Relations'][0]} **Relations**\n\n{categories['Relations'][1]}")

    # SCORING TABLE
    st.divider()
    with st.expander("📊 View Scoring Metrics"):
        st.table([
            {"Metric": "Tara Bala (Soul Strength)", "Value": f"{data['tara']}/9", "Status": "Excellent" if data['tara'] in [2,4,6,8,9] else "Challenging"},
            {"Metric": "Tithi (Lunar Day)", "Value": data['tithi'], "Status": "Active"},
            {"Metric": "Current Nakshatra", "Value": data['nakshatra'], "Status": "Active"},
            {"Metric": "Day Lord", "Value": data['day'], "Status": "Active"}
        ])

except Exception as e:
    st.warning(f"Engine warming up... ({e})")

st.caption("Customized for iPhone Home Screen. Powered by VedAstro Engine.")
