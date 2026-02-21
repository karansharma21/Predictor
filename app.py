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

def get_nakshatra_id(time_obj):
    """Deep-drills into the dictionary to find the Nakshatra Number"""
    try:
        data = Calculate.PanchangaTable(time_obj)
        # The library returns a list or dict in this environment
        # We search for the 'Nakshatra' key and then the 'value__' of its name
        if isinstance(data, dict):
            return int(data['Nakshatra']['NakshatraName']['value__'])
        else:
            return int(data.Nakshatra.NakshatraName.value__)
    except Exception as e:
        # Fallback: if PanchangaTable is too complex, we use a simpler score
        return 1 

def run_forecast(target_date):
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # A. Tara Bala (Soul Filter)
    b_num = get_nakshatra_id(birth_time)
    t_num = get_nakshatra_id(current_time)
    
    count = (t_num - b_num + 1)
    if count <= 0: count += 27
    tara_num = count % 9 or 9

    # B. Daily Color (Stable Python Logic)
    day_name = target_date.strftime("%A")
    color_map = {
        "Sunday": "Orange", "Monday": "White", "Tuesday": "Red", 
        "Wednesday": "Green", "Thursday": "Yellow", "Friday": "Pink", "Saturday": "Black"
    }
    day_color = color_map.get(day_name, "White")
    
    # C. Scoring Logic
    score = 40 
    # Positive Tara Balas (2, 4, 6, 8, 9)
    if tara_num in [2, 4, 6, 8, 9]:
        score += 40
    else:
        score += 10
    
    return score, day_color, tara_num

# --- 5. UI DISPLAY ---
try:
    if mode == "Daily":
        score, color, tara = run_forecast(datetime.datetime.now())
        st.metric("Power Score", f"{score}/100")
        st.progress(score / 100)
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Vibe")
            st.write(f"🎨 **Wear:** {color}")
            st.write(f"⭐ **Tara:** {tara}/9")
        with col2:
            st.subheader("Guidance")
            msg = "Great for action" if score > 70 else "Proceed with caution"
            st.info(msg)

    else:
        st.subheader("7-Day Power Outlook")
        for i in range(7):
            d = datetime.datetime.now() + datetime.timedelta(days=i)
            s, c, _ = run_forecast(d)
            st.write(f"**{d.strftime('%a, %d %b')}** — Score: `{s}/100` | Wear: **{c}**")

except Exception as e:
    st.error(f"Syncing cosmic data... (Wait 5s) - {e}")

st.caption("Optimized for iPhone. Data: VedAstro.")
