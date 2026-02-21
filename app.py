import sys
import types

# --- 1. CRITICAL PYTHON 3.13 POLYFILL ---
if "pkg_resources" not in sys.modules:
    mock_pkg = types.ModuleType("pkg_resources")
    mock_pkg.declare_namespace = lambda name: None
    mock_pkg.get_distribution = lambda name: types.SimpleNamespace(version="0.0.0")
    mock_pkg.Requirement = lambda x: x
    sys.modules["pkg_resources"] = mock_pkg

import streamlit as st
import datetime
import pandas as pd
from vedastro import *

# --- 2. APP CONFIG ---
st.set_page_config(page_title="Vedic Engine Pro", page_icon="🔱", layout="wide")

# --- 3. SIDEBAR INPUTS ---
st.sidebar.header("🌍 Location & Birth Data")
nav_mode = st.sidebar.radio("View Mode", ["Daily Dashboard", "Weekly Forecast"])

with st.sidebar.expander("Birth Details (Soul Blueprint)", expanded=True):
    b_date = st.sidebar.date_input("Birth Date", datetime.date(1995, 1, 1))
    b_time = st.sidebar.time_input("Birth Time", datetime.time(12, 0))
    b_tz = st.sidebar.text_input("Birth TZ (e.g. +05:30)", "+05:30")
    b_lat = st.sidebar.number_input("Birth Lat", value=28.6139)
    b_lon = st.sidebar.number_input("Birth Lon", value=77.2090)

with st.sidebar.expander("Current Location (Local Muhurta)", expanded=True):
    c_lat = st.sidebar.number_input("Current Lat", value=40.7128)
    c_lon = st.sidebar.number_input("Current Lon", value=-74.0060)

# --- 4. CALCULATION ENGINE ---
def get_vibe_engine(target_date):
    # Setup Locations
    birth_loc = GeoLocation("Birth", b_lon, b_lat)
    curr_loc = GeoLocation("Current", c_lon, c_lat)
    
    # Precise Time Formatting for VedAstro Engine
    birth_time_str = f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}"
    calc_time_str = f"{target_date.strftime('%H:%M %d/%m/%Y')} +00:00"
    
    birth_time = Time(birth_time_str, birth_loc)
    calc_time = Time(calc_time_str, curr_loc)

    # A. CHANDRA LAGNA (Moon as Ascendant)
    # Using .GetSignName() or .Name depending on the specific wrapper version
    b_moon_sign_obj = Calculate.PlanetSign(PlanetName.Moon, birth_time)
    b_moon_sign_value = b_moon_sign_obj.GetSignName().value__ 
    
    planets = [
        PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury,
        PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu
    ]
    
    planet_data = []
    houses_occupied = []

    for p in planets:
        # Get sign for the current transit
        p_sign_obj = Calculate.PlanetSign(p, calc_time)
        cur_sign_val = p_sign_obj.GetSignName().value__
        cur_sign_name = p_sign_obj.GetSignName().name
        
        # Relative House Logic (Chandra Lagna)
        rel_house = (cur_sign_val - b_moon_sign_value + 12) % 12 + 1
        houses_occupied.append(rel_house)
        
        planet_data.append({
            "Planet": p.name,
            "House": f"House {rel_house}",
            "Sign": cur_sign_name,
            "Transit": "Direct" if p.name not in ["Rahu", "Ketu"] else "Retrograde"
        })

    # B. LIFE PILLAR LOGIC
    # Simplified Vedic mapping for UI pillars
    pillars = {
        "Work": "High Action" if any(h in [1, 10, 11] for h in houses_occupied[:3]) else "Steady",
        "Wealth": "Growth" if any(h in [2, 5, 9, 11] for h in houses_occupied[4:6]) else "Stable",
        "Health": "Strong" if any(h in [1, 5, 9] for h in houses_occupied) else "Conserve",
        "Relations": "Social" if any(h in [3, 7, 11] for h in houses_occupied) else "Neutral"
    }

    # C. PRECISION TIMING
    try:
        rahu = str(PanchangaCalculator.GetRahuKaalRange(calc_time))
        gulika = str(PanchangaCalculator.GetGulikaKaalRange(calc_time))
    except:
        rahu, gulika = "Calculation Pending", "Calculation Pending"
    
    return {"metrics": planet_data, "pillars": pillars, "rahu": rahu, "gulika": gulika, "date": target_date}

# --- 5. UI RENDERING ---
st.title("🔱 Your Cosmic Intelligence Engine")

try:
    if nav_mode == "Daily Dashboard":
        data = get_vibe_engine(datetime.datetime.now())
        
        # Life Pillars
        st.subheader("🔮 Life Pillars (Chandra Lagna)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💼 Work", data['pillars']['Work'])
        c2.metric("💰 Wealth", data['pillars']['Wealth'])
        c3.metric("🧘 Health", data['pillars']['Health'])
        c4.metric("❤️ Relationships", data['pillars']['Relations'])

        # Deep Metrics Table
        st.subheader("📊 Full Astronomical Data")
        st.table(pd.DataFrame(data['metrics']))

        # Timing Section
        st.divider()
        t1, t2 = st.columns(2)
        with t1:
            st.error(f"🚫 **Rahu Kaal (Avoid):** {data['rahu']}")
        with t2:
            st.success(f"✅ **Gulika Kaal (Auspicious):** {data['gulika']}")

    else:
        st.subheader("📅 7-Day Weekly Forecast Table")
        week_list = []
        for i in range(7):
            d_target = datetime.datetime.now() + datetime.timedelta(days=i)
            d_res = get_vibe_engine(d_target)
            week_list.append({
                "Date": d_res['date'].strftime("%a, %b %d"),
                "Work": d_res['pillars']['Work'],
                "Wealth": d_res['pillars']['Wealth'],
                "Health": d_res['pillars']['Health'],
                "Rahu Kaal": d_res['rahu']
            })
        st.dataframe(pd.DataFrame(week_list), use_container_width=True)

except Exception as e:
    st.error(f"Engine Alignment Error: {e}")
    st.info("Check if your Birth Timezone is in the format '+05:30' and coordinates are valid numbers.")

st.caption("Custom Engine for Python 3.13 | VedAstro API | Chandra Lagna Methodology")
