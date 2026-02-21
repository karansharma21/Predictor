import streamlit as st

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
# -------------------------------------

from vedastro import *
import datetime

# --- 2. APP CONFIGURATION ---
st.set_page_config(page_title="Vedic Daily Engine", page_icon="✨")
st.title("✨ Vedic Daily Engine")

# --- 3. SIDEBAR INPUTS ---
st.sidebar.header("User Settings")
name = st.sidebar.text_input("Name", "Arjun")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))
timezone = st.sidebar.text_input("Timezone (e.g., +05:30)", "+05:30")
lat = st.sidebar.number_input("Latitude", value=12.97, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=77.59, format="%.4f")
mode = st.sidebar.selectbox("View Mode", ["Daily", "Weekly"])

# --- 4. DATA INITIALIZATION ---
birth_dt_str = f"{birth_time_input.strftime('%H:%M')} {birth_date.strftime('%d/%m/%Y')} {timezone}"
location = GeoLocation(name, lon, lat)
birth_time = Time(birth_dt_str, location)

def run_forecast(target_date):
    # Sync target date to UTC
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # A. Tara Bala (Soul Filter) 
    # Using PanchangaTable - the most reliable "primitive" data source
    birth_p = Calculate.PanchangaTable(birth_time)
    today_p = Calculate.PanchangaTable(current_time)
    
    # Extracting numeric index (1-27)
    b_num = int(birth_p.Nakshatra.NakshatraName.value__)
    t_num = int(today_p.Nakshatra.NakshatraName.value__)
    
    count = (t_num - b_num + 1)
    if count <= 0: count += 27
    tara_num = count % 9 or 9

    # B. Daily Color & Timing
    day_of_week = Calculate.DayOfWeek(current_time)
    color_map = {
        "Sunday": "Orange", "Monday": "White", "Tuesday": "Red", 
        "Wednesday": "Green", "Thursday": "Yellow", "Friday": "Pink", "Saturday": "Black"
    }
    day_color = color_map.get(str(day_of_week), "White")
    
    # C. Scoring Logic
    # Simple score build
    score = 50 # Baseline
    score += 30 if tara_num in [2,4,6,8,9] else 10
    
    # D. Timing
    rahu_kaal = Calculate.RahuKaalRange(current_time)
    hora = Calculate.CurrentHora(current_time)
    
    return score, day_color, rahu_kaal, hora

# --- 5. UI DISPLAY ---
try:
    if mode == "Daily":
        score, color, rahu, hora = run_forecast(datetime.datetime.now())
        st.metric("Power Score", f"{score}/100")
        st.progress(score / 100)
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"✨ **Hora:** {hora}")
            st.write(f"🚫 **Rahu Kaal:** {rahu}")
        with col2:
            st.write(f"🎨 **Wear:** {color}")
            now_time = Time(datetime.datetime.now().strftime('%H:%M %d/%m/%Y +00:00'), location)
            st.write(f"📅 **Day:** {Calculate.DayOfWeek(now_time)}")

    else:
        st.subheader("7-Day Power Outlook")
        for i in range(7):
            d = datetime.datetime.now() + datetime.timedelta(days=i)
            s, c, _, _ = run_forecast(d)
            st.write(f"**{d.strftime('%a, %d %b')}** — Score: `{s}/100` | Wear: **{c}**")

except Exception as e:
    st.error(f"Connecting to the stars... (Current Status: {e})")

st.caption("Optimized for iPhone Home Screen. Data: VedAstro Engine.")
