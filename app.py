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
st.set_page_config(page_title="Vedic Daily", page_icon="☸️", layout="wide")

# --- 4. DATA FETCHERS ---
@st.cache_data
def get_geo_details(city_name):
    try:
        results = GeoLocation.GetGeoLocation(city_name)
        return results[0] if results else None
    except:
        return None

def get_safe_attr(obj, attr_name, default="+00:00"):
    try:
        if hasattr(obj, attr_name): return str(getattr(obj, attr_name))
        if hasattr(obj, '_data') and attr_name in obj._data: return str(obj._data[attr_name])
    except: pass
    return default

# --- 5. SIDEBAR ---
st.sidebar.header("🕹️ Controls")
view_mode = st.sidebar.radio("View", ["Daily Dashboard", "Weekly Outlook"])

st.sidebar.divider()
st.sidebar.header("📍 Locations")
curr_city = st.sidebar.text_input("Current City", "London")
geo_curr = get_geo_details(curr_city) or GeoLocation("London", -0.1278, 51.5074)

birth_city = st.sidebar.text_input("Birth City", "Mumbai")
geo_birth = get_geo_details(birth_city) or GeoLocation("Mumbai", 72.8777, 19.0760)

st.sidebar.divider()
st.sidebar.header("👶 Birth Data")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))

# --- 6. CORE LOGIC ---
def get_engine_data(g_birth, g_curr, b_date, b_time_in, target_dt=None):
    if target_dt is None: target_dt = datetime.datetime.now()
    
    # Setup Times
    tz_b = get_safe_attr(g_birth, 'TimezoneStr', '+05:30')
    tz_c = get_safe_attr(g_curr, 'TimezoneStr', '+00:00')
    b_time = Time(f"{b_time_in.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {tz_b}", g_birth)
    c_time = Time(target_dt.strftime("%H:%M %d/%m/%Y ") + tz_c, g_curr)
    
    # 1. Timing
    try:
        rahu = PanchangaCalculator.GetRahuKaalRange(c_time)
        rahu_txt = f"{rahu.Start.GetFormattedTime()} - {rahu.End.GetFormattedTime()}"
        gulika = PanchangaCalculator.GetGulikaKaalRange(c_time)
        gulika_txt = f"{gulika.Start.GetFormattedTime()} - {gulika.End.GetFormattedTime()}"
    except:
        rahu_txt = gulika_txt = "Calculating..."

    # 2. Score & Tithi
    try:
        tara_val = int(PanchangaCalculator.GetTaraBala(b_time, c_time).value__)
        tithi = str(PanchangaCalculator.GetTithi(c_time).TithiName.name)
    except:
        tara_val, tithi = 1, "Unknown"

    # 3. Planets & Pillars
    planets_list = []
    pillars = {"Work": "Stable", "Wealth": "Neutral", "Health": "Good", "Relations": "Average"}
    
    try:
        # Get Sign Numbers directly
        b_moon_sign = int(Calculate.PlanetTransitSign(PlanetName.Moon, b_time).GetSignName().value__)
        
        plist = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
                 PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
        
        for p in plist:
            s_obj = Calculate.PlanetTransitSign(p, c_time).GetSignName()
            s_num = int(s_obj.value__)
            # House Math
            h_num = (s_num - b_moon_sign + 1)
            if h_num <= 0: h_num += 12
            
            planets_list.append({"Planet": str(p), "House": h_num, "Sign": str(s_obj.name)})
            
            # Update Pillars
            if str(p) == "Moon":
                if h_num in [2, 11]: pillars["Wealth"] = "💹 High Potential"
                if h_num in [10, 6]: pillars["Work"] = "🚀 Peak Focus"
                if h_num == 7: pillars["Relations"] = "❤️ Harmonic"
            if str(p) == "Mars" and h_num in [6, 8, 12]:
                pillars["Health"] = "⚠️ Low Energy"
    except:
        pass

    score = 40 + (45 if tara_val in [2,4,6,8,9] else 10)
    return {"score": score, "rahu": rahu_txt, "gulika": gulika_txt, "planets": planets_list, "pillars": pillars, "tara": tara_val, "tithi": tithi}

# --- 7. UI RENDER ---
st.title("☸️ Vedic Intelligence Engine")

try:
    data = get_engine_data(geo_birth, geo_curr, birth_date, birth_time_input)

    if view_mode == "Daily Dashboard":
        # Score
        st.metric("Power Score", f"{data['score']}/100")
        st.progress(data['score'] / 100)

        # Timing
        c1, c2 = st.columns(2)
        c1.error(f"🚫 **Rahu Kaal:**\n{data['rahu']}")
        c2.success(f"✅ **Gulika Kaal:**\n{data['gulika']}")

        # Pillars
        st.divider()
        st.subheader("🔮 Life Pillars")
        p1, p2, p3, p4 = st.columns(4)
        p1.info(f"💼 **Work**\n\n{data['pillars']['Work']}")
        p2.info(f"💰 **Wealth**\n\n{data['pillars']['Wealth']}")
        p3.info(f"🧘 **Health**\n\n{data['pillars']['Health']}")
        p4.info(f"❤️ **Relations**\n\n{data['pillars']['Relations']}")

        # Planet Table
        st.divider()
        st.subheader("📊 Deep Planetary Transits")
        if data['planets']:
            st.table(data['planets'])
        else:
            st.warning("⚠️ Data Syncing: Please ensure both cities are set in the sidebar.")

    else:
        st.subheader("📅 Weekly Forecast")
        week_list = []
        for i in range(7):
            dt = datetime.datetime.now() + datetime.timedelta(days=i)
            d = get_engine_data(geo_birth, geo_curr, birth_date, birth_time_input, dt)
            week_list.append({"Date": dt.strftime("%a %d"), "Score": d['score'], "Tithi": d['tithi']})
        st.dataframe(week_list, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Waiting for engine... {e}")

st.caption("Data provided via VedAstro & Chandra Lagna calculations.")
