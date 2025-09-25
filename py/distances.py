import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union

TRACTS_EQ   = "data/processed/tracts_fl_equity.geojson"
PHARM_CLEAN = "florida_pharmacies_geocoded.csv"   
OUT_GEOJSON = "data/processed/fl_tracts_distances.geojson"
OUT_TOPCSV  = "data/processed/top_deserts.csv"

print("Loading equity tracts…")
tracts = gpd.read_file(TRACTS_EQ)
tracts["GEOID"] = tracts["GEOID"].astype(str).str.zfill(11)

print("Loading pharmacies…")
ph = pd.read_csv(PHARM_CLEAN, dtype=str, low_memory=False)

# require lat/lon
if not {"lat","lon"}.issubset(ph.columns):
    raise ValueError("Expected 'lat' and 'lon' in pharmacy file. Point PHARM_CLEAN to the geocoded CSV.")

# drop missing
ph["lat"] = pd.to_numeric(ph["lat"], errors="coerce")
ph["lon"] = pd.to_numeric(ph["lon"], errors="coerce")
ph = ph.dropna(subset=["lat","lon"]).copy()
if ph.empty:
    raise ValueError("All pharmacy lat/lon are NaN after parsing. Check your geocoded file.")

gph = gpd.GeoDataFrame(ph, geometry=gpd.points_from_xy(ph["lon"], ph["lat"]), crs="EPSG:4326")

tracts_m = tracts.to_crs(3857).copy()
gph_m    = gph.to_crs(3857).copy()

# keep original index
tracts_m["centroid"] = tracts_m.geometry.centroid

print("Building union of pharmacy points…")
pharm_union = unary_union(gph_m.geometry.values)  

print("Computing nearest distances (meters)…")
tracts_m["nearest_m"] = tracts_m["centroid"].distance(pharm_union)
tracts_m["nearest_miles"] = tracts_m["nearest_m"] / 1609.34

tracts_m["potential_desert"] = tracts_m["nearest_miles"] > 1.0

out = tracts_m.to_crs(4326).drop(columns=["centroid"])
out.to_file(OUT_GEOJSON, driver="GeoJSON")

(out[["GEOID","SVI","in_mua","nearest_miles"]]
   .sort_values("nearest_miles", ascending=False)
   .head(50)
   .to_csv(OUT_TOPCSV, index=False))

print("Saved:")
print(" ", OUT_GEOJSON)
print(" ", OUT_TOPCSV)
print("Rows:", len(out), "Potential deserts (>1 mi):", int(out["potential_desert"].sum()))
