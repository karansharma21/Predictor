
    # --- USER STORY 4: Dynamic Transits ---

    # --- START OF TRANSIT AUDIT SNIPPET ---
    # Ensure these variables are defined in your main script: 
    # birth_time (Natal Time object), geo (GeoLocation object)
   


import json
from datetime import datetime
from vedastro import *

def setup_vedastro_time(date_str, time_str, offset_str, lat, lon, city):
    d, t, o = str(date_str).strip(), str(time_str).strip(), str(offset_str).strip()
    if "-" in d:
        p = d.split("-")
        d = f"{p[2]}/{p[1]}/{p[0]}"
    if len(o) == 5 and (o.startswith('+') or o.startswith('-')):
        o = f"{o[0]}0{o[1:]}"
    return Time(f"{t} {d} {o}", GeoLocation(str(city), float(lat), float(lon)))

def run_transit_audit():
    with open("config.json", "r") as f:
        config = json.load(f)

    skipped_calculations = []
    Calculate.Ayanamsa = Ayanamsa.Lahiri
    zodiac = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

    # 1. Initialize Times
    birth_time = setup_vedastro_time(
        config["birth_details"]["date_of_birth"], config["birth_details"]["time_of_birth"],
        config["birth_details"]["timezone_offset"], config["birth_details"]["location"]["latitude"],
        config["birth_details"]["location"]["longitude"], config["birth_details"]["location"]["city"]
    )

    query_time = setup_vedastro_time(
        config["current_details"]["query_date"], config["current_details"]["query_time"],
        config["current_details"]["timezone_offset"], config["current_details"]["location"]["latitude"],
        config["current_details"]["location"]["longitude"], config["current_details"]["location"]["city"]
    )

    results = {}
    try:
        # 2. Get Natal Reference (Using the most compatible method)
        # We know LagnaSignName works because it succeeded in your previous logs
        lagna_obj = Calculate.LagnaSignName(birth_time)
        lagna_sign = str(lagna_obj)
        l_idx = zodiac.index(lagna_sign)

        # Get Natal Moon Sign
        moon_data = Calculate.AllPlanetData(PlanetName.Moon, birth_time)
        # Accessing the sign name from the dictionary
        moon_sign = str(moon_data.get("PlanetRasiD1Sign", {}).get("Name", "Aries"))
        m_idx = zodiac.index(moon_sign)

        # 3. Transits (TR-001 & TR-002)
        tr_001, tr_002 = {}, {}
        target_planets = [PlanetName.Saturn, PlanetName.Jupiter, PlanetName.Rahu, PlanetName.Ketu]

        for p in target_planets:
            p_data = Calculate.AllPlanetData(p, query_time)
            
            # Extract Sign Name safely
            # Note: Checking multiple common keys used by different VedAstro versions
            p_sign = p_data.get("PlanetRasiD1Sign", {}).get("Name")
            if not p_sign:
                p_sign = p_data.get("Sign", {}).get("Name")
            
            if not p_sign:
                skipped_calculations.append({"UID": str(p), "Reason": "Dictionary keys not found in AllPlanetData"})
                continue

            p_idx = zodiac.index(str(p_sign))
            p_name = str(p).split('.')[-1]
            
            tr_001[p_name] = str(p_sign)
            tr_002[f"{p_name}_House"] = (p_idx - l_idx) % 12 + 1

        # 4. Sade Sati (TR-003)
        sat_data_now = Calculate.AllPlanetData(PlanetName.Saturn, query_time)
        sat_sign_now = str(sat_data_now.get("PlanetRasiD1Sign", {}).get("Name", "Aries"))
        s_idx = zodiac.index(sat_sign_now)
        
        rel = (s_idx - m_idx) % 12
        p_map = {11: "Rising", 0: "Peak", 1: "Setting"}

        results = {
            "Metadata": {"Lagna": lagna_sign, "Moon": moon_sign},
            "TR-001_Transit_Signs": tr_001,
            "TR-002_Relative_Houses": tr_002,
            "TR-003_Sade_Sati": {"Is_Active": rel in p_map, "Phase": p_map.get(rel, "None")}
        }
    except Exception as e:
        skipped_calculations.append({"UID": "Full_Audit_Fail", "Reason": f"{type(e).__name__}: {str(e)}"})

    return {
        "Audit_Log": {
            "Timestamp": str(datetime.now()),
            "Skipped_Calculations": skipped_calculations
        },
        "Transit_Results": results
    }

if __name__ == "__main__":
    # 1. Run the audit
    final_payload = run_transit_audit()
    
    # 2. Define the output filename
    output_file = "3.transit_payload.json"
    
    # 3. Write to JSON file with clean indentation
    with open(output_file, "w") as outfile:
        json.dump(final_payload, outfile, indent=4)
    
    # 4. Print to console for immediate verification
    print(f"--- Audit Complete ---")
    print(f"File Saved: {output_file}")
    

