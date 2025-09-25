import pandas as pd
import googlemaps
from dotenv import load_dotenv
import os

load_dotenv()
api_key=os.getenv("GOOGLE_API")

df = pd.read_csv("florida_pharmacies_clean.csv")
gmaps = googlemaps.Client(key=api_key)

lats, lons = [], []
for addr in df["full_address"]:
    geocode_result = gmaps.geocode(addr)
    if geocode_result:
        loc = geocode_result[0]["geometry"]["location"]
        lats.append(loc["lat"])
        lons.append(loc["lng"])
    else:
        lats.append(None); lons.append(None)

df["lat"], df["lon"] = lats, lons
df.to_csv("florida_pharmacies_geocoded.csv", index=False)


