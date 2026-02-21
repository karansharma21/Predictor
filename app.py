import streamlit as st
import sys

# --- 1. PRE-EMPTIVE STRIKE FOR PYTHON 3.13 ---
# We manually inject pkg_resources into the system modules 
# so 'vedastro' finds it immediately upon import.
try:
    import pkg_resources
except ImportError:
    try:
        import pip._vendor.pkg_resources as pkg_resources
    except ImportError:
        try:
            import setuptools.pkg_resources as pkg_resources
        except ImportError:
            pkg_resources = None
    
    if pkg_resources:
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

def get_engine_data(target_date):
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # 5-Limb Data (Panchang)
    p = Calculate.PanchangaTable(current_time)
    
    # Safely extract Nakshatra data from Dictionary (Cloud format)
    try:
        if isinstance(p, dict):
            t_nak_id = int(p['Nakshatra']['NakshatraName']['value__'])
            t_nak_name = str(p['Nakshatra']['NakshatraName']['name'])
            tithi = str(p['Tithi']['TithiName']['name'])
        else:
            t_nak_id = int(p.Nakshatra.NakshatraName.value__)
            t_nak_name = str(p.Nakshatra.NakshatraName.name)
            tithi = str(p.Tithi.TithiName.name)
    except:
        t_nak_id, t_nak_name, tithi = 1, "Unknown", "Unknown"

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
        "nakshatra": t_nak_name,
        "rahu": str(rahu),
        "gulika": str(gulika),
        "day": target_date.strftime("%A")
    }

# --- 6. UI DISPLAY ---
st.title("☸️ Your Cosmic Dashboard")

try:
    data = get_engine_data(datetime.datetime.now())
    
    # TOP METRICS
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
    
    # Mapping Tara Bala to Life Areas
    # 2=Sampat (Wealth), 4=Kshema (Health), 6=Sadhana (Work), 8=Mitra (Relations)
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

    # SCORING TABLE
    st.divider()
    with st.expander("📊 View Detailed Metrics"):
        st.table([
            {"Metric": "Tara Bala", "Value": f"{data['tara']}/9", "Status": "Auspicious" if data['tara'] in [2,4,6,8,9] else "Average"},
            {"Metric": "Tithi", "Value": data['tithi'], "Status": "Current"},
            {"Metric": "Nakshatra", "Value": data['nakshatra'], "Status": "Current"},
            {"Metric": "Day Lord", "Value": data['day'], "Status": "Ruling"}
        ])

except Exception as e:
    st.warning("Syncing with the stars... please wait.")
    st.caption(f"Technical note: {e}")

st.caption("Optimized for iPhone Home Screen. Powered by VedAstro.")
