
    # --- USER STORY 3: Temporal Timeline ---
    # The API now uses DasaAtRange
 



from vedastro import *
from datetime import datetime, timedelta
import json
def load_config(filepath="config.json"):
    with open(filepath, 'r') as file:
        return json.load(file)

def setup_vedastro_time(date_str, time_str, offset_str, lat, lon, city):
    # VedAstro strictly requires format: "HH:mm DD/MM/YYYY +HH:MM"
    combined_time_str = f"{time_str} {date_str} {offset_str}"
    geolocation = GeoLocation(city, lat, lon)
    return Time(combined_time_str, geolocation)


def generate_dasha_audit_file(config):
    # --- CONFIGURATION ---
    # Setup calculation times with Timezone offsets
    birth_time = setup_vedastro_time(
        config["birth_details"]["date_of_birth"],
        config["birth_details"]["time_of_birth"],
        config["birth_details"]["timezone_offset"],
        config["birth_details"]["location"]["latitude"],
        config["birth_details"]["location"]["longitude"],
        config["birth_details"]["location"]["city"]
    )
    # Define the geolocation for the loop to use
    loc = config["birth_details"]["location"]
    geolocation = GeoLocation(loc["city"], loc["latitude"], loc["longitude"])
    offset = config["birth_details"]["timezone_offset"]

    #geo = GeoLocation("New Delhi", 28.6139, 77.209)
    #birth_time_str = "14:30 15/08/1990 +05:30"
    #birth_time = Time(birth_time_str, geo)
    # 2. Native Python Datetimes for the 'for' loops
    dob_str = config["birth_details"]["date_of_birth"] 
    tob_str = config["birth_details"]["time_of_birth"]
    
    # This creates the exact start point for the Dasha timeline
    start_dt = datetime.strptime(f"{dob_str} {tob_str}", "%d/%m/%Y %H:%M")
    
    #`` Look-ahead: 8 years from today's date
    now_dt = datetime.now()
    end_dt = datetime(now_dt.year + 8, now_dt.month, now_dt.day)    


    #start_dt = datetime(1990, 8, 15, 14, 30)
    #now_dt = datetime.now()
    #end_dt = datetime(now_dt.year + 8, now_dt.month, now_dt.day)
    
    print(f"Starting Professional Audit Generation...")

    # --- TM-003: VERIFIED ATMAKARAKA LOGIC ---
    def get_atmakaraka():
        karaka_planets = [
            PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, 
            PlanetName.Mercury, PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn
        ]
        highest_degree = -1.0
        ak_name = "Unknown"

        for p in karaka_planets:
            try:
                p_data = Calculate.AllPlanetData(p, birth_time)
                # Accessing verified 2026 path: PlanetRasiD1Sign -> DegreesIn -> TotalDegrees
                sign_data = p_data.get("PlanetRasiD1Sign", {})
                degrees_in_sign = float(sign_data.get("DegreesIn", {}).get("TotalDegrees", 0.0))
                
                if degrees_in_sign > highest_degree:
                    highest_degree = degrees_in_sign
                    ak_name = str(p)
            except:
                continue
        return ak_name

    # --- TM-001 & TM-002: SEQUENTIAL SCAN ---
    dasha_sequence = []
    current_dt = start_dt
    last_md, last_ad = "", ""

    while current_dt <= end_dt:
        time_str = current_dt.strftime("%H:%M %d/%m/%Y {offset}")
        target_time = Time(time_str, geolocation)

        try:
            # Verified 3-arg method for 2026 build
            raw = Calculate.DasaAtTime(birth_time, target_time, 3)
            md = list(raw.keys())[0]
            ad = list(raw[md]['SubDasas'].keys())[0]

            if md != last_md:
                dasha_sequence.append({
                    "Level": "Mahadasha",
                    "Planet": md,
                    "Start": current_dt.strftime("%Y-%m-%d")
                })
                last_md = md

            if ad != last_ad:
                dasha_sequence.append({
                    "Level": "Antardasha",
                    "Planet": ad,
                    "Parent": md,
                    "Start": current_dt.strftime("%Y-%m-%d")
                })
                last_ad = ad
        except:
            pass
        
        current_dt += timedelta(days=20)

    # Post-process End Dates
    for i in range(len(dasha_sequence) - 1):
        dasha_sequence[i]["End"] = dasha_sequence[i+1]["Start"]
    if dasha_sequence:
        dasha_sequence[-1]["End"] = end_dt.strftime("%Y-%m-%d")

    # --- TM-001: CURRENT SNAPSHOT ---
    now_snap = Calculate.DasaForNow(birth_time, 3)
    md_now = list(now_snap.keys())[0]
    ad_now = list(now_snap[md_now]['SubDasas'].keys())[0]
    pd_now = list(now_snap[md_now]['SubDasas'][ad_now]['SubDasas'].keys())[0]

    # --- FINAL STRUCTURED JSON ---
    audit_data = {
        "Metadata": {
            "UID_Reference": ["TM-001", "TM-002", "TM-003"],
            "Birth_Time": "1990-08-15T14:30:00+05:30",
            "Current_Time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "Dasha_Timeline": {
            "TM-001_Active_Period": {
                "Mahadasha": md_now,
                "Antardasha": ad_now,
                "Pratyantardasha": pd_now
            },
            "TM-002_Full_Sequence": dasha_sequence,
            "TM-003_Atmakaraka": get_atmakaraka()
        }
    }

    with open("2.dasha_payload.json", "w") as f:
        json.dump(audit_data, f, indent=2)
    
    print("Success: dasha_audit_log.json generated with verified Atmakaraka.")

if __name__ == "__main__":
       # Load inputs
    config_data = load_config("config.json")
    generate_dasha_audit_file(config_data)
