import sys
import types

# --- 1. CRITICAL PYTHON 3.13 POLYFILL (Must stay at top) ---
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
st.sidebar.header("🌍 Birth & Current Data")
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
    
    # Setup Times
    birth_time = Time(f"{b_time.strftime('%H:%M')} {b_date.strftime('%d/%m/%Y')} {b_tz}", birth_loc)
    # Target time normalized to UTC for calculation consistency
    calc_time = Time(f"{target_date.strftime('%H:%M %d/%m/%Y')} +00:00", curr_loc)

    # A. CHANDRA LAGNA (Moon as Ascendant)
    # Find Moon's sign index at birth (1-12)
    b_moon_sign = Calculate.PlanetSignName(PlanetName.Moon, birth_time).value__
    
    planets = [
        PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury,
        PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu
    ]
    
    planet_data = []
    houses_occupied = []

    for p in planets:
        cur_sign = Calculate.PlanetSignName(p, calc_time).value__
        # Relative House Logic: (Current - BirthMoon + 12) % 12 + 1
        rel_house = (cur_sign - b_moon_sign + 12) % 12 + 1
        houses_occupied.append(rel_house)
        
        planet_data.append({
            "Planet": p.name,
            "House": f"House {rel_house}",
            "Sign": Calculate.PlanetSignName(p, calc_time).name,
            "Transit": "Direct" if p.name not in ["Rahu", "Ketu"] else "Retrograde"
        })

    # B. LIFE PILLAR LOGIC
    # Mapping specific houses to pillars based on Chandra Lagna
    pillars = {
        "Work": "Actionable" if any(h in [1, 10, 11] for h in houses_occupied[:3]) else "Stable",
        "Wealth": "Growth" if any(h in [2, 5, 9, 11] for h in houses_occupied[4:6]) else "Routine",
        "Health": "High Energy" if any(h in [1, 5, 9] for h in houses_occupied) else "Conserve",
        "Relations": "Social" if any(h in [3, 7, 11] for h in houses_occupied) else "Neutral"
    }

    # C. PRECISION TIMING
    rahu = str(PanchangaCalculator.GetRahuKaalRange(calc_time))
    gulika = str(PanchangaCalculator.GetGulikaKaalRange(calc_time))
    
    return {"metrics": planet_data, "pillars": pillars, "rahu": rahu, "gulika": gulika, "date": target_date}

# --- 5. UI RENDERING ---
st.title("☸️ Your Cosmic Intelligence")

try:
    if nav_mode == "Daily Dashboard":
        data = get_vibe_engine(datetime.datetime.now())
        
        # Pillars Row
        st.subheader("🔮 Life Pillars")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💼 Work", data['pillars']['Work'])
        c2.metric("💰 Wealth", data['pillars']['Wealth'])
        c3.metric("🧘 Health", data['pillars']['Health'])
        c4.metric("❤️ Relationships", data['pillars']['Relations'])

        # Deep Metrics Table
        st.subheader("📊 Deep Metrics (Chandra Lagna)")
        st.dataframe(pd.DataFrame(data['metrics']), use_container_width=True)

        # Timing
        st.divider()
        t1, t2 = st.columns(2)
        with t1:
            st.error(f"🚫 **Rahu Kaal:** {data['rahu']}")
        with t2:
            st.success(f"✅ **Gulika Kaal:** {data['gulika']}")

    else:
        st.subheader("📅 7-Day Weekly Forecast")
        week_data = []
        for i in range(7):
            day = datetime.datetime.now() + datetime.timedelta(days=i)
            d = get_vibe_engine(day)
            week_data.append({
                "Date": d['date'].strftime("%a, %b %d"),
                "Work": d['pillars']['Work'],
                "Wealth": d['pillars']['Wealth'],
                "Health": d['pillars']['Health']
            })
        st.table(pd.DataFrame(week_data))

except Exception as e:
    st.error(f"Engine Alignment Error: {e}")
    st.info("Ensure coordinates and timezones are in the correct format.")

st.caption("Custom Engine built for Python 3.13 | VedAstro API 2024.x")
