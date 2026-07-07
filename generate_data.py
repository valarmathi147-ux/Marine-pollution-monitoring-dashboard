import csv
import random
from datetime import datetime, timedelta

def get_pollution_status(level, oil_spill, plastic, sewage):
    if level > 75 or oil_spill == "Yes":
        return "High"
    if plastic > 300 and sewage == "Yes":
        return "High"
    if 40 <= level <= 75:
        return "Moderate"
    return "Low"

def generate_data(num_rows=1200):
    locations = ["Mumbai", "Chennai", "Kochi", "Visakhapatnam", "Goa", "Mangalore", "Kolkata", "Port Blair", "Surat", "Puri"]
    water_bodies = ["Sea", "Ocean", "River"]
    
    with open("marine_pollution_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "record_id", "location", "water_body", "pollution_level", "temperature", 
            "pH_value", "dissolved_oxygen", "plastic_density", "oil_spill", 
            "industrial_waste", "sewage_discharge", "biodiversity_index", "date", "pollution_status"
        ])
        
        start_date = datetime(2023, 1, 1)
        
        for i in range(1, num_rows + 1):
            loc = random.choice(locations)
            wb = random.choice(water_bodies)
            pollution_level = random.randint(10, 100)
            temp = round(random.uniform(20.0, 32.0), 1)
            ph = round(random.uniform(6.5, 8.5), 1)
            do = round(random.uniform(3.0, 8.0), 1)
            plastic = random.randint(50, 500)
            oil = random.choice(["Yes", "No", "No", "No"]) # Lower probability of yes
            industry = random.choice(["Yes", "No"])
            sewage = random.choice(["Yes", "No"])
            bio_index = round(random.uniform(0.1, 1.0), 2)
            if oil == 'Yes' or pollution_level > 80:
                bio_index = round(random.uniform(0.1, 0.4), 2) # Worse biodiversity in high pollution
                
            date_val = (start_date + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
            
            # Use the rule-engine to set initial status
            status = get_pollution_status(pollution_level, oil, plastic, sewage)
            
            writer.writerow([
                i, loc, wb, pollution_level, temp, ph, do, plastic, oil, industry, sewage, bio_index, date_val, status
            ])

if __name__ == "__main__":
    generate_data()
    print("Successfully generated marine_pollution_data.csv")
