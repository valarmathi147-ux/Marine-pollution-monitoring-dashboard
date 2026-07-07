import pymongo
import pandas as pd
from django.conf import settings

# MongoDB Setup
def get_db_collection():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['marine_db']
    collection = db['marine_pollution']
    return collection

# Rule-Based Engine
def calculate_status(row):
    """
    IF pollution_level > 75 OR oil_spill == "Yes": "High"
    ELIF pollution_level >= 40 AND pollution_level <= 75: "Moderate"
    ELSE: "Low"
    Advanced Rule: IF plastic_density > 300 AND sewage_discharge == "Yes": "High"
    """
    level = row.get('pollution_level', 0)
    oil = row.get('oil_spill', 'No')
    plastic = row.get('plastic_density', 0)
    sewage = row.get('sewage_discharge', 'No')
    
    if level > 75 or oil == 'Yes':
        return 'High'
    if plastic > 300 and sewage == 'Yes':
        return 'High'
    if 40 <= level <= 75:
        return 'Moderate'
    return 'Low'

# Data Processing
def process_and_store_csv(file_path):
    # Read CSV
    df = pd.read_csv(file_path)
    
    # Handle missing values - rule of thumb: drop rows with critical missing info
    df = df.dropna(subset=['location', 'pollution_level'])
    df = df.fillna({
        'plastic_density': pd.to_numeric(df['plastic_density'].dropna()).mean() if 'plastic_density' in df and not df['plastic_density'].dropna().empty else 0,
        'temperature': pd.to_numeric(df['temperature'].dropna()).mean() if 'temperature' in df and not df['temperature'].dropna().empty else 25.0,
        'oil_spill': 'No',
        'sewage_discharge': 'No'
    })
    
    # Convert required columns numeric
    df['pollution_level'] = pd.to_numeric(df['pollution_level'], errors='coerce').fillna(0)
    df['plastic_density'] = pd.to_numeric(df['plastic_density'], errors='coerce').fillna(0)
    
    # Apply Rule Engine using lambda
    df['pollution_status'] = df.apply(lambda row: calculate_status(row), axis=1)
    
    # Store to MongoDB
    collection = get_db_collection()
    
    # Bulk insert
    records = df.to_dict('records')
    if records:
        # Avoid inserting duplicates by dropping or checking (For simplicity simply clear and re-upload or just append)
        # We will append, but to avoid infinite growth on multiple uploads, you could `collection.delete_many({})` 
        collection.delete_many({}) # Reset collection on new upload as per typical simple semester project behaviour
        collection.insert_many(records)
    
    return len(records)
