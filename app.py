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

# --- 4. SAFE EXTRACTORS ---
def get_safe_attr(obj, attr_name, default="Unknown"):
    try:
        if hasattr(obj, attr_name): return str(getattr(obj, attr_name))
        if hasattr(obj, '_data') and attr_name in obj._data: return str(obj._data[attr_name])
    except: pass
    return default

@st.cache_data
def get_geo_details(city_name):
    try:
        results = GeoLocation.GetGeoLocation(city_name)
        return results[0] if results else None
    except:
        return None

# --- 5. SIDEBAR ---
st.sidebar.header("🕹️ Display")
view_mode = st.sidebar.radio("View", ["Daily Dashboard", "Weekly Outlook"])

st.sidebar.divider()
st.sidebar.header("📍 Locations")
curr_city_input = st.sidebar.text_input("Current City (Today)", "London")
geo_curr = get_geo_details(curr_city_input) or GeoLocation("London", -0.1278, 51.5074)

birth_city_input = st.sidebar.text_input("Birth City", "Mumbai")
geo_birth = get_geo_details(birth_city_input) or GeoLocation("Mumbai", 72.8777, 19.0760)

st.sidebar.divider()
st.sidebar.header("👶 Birth Details")
birth_date = st.sidebar.date_input("Birth Date", datetime.date(1990, 5, 15))
birth_time_input = st.sidebar.time_input("Birth Time", datetime.time(10, 30))

if st.sidebar.button("♻️ Force Sync Engine"):
    st.cache_data.clear()
    st.rerun()

# --- 6. ENGINE CORE ---
def get_cosmic_data(g_birth, g_curr, b_date, b_time_in, target_dt=None):
    if target_dt is None: target_dt = datetime.datetime.now()
    
    # 1. Standardize Time
    tz_b = get_safe_attr(g_birth, 'TimezoneStr', '+05:30')
    tz_c = get_safe_attr(g_curr, 'TimezoneStr', '+00:00')
    
    b_time = Time(f"{b_time_in.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {tz_b}", g_birth)
    c_time = Time(target_dt.strftime("%H:%M %d/%m/%Y ") + tz_c, g_curr)
    
    # 2. Timing (Panchanga)
    try:
        rahu = PanchangaCalculator.GetRahuKaalRange(c_time)
        rahu_txt = f"{rahu.Start.GetFormattedTime()} - {rahu.End.GetFormattedTime()}"
        gulika = PanchangaCalculator.GetGulikaKaalRange(c_time)
        gulika_txt = f"{gulika.Start.GetFormattedTime()} - {gulika.End.GetFormattedTime()}"
    except:
        rahu_txt = "Calculating..."
        gulika_txt = "Calculating..."

    # 3. Planet Logic using Chandra Lagna (Moon Sign System)
    metrics = []
    cats = {"Work": "Stable", "Wealth": "Stable", "Health": "Good", "Relations": "Average"}
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
    try:
        # Get Birth Moon Sign Number (1-12)
        birth_moon_sign = int(Calculate.PlanetTransitSign(PlanetName.Moon, b_time).GetSignName().value__)
        
        for p in planets:
            # Get Current Planet Sign Number
            current_sign_obj = Calculate.PlanetTransitSign(p, c_time)
            curr_sign_num = int(current_sign_obj.GetSignName().value__)
            curr_sign_name = str(current_sign_obj.GetSignName().name)
            
            # Calculate House: (Current Sign - Birth Moon Sign + 1)
            h_num = (curr_sign_num - birth_moon_sign + 1)
            if h_num <= 0: h_num += 12
            
            metrics.append({"Planet": str(p), "House": f"House {h_num}", "Sign": curr_sign_name})
            
            # Categories based on derived house
            if str(p) == "Moon":
                if h_num in [2, 11]: cats["Wealth"] = "🚀 High Gain"
                if h_num in [6, 10]: cats["Work"] = "💼 Career Focus"
                if h_num == 7: cats["Relations"] = "❤️ Harmony"
            if str(p) == "Mars" and h_num in [6, 8, 12]:
                cats["Health"] = "⚠️ Low Vitality"
    except:
        pass

    # 4. Score Logic
    try:
        tara = int(PanchangaCalculator.GetTaraBala(b_time, c_time).value__)
        tithi = str(PanchangaCalculator.GetTithi(c_time).TithiName.name)
    except:
        tara, tithi = 1, "Neutral"

    score = 40 + (45 if tara in [2,4,6,8,9] else 10)
    return {"score": score, "rahu": rahu_txt, "gulika": gulika_txt, "metrics": metrics, "tara": tara, "tithi": tithi, "cats": cats}

# --- 7. UI DISPLAY ---
st.title("☸️ Vedic Daily Engine")

try:
    data = get_cosmic_data(geo_birth, geo_curr, birth_date, birth_time_input)
    
    if view_mode == "Daily Dashboard":
        st.metric("Power Score", f"{data['score']}/100")
        st.progress(data['score'] / 100)

        col1, col2 = st.columns(2)
        col1.error(f"🚫 **Rahu Kaal:**\n\n{data['rahu']}")
        col2.success(f"✅ **Gulika Kaal:**\n\n{data['gulika']}")

        st.divider()
        st.subheader("🔮 Life Category Forecast")
        c1, c2, c3, c4 = st.columns(4)
        c1.info(f"💼 **Work**\n\n{data['cats']['Work']}")
        c2.info(f"💰 **Wealth**\n\n{data['cats']['Wealth']}")
        c3.info(f"🧘 **Health**\n\n{data['cats']['Health']}")
        c4.info(f"❤️ **Relations**\n\n{data['cats']['Relations']}")

        st.divider()
        st.subheader("📊 Deep Astrological Metrics")
        if data['metrics']:
            st.table(data['metrics'])
        else:
            st.warning("Engine is syncing signs. Try changing your Birth City slightly to force a refresh.")

    else:
        st.subheader("📅 7-Day Outlook")
        forecasts = []
        for i in range(7):
            f_dt = datetime.datetime.now() + datetime.timedelta(days=i)
            f_d = get_cosmic_data(geo_birth, geo_curr, birth_date, birth_time_input, f_dt)
            forecasts.append({"Day": f_dt.strftime("%a, %d %b"), "Score": f_d['score'], "Phase": f_d['tithi']})
        st.table(forecasts)

except Exception as e:
    st.error(f"Engine connecting... {e}")

st.caption("Customized for iPhone Home Screen. Powered by VedAstro.")
