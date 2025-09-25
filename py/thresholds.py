import os, json
import pandas as pd
import geopandas as gpd

TRACTS_DIST = "data/processed/fl_tracts_distances.geojson"
OUT_DESERTS = "data/processed/fl_tracts_deserts.geojson"
OUT_SUMMARY = "data/processed/summary_stats.json"
OUT_TOP = "data/processed/top_deserts_equity.csv"

# this loads tracts with nearest_miles + equity
g = gpd.read_file(TRACTS_DIST)
g["nearest_miles"] = pd.to_numeric(g["nearest_miles"], errors="coerce")
g["SVI"] = pd.to_numeric(g.get("SVI"), errors="coerce")

# tracts with nearest_miles <= 2 mi to urban; others are rural
g["area_type"] = g["nearest_miles"].apply(lambda d: "urban" if d <= 2 else "rural")

thresh = {"urban": 1.0, "rural": 10.0}
g["threshold_mi"] = g["area_type"].map(thresh)
g["is_desert"] = g["nearest_miles"] > g["threshold_mi"]

total_tracts = len(g)
deserts = int(g["is_desert"].sum())
pct_deserts = round(100.0 * deserts / total_tracts, 2)

high_svi_mask = g["SVI"].notna() & (g["SVI"] >= 0.75)

stats = {
    "total_tracts": total_tracts,
    "desert_tracts": deserts,
    "desert_rate_percent": pct_deserts,
    "by_area_type_percent": (
        g.groupby("area_type")["is_desert"].mean().mul(100).round(2).to_dict()
    ),
    "high_SVI_deserts_count": int(g.loc[g["is_desert"] & high_svi_mask].shape[0]),
}

if "in_mua" in g.columns:
    stats["deserts_in_MUA_count"] = int(g.loc[g["is_desert"] & g["in_mua"], "GEOID"].count())

os.makedirs("data/processed", exist_ok=True)
g.to_file(OUT_DESERTS, driver="GeoJSON")

top = (g.sort_values("nearest_miles", ascending=False)
         .loc[:, ["GEOID","nearest_miles","area_type","threshold_mi","is_desert","SVI","in_mua"]]
         .head(100))
top.to_csv(OUT_TOP, index=False)

with open(OUT_SUMMARY, "w") as f:
    json.dump(stats, f, indent=2)

print("Saved:")
print(" ", OUT_DESERTS)
print(" ", OUT_TOP)
print(" ", OUT_SUMMARY)
print("Stats:", json.dumps(stats, indent=2))
