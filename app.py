import streamlit as st
from vedastro import *
import datetime

# --- 1. INITIALIZE ENGINE ---
# This is often the missing link. We set a free key to "wake up" the server.
try:
    Calculate.SetAPIKey("FreeAPIUser")
except:
    pass

# --- 2. CONFIG ---
st.set_page_config(page_title="Vedic Daily", page_icon="☸️", layout="wide")

# --- 3. PERSISTENT GEO-FETCH ---
@st.cache_data
def get_geo(city):
    try:
        # We try to get the first valid result
        res = GeoLocation.GetGeoLocation(city)
        return res[0] if res else None
    except:
        return None

# --- 4. SIDEBAR INPUTS ---
st.sidebar.header("📍 Settings")
curr_city_name = st.sidebar.text_input("Current City", "London")
birth_city_name = st.sidebar.text_input("Birth City", "Mumbai")

# Resolve Geolocation
geo_curr = get_geo(curr_city_name) or GeoLocation("London", -0.1278, 51.5074)
geo_birth = get_geo(birth_city_name) or GeoLocation("Mumbai", 72.8777, 19.0760)

st.sidebar.divider()
st.sidebar.header("👶 Birth Details")
b_date = st.sidebar.date_input("Date", datetime.date(1990, 5, 15))
b_time = st.sidebar.time_input("Time", datetime.time(10, 30))

# --- 5. THE CALCULATION ENGINE ---
def fetch_all_data(g_birth, g_curr, b_d, b_t):
    # Construct Time Objects
    # We use a hardcoded offset fallback if the geo-object is being stubborn
    birth_str = f"{b_t.strftime('%H:%M')} {b_d.strftime('%d/%m/%Y')} +05:30"
    now_str = datetime.datetime.now().strftime("%H:%M %d/%m/%Y +00:00")
    
    time_birth = Time(birth_str, g_birth)
    time_now = Time(now_str, g_curr)
    
    output = {
        "score": 50,
        "pillars": {"Work": "Stable", "Wealth": "Neutral", "Health": "Good", "Relations": "Average"},
        "planets": [],
        "times": {"Rahu": "Syncing...", "Gulika": "Syncing..."}
    }

    try:
        # A. Panchanga (Rahu/Gulika)
        rahu = PanchangaCalculator.GetRahuKaalRange(time_now)
        gulika = PanchangaCalculator.GetGulikaKaalRange(time_now)
        output["times"]["Rahu"] = f"{rahu.Start.GetFormattedTime()} - {rahu.End.GetFormattedTime()}"
        output["times"]["Gulika"] = f"{gulika.Start.GetFormattedTime()} - {gulika.End.GetFormattedTime()}"
        
        # B. Score (Tara Bala)
        tara = int(PanchangaCalculator.GetTaraBala(time_birth, time_now).value__)
        output["score"] = 40 + (45 if tara in [2,4,6,8,9] else 10)

        # C. Planets & Pillars (The Data Table)
        # We manually count the houses from the Birth Moon Sign
        birth_moon_sign = int(Calculate.PlanetTransitSign(PlanetName.Moon, time_birth).GetSignName().value__)
        
        plist = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
                 PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
        
        for p in plist:
            curr_sign = Calculate.PlanetTransitSign(p, time_now).GetSignName()
            s_num = int(curr_sign.value__)
            
            # Vedic House Math: (Current Sign - Birth Sign) + 1
            h_num = (s_num - birth_moon_sign + 1)
            if h_num <= 0: h_num += 12
            
            output["planets"].append({
                "Planet": str(p),
                "House": h_num,
                "Zodiac": str(curr_sign.name)
            })

            # D. Pillars Logic
            if str(p) == "Moon":
                if h_num in [2, 11]: output["pillars"]["Wealth"] = "💹 High Potential"
                if h_num in [10, 6]: output["pillars"]["Work"] = "💼 Focus High"
                if h_num == 7: output["pillars"]["Relations"] = "❤️ Harmony"
            if str(p) == "Mars" and h_num in [6, 8, 12]:
                output["pillars"]["Health"] = "⚠️ Low Energy"
                
    except Exception as e:
        st.sidebar.error(f"Sync Error: {str(e)[:50]}")
        
    return output

# --- 6. UI RENDERING ---
st.header("☸️ Your Cosmic Live Feed")

data = fetch_all_data(geo_birth, geo_curr, b_date, b_time)

# Row 1: The Main Meter
st.metric("Power Score", f"{data['score']}/100")
st.progress(data['score'] / 100)

# Row 2: Precision Timing
c1, c2 = st.columns(2)
c1.error(f"🚫 **Rahu Kaal (Avoid)**\n\n{data['times']['Rahu']}")
c2.success(f"✅ **Gulika Kaal (Good)**\n\n{data['times']['Gulika']}")

# Row 3: The 4 Pillars (Restored)
st.divider()
st.subheader("🔮 Life Category Breakdown")
p1, p2, p3, p4 = st.columns(4)
p1.info(f"💼 **Work**\n\n{data['pillars']['Work']}")
p2.info(f"💰 **Wealth**\n\n{data['pillars']['Wealth']}")
p3.info(f"🧘 **Health**\n\n{data['pillars']['Health']}")
p4.info(f"❤️ **Relations**\n\n{data['pillars']['Relations']}")

# Row 4: Deep Data Table
st.divider()
st.subheader("📊 Full Planetary Transit Data")
if data["planets"]:
    st.table(data["planets"])
else:
    st.warning("🔄 Connecting to Vedic Satellite... Ensure your Birth City and Current City are filled in.")

st.caption("Calculation Method: Chandra Lagna (House 1 = Natal Moon)")
