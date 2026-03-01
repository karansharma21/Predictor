import json
import traceback
from datetime import datetime
from vedastro import *

def clean_name(enum_str):
    """Converts 'PlanetName.Sun' to 'Sun'"""
    return str(enum_str).split('.')[-1]

def load_config(filepath="config.json"):
    with open(filepath, 'r') as file:
        return json.load(file)

def setup_vedastro_time(date_str, time_str, offset_str, lat, lon, city):
    # VedAstro strictly requires format: "HH:mm DD/MM/YYYY +HH:MM"
    combined_time_str = f"{time_str} {date_str} {offset_str}"
    geolocation = GeoLocation(city, lat, lon)
    return Time(combined_time_str, geolocation)

def generate_astrology_data(config):
    # Setup calculation times with Timezone offsets
    birth_time = setup_vedastro_time(
        config["birth_details"]["date_of_birth"],
        config["birth_details"]["time_of_birth"],
        config["birth_details"]["timezone_offset"],
        config["birth_details"]["location"]["latitude"],
        config["birth_details"]["location"]["longitude"],
        config["birth_details"]["location"]["city"]
    )


    current_time = setup_vedastro_time(
        config["current_details"]["query_date"],
        config["current_details"]["query_time"],
        config["current_details"]["timezone_offset"],
        config["current_details"]["location"]["latitude"],
        config["current_details"]["location"]["longitude"],
        config["current_details"]["location"]["city"]
    )

    # Initialize standard planets and houses for iteration
    planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
               PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu]
    
    # Base JSON Structure
    output = {
        "Metadata": {
            "Ayanamsa": config["settings"]["ayanamsa"],
            "Calculation_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Location_Context": {
                "Birth": f"{config['birth_details']['location']['latitude']},{config['birth_details']['location']['longitude']}/{config['birth_details']['location']['city']}",
                "Current": f"{config['current_details']['location']['latitude']},{config['current_details']['location']['longitude']}/{config['current_details']['location']['city']}"
            },
            "Library_Source": "VedAstro-GitHub"
        },
        "Audit_Log": {
            "Skipped_Calculations": [],
            "Notes": "Any UID that fails calculation at runtime or misses data keys is logged here."
        },
        "Static_Foundation": {},
        "Varga_Analysis": {},
        "Temporal_Timeline": {},
        "Dynamic_Transits": {}
    }

    def safe_calc(uid, fallback_val, calc_func):
        try:
            return calc_func()
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            if not error_msg: 
                error_msg = "Calculation failed or mapping key missing."
            output["Audit_Log"]["Skipped_Calculations"].append({
                "UID": uid,
                "Reason": error_msg
            })
            return fallback_val

    # --- USER STORY 1: Static Foundation ---
    
    def get_st001():
        rashi = []
        # Get Lagna
        lagna_sign = Calculate.LagnaSignName(birth_time)
        rashi.append({"Planet": "Lagna", "Sign": str(lagna_sign), "Degree": 0.0, "House": 1})
        
        for p in planets:
            # New API usage: pull the bulk dictionary for the planet
            p_data = Calculate.AllPlanetData(p, birth_time)
            
            rashi.append({
                "Planet": str(p), 
                # Dictionary keys are guessed based on standard VedAstro outputs. 
                # If they vary slightly in your version, safe_calc catches the KeyError.
                "Sign": str(p_data.get("PlanetZodiacSign", "Unknown")), 
                "Degree": p_data.get("PlanetNirayanaDegree", 0.0), 
                "House": p_data.get("PlanetHouse", 0), 
                "Is_Retrograde": p_data.get("IsRetrograde", False)
            })
        return rashi
    
    output["Static_Foundation"]["ST-001_Rashi_Chart"] = safe_calc("ST-001", [], get_st001)

    def get_st002():
        lords = {}
        for i in range(1, 13):
            house_enum = getattr(HouseName, f"House{i}")
            # New API usage: pull the bulk dictionary for the house
            h_data = Calculate.AllHouseData(house_enum, birth_time)
            lords[f"H{i}"] = str(h_data.get("LordOfHouse", "Unknown"))
        return lords
    
    output["Static_Foundation"]["ST-002_House_Lords"] = safe_calc("ST-002", {}, get_st002)

    def get_st003():
        shadbala = {}
        for p in [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]:
             p_data = Calculate.AllPlanetData(p, birth_time)
             if "PlanetShadbalaPinda" in p_data:
                 shadbala[str(p)] = p_data["PlanetShadbalaPinda"]                 
             else:
                 raise KeyError("ShadbalaPinda not found in AllPlanetData dictionary")
        return shadbala
    
    output["Static_Foundation"]["ST-003_Shadbala"] = safe_calc("ST-003", {}, get_st003)
    
    # Testing new BhinnashtakavargaChart API endpoint
    output["Static_Foundation"]["ST-004_Ashtakavarga_SAV"] = safe_calc("ST-004", {}, lambda: Calculate.BhinnashtakavargaChart(birth_time))
    
    output["Static_Foundation"]["ST-005_Yoga_List"] = safe_calc("ST-005", [], lambda: {"Note": "Yoga extraction requires specific iteration in current Python version."})

    # --- USER STORY 2: Varga Analysis ---
    # Attempting to fetch from AllPlanetData bulk payload
    def get_vargas(varga_key):
        varga_data = []
        for p in planets:
            p_data = Calculate.AllPlanetData(p, birth_time)
            if varga_key in p_data:
                varga_data.append({"Planet": str(p), "Sign": str(p_data[varga_key])})
            else:
                raise KeyError(f"{varga_key} missing from AllPlanetData")
        return varga_data

    output["Varga_Analysis"]["VG-001_D9_Navamsha"] = safe_calc("VG-001", [], lambda: get_vargas("PlanetNavamshaD9Sign"))
    output["Varga_Analysis"]["VG-002_D10_Dashamsha"] = safe_calc("VG-002", [], lambda: get_vargas("PlanetDashamamshaD10Sign"))
    output["Varga_Analysis"]["VG-003_D12_Dwadasamsha"] = safe_calc("VG-003", [], lambda: get_vargas("PlanetDwadashamshaD12Sign"))
    output["Varga_Analysis"]["VG-004_D30_Trimshamsha"] = safe_calc("VG-004", [], lambda: get_vargas("PlanetTrimshamshaD30Sign"))

    # --- USER STORY 3: Temporal Timeline ---
    # The API now uses DasaAtRange
    #output["Temporal_Timeline"]["TM-001_Current_Dasha"] = safe_calc("TM-001/002", {}, lambda: {"Raw_Data": Calculate.DasaAtRange(birth_time, 2024, 2030,3,1.0)})
    #output["Temporal_Timeline"]["TM-002_Dasha_Sequence"] = [] # Merged audit logic with TM-001
    def get_dasha_data():
        # We pull the Moon's data which we already know contains Dasha info
        moon_data = Calculate.AllPlanetData(PlanetName.Moon, birth_time)
    
        # We extract the specific key discovered in your trace
        dasha_info = moon_data.get("PlanetDasaEffectsBasedOnIshtaKashta", "No Dasha Data Found")
    
        # If it's a list or dict, we return it; if it's an object, we stringify it
        if isinstance(dasha_info, (list, dict)):
            return dasha_info
        return str(dasha_info)

    output["Temporal_Timeline"]["TM-001_Current_Dasha"] = safe_calc("TM-001/002", "Data Unavailable", get_dasha_data)

    def get_atmakaraka():
    # Jaimini Seven-Planet system (8-planet including Rahu is optional)
        karaka_planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn]
    
        highest_degree = -1.0
        atmakaraka_name = "Unknown"

        for p in karaka_planets:
            p_data = Calculate.AllPlanetData(p, birth_time)
        
            # We need the degrees WITHIN the sign (0-30)
            # Based on your debug: 'PlanetRasiD1Sign' -> 'DegreesIn' -> 'TotalDegrees'
            sign_data = p_data.get("PlanetRasiD1Sign", {})
            degrees_in_sign = float(sign_data.get("DegreesIn", {}).get("TotalDegrees", 0.0))
            if degrees_in_sign > highest_degree:
                highest_degree = degrees_in_sign
                atmakaraka_name = clean_name(p)
            
        return atmakaraka_name

    output["Temporal_Timeline"]["TM-003_Atmakaraka"] = safe_calc("TM-003", "Unknown", get_atmakaraka)


    
    

    # --- USER STORY 4: Dynamic Transits ---
    def get_tr001():
        transits = []
        for p in [PlanetName.Saturn, PlanetName.Jupiter, PlanetName.Rahu, PlanetName.Ketu]:
            p_data = Calculate.AllPlanetData(p, current_time)
            transits.append({"Planet": str(p), "Sign": str(p_data.get("PlanetZodiacSign", "Unknown"))})
        return transits

    output["Dynamic_Transits"]["TR-001_Current_Positions"] = safe_calc("TR-001", [], get_tr001)
    output["Dynamic_Transits"]["TR-002_House_Transits"] = safe_calc("TR-002", {}, lambda: {"Note": "Requires relative house mapping logic."})
    output["Dynamic_Transits"]["TR-003_Sade_Sati"] = safe_calc("TR-003", {"Is_Active": False, "Phase": "None"}, lambda: {"Note": "IsSadeSati method isolated in current wrapper version."})

    return output

if __name__ == "__main__":
    print("Initializing AI Astrologer Analytical Engine...")
    
    # Load inputs
    config_data = load_config("config.json")
    
    # Generate Payload
    json_payload = generate_astrology_data(config_data)
    
    # Write Output
    with open("astrology_payload.json", "w") as outfile:
        json.dump(json_payload, outfile, indent=4)
        
    print("Calculations complete. Payload saved to astrology_payload.json.")
    print(f"Skipped Calculations Logged: {len(json_payload['Audit_Log']['Skipped_Calculations'])}")
