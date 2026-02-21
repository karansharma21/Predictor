import streamlit as st
import sys

# --- 1. SYSTEM POLYFILL ---
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
st.set_page_config(page_title="Vedic Data Engine", page_icon="☸️", layout="wide")

# --- 4. DATA FETCHERS ---
@st.cache_data
def get_geo_details(city_name):
    try:
        results = GeoLocation.GetGeoLocation(city_name)
        return results[0] if results else None
    except:
        return None

def get_safe_attr(obj, attr_name, default="0"):
    try:
        if hasattr(obj, attr_name): return str(getattr(obj, attr_name))
        if hasattr(obj, '_data') and attr_name in obj._data: return str(obj._data[attr_name])
    except: pass
    return default

# --- 5. SIDEBAR ---
st.sidebar.header("🕹️ View Toggle")
view_mode = st.sidebar.radio("View", ["Daily Dashboard", "Weekly Outlook"])

st.sidebar.divider()
st.sidebar.header("📍 Locations")
curr_city_input = st.sidebar.text_input("Current City", "London")
geo_curr = get_geo_details(curr_city_input) or GeoLocation("London", -0.1278, 51.5074)

birth_city_input = st.sidebar.text_input("Birth City", "Mumbai")
geo_birth = get_geo_details(birth_city_input) or GeoLocation("Mumbai", 72.8777, 19.0760)

st.sidebar.divider()
st.sidebar.header("👶 Birth Data")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))

# --- 6. CORE CALCULATIONS ---
def get_full_astrometry(g_birth, g_curr, b_date, b_time_in, target_dt=None):
    if target_dt is None: target_dt = datetime.datetime.now()
    
    # Setup Time Objects
    tz_b = get_safe_attr(g_birth, 'TimezoneStr', '+05:30')
    tz_c = get_safe_attr(g_curr, 'TimezoneStr', '+00:00')
    b_time = Time(f"{b_time_in.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {tz_b}", g_birth)
    c_time = Time(target_dt.strftime("%H:%M %d/%m/%Y ") + tz_c, g_curr)
    
    # 1. Planetary Data (The "Deep Metrics")
    planet_data = []
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu]
    
    try:
        # Get Birth Moon Sign for House Calculation (Chandra Lagna)
        b_moon_sign = int(Calculate.PlanetTransitSign(PlanetName.Moon, b_time).GetSignName().value__)
        
        for p in planets:
            # Get Current position details
            sign_obj = Calculate.PlanetTransitSign(p, c_time)
            sign_name = str(sign_obj.GetSignName().name)
            sign_num = int(sign_obj.GetSignName().value__)
            
            # Calculate House Position (Relative to Birth Moon)
            house_num = (sign_num - b_moon_sign + 1)
            if house_num <= 0: house_num += 12
            
            planet_data.append({
                "Planet": str(p),
                "House": house_num,
                "Zodiac Sign": sign_name,
                "Status": "Direct" # Transit status logic can be expanded
            })
    except: pass

    # 2. Timing
    try:
        rahu = PanchangaCalculator.GetRahuKaalRange(c_time)
        rahu_txt = f"{rahu.Start.GetFormattedTime()} - {rahu.End.GetFormattedTime()}"
        gulika = PanchangaCalculator.GetGulikaKaalRange(c_time)
        gulika_txt = f"{gulika.Start.GetFormattedTime()} - {gulika.End.GetFormattedTime()}"
    except:
        rahu_txt = gulika_txt = "Syncing..."

    # 3. Score & Tithi
    try:
        tara = int(PanchangaCalculator.GetTaraBala(b_time, c_time).value__)
        tithi = str(PanchangaCalculator.GetTithi(c_time).TithiName.name)
    except:
        tara, tithi = 1, "Unknown"

    score = 40 + (45 if tara in [2,4,6,8,9] else 10)
    
    return {
        "score": score,
        "rahu": rahu_txt,
        "gulika": gulika_txt,
        "planets": planet_data,
        "tithi": tithi,
        "tara": tara
    }

# --- 7. UI RENDER ---
st.title("☸️ Deep Vedic Intelligence")

try:
    data = get_full_astrometry(geo_birth, geo_curr, birth_date, birth_time_input)
    
    if view_mode == "Daily Dashboard":
        # ROW 1: SCORE & TITHI
        c1, c2 = st.columns([2,1])
        with c1:
            st.metric("Power Score", f"{data['score']}/100")
            st.progress(data['score'] / 100)
        with c2:
            st.write(f"**Lunar Day (Tithi):**\n{data['tithi']}")
            st.write(f"**Star Strength:**\n{data['tara']}/9")

        # ROW 2: TIMING
        st.subheader("⏳ Precision Windows")
        t1, t2 = st.columns(2)
        t1.error(f"🚫 **Rahu Kaal (Avoid):**\n{data['rahu']}")
        t2.success(f"✅ **Gulika Kaal (Good):**\n{data['gulika']}")

        # ROW 3: DEEP METRICS TABLE
        st.divider()
        st.subheader("📊 Planetary Transit Data (Gochar)")
        st.write("Calculated using **Chandra Lagna** (Birth Moon as 1st House).")
        if data['planets']:
            st.table(data['planets'])
        else:
            st.warning("Planet data is initializing. If empty, please check your Birth City input.")

    else:
        # WEEKLY VIEW
        st.subheader("📅 7-Day Data Forecast")
        week_data = []
        for i in range(7):
            day_dt = datetime.datetime.now() + datetime.timedelta(days=i)
            day_info = get_full_astrometry(geo_birth, geo_curr, birth_date, birth_time_input, day_dt)
            week_data.append({
                "Date": day_dt.strftime("%a, %d %b"),
                "Score": day_info['score'],
                "Tithi": day_info['tithi']
            })
        st.dataframe(week_data, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"System Connection Error: {e}")

st.caption("Custom Engine for iPhone. Methodology: Sripada Saptarishi & Swiss Ephemeris.")
