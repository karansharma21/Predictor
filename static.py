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
    
    
    def get_st001(planet_enum):
        """The bulletproof logic confirmed by our diagnostic"""
        raw_data = Calculate.AllPlanetData(planet_enum, birth_time)
    
        # Extract Sign & Degree
        rasi_data = raw_data.get("PlanetRasiD1Sign", {})
        sign_name = rasi_data.get("Name", "Unknown")
        total_degrees = rasi_data.get("DegreesIn", {}).get("TotalDegrees", 0.0)
    
        # Extract & Clean House
        raw_house = str(raw_data.get("HousePlanetOccupiesBasedOnSign", "0"))
        clean_house = raw_house.replace("House", "").strip()

        try:
            house_num = int(float(clean_house))
        except:
            house_num = 0

        return {
            "Sign": str(sign_name),
            "Degree": round(float(total_degrees), 2),
            "House": house_num
        }

    # --- THE LOOP ---
    # Defining the list explicitly to avoid any PlanetName namespace issues
    target_planets = [
        PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, 
        PlanetName.Mercury, PlanetName.Jupiter, PlanetName.Venus, 
        PlanetName.Saturn, PlanetName.Rahu, PlanetName.Ketu
    ]

    for p in target_planets:
        p_name = str(p).split('.')[-1] # Cleaner than clean_name if that was bugging
    
        # We use lambda p=p to 'freeze' the planet in the current loop iteration
        output["Static_Foundation"][f"ST-001_{p_name}"] = safe_calc(f"ST-001_{p_name}", {"Sign": "Unknown", "Degree": 0.0, "House": 0}, lambda p=p: get_st001(p))




    
    
    
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
    
    def get_st005():
        # 1. Extract the raw dictionary directly from the API call
        n_yoga_data = Calculate.NithyaYoga(birth_time)

        # 2. Access using Dictionary Brackets (Safe for <class 'dict'>)
        # We use .get() to ensure that even if a key is missing, it doesn't crash
        yoga_name = n_yoga_data.get("Name", "Unknown")
        yoga_desc = n_yoga_data.get("Description", "No description available.")

        # 3. Build the final output block
        return {
            "Location": str(birth_time.geolocation.location_name),
            "Time": str(birth_time.url_time_string()),
            "Nithya_Yoga": {
                "Name": str(yoga_name),
                "Description": str(yoga_desc)
            }
        }

    # Update the assignment in your Static_Foundation block
    output["Static_Foundation"]["ST-005_Nithya_Yoga"] = safe_calc("ST-005", {}, get_st005)


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



    return output
if __name__ == "__main__":
    print("Initializing AI Astrologer Analytical Engine...")
    
    # Load inputs
    config_data = load_config("config.json")
    
    # Generate Payload
    json_payload = generate_astrology_data(config_data)
    
    # Write Output
    with open("1.birth_payload.json", "w") as outfile:
        json.dump(json_payload, outfile, indent=4)
        
    print("Calculations complete. Payload saved to astrology_payload.json.")
    print(f"Skipped Calculations Logged: {len(json_payload['Audit_Log']['Skipped_Calculations'])}")

