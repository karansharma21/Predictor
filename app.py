import streamlit as st

# --- EMERGENCY FIX FOR PYTHON 3.13 ---
try:
    import pkg_resources
except ImportError:
    try:
        import pip._vendor.pkg_resources as pkg_resources
    except ImportError:
        # If the above fails, we'll try to use setuptools directly
        from setuptools import pkg_resources
    import sys
    sys.modules["pkg_resources"] = pkg_resources
# -------------------------------------

from vedastro import *
import datetime

# ... the rest of your code follows below ...


# --- APP CONFIGURATION ---
st.set_page_config(page_title="Vedic Daily Engine", page_icon="✨")

st.title("✨ Vedic Daily Engine")
st.sidebar.header("User Settings")

# --- USER INPUTS ---
name = st.sidebar.text_input("Name", "Arjun")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))
timezone = st.sidebar.text_input("Timezone (e.g., +05:30)", "+05:30")
lat = st.sidebar.number_input("Latitude", value=12.97)
lon = st.sidebar.number_input("Longitude", value=77.59)
mode = st.sidebar.selectbox("View Mode", ["Daily", "Weekly"])

# Format time string for VedAstro
birth_dt_str = f"{birth_time_input.strftime('%H:%M')} {birth_date.strftime('%d/%m/%Y')} {timezone}"

# --- ENGINE LOGIC ---
location = GeoLocation(name, lon, lat)
birth_time = Time(birth_dt_str, location)

def run_forecast(target_date):
    now_str = target_date.strftime("%H:%M %d/%m/%Y +00:00")
    current_time = Time(now_str, location)
    
    # 1. Panchang & Soul Harmony (Hierarchy Filter 1 & 2)
   # panchang = Calculate.PanchangaTable(current_time)
   # birth_star_num = int(Calculate.MoonNakshatra(birth_time).NakshatraName)
   # today_star_num = int(Calculate.MoonNakshatra(current_time).NakshatraName)
  #  count = (today_star_num - birth_star_num + 1)
  #  if count <= 0: count += 27
  #  tara_num = count % 9 or 9

        # 1. Panchang & Soul Harmony (Hierarchy Filter 1 & 2)
    panchang = Calculate.PanchangaTable(current_time)
    
    # Corrected: We use the index number (1-27) for the math to work
    birth_star_num = int(Calculate.MoonNakshatra(birth_time).GetIndexNumber())
    today_star_num = int(Calculate.MoonNakshatra(current_time).GetIndexNumber())
    
    count = (today_star_num - birth_star_num + 1)
    if count <= 0: count += 27
    tara_num = count % 9 or 9


    # 2. Precision Timing & Color
    day_of_week = Calculate.DayOfWeek(current_time)
    color_map = {"Sunday": "Orange", "Monday": "White", "Tuesday": "Red", "Wednesday": "Green", "Thursday": "Yellow", "Friday": "Pink", "Saturday": "Black"}
    day_color = color_map.get(str(day_of_week), "White")
    
    # 3. Scoring
    m_house = Calculate.PlanetTransitHouse(PlanetName.Moon, birth_time, current_time)
    m_bindu = Calculate.BhinnashtakavargaChart(birth_time).GetPoints(PlanetName.Moon, current_time)
    
    score = 40 + (30 if tara_num in [2,4,6,8,9] else 10) + (20 if m_house in [House.House1, House.House3, House.House6, House.House11] else 5) + (10 if m_bindu >= 5 else 0)
    
    return score, day_color, panchang, str(Calculate.RahuKaalRange(current_time)), str(Calculate.CurrentHora(current_time))

# --- UI DISPLAY ---
if mode == "Daily":
    score, color, p, rahu, hora = run_forecast(datetime.datetime.now())
    st.metric("Power Score", f"{score}/100")
    st.progress(score / 100)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"🎨 **Best Color:** {color}")
        st.write(f"✨ **Current Hora:** {hora}")
    with col2:
        st.write(f"🚫 **Rahu Kaal:** {rahu}")
        st.write(f"🌕 **Tithi:** {p.Tithi}")

else:
    st.subheader("7-Day Energy Outlook")
    for i in range(7):
        d = datetime.datetime.now() + datetime.timedelta(days=i)
        s, c, _, _, _ = run_forecast(d)
        st.write(f"{d.strftime('%a, %d %b')} — Score: **{s}** ({c})")
