import os, sys, re
import pandas as pd
import geopandas as gpd

RAW = "data/raw"
TRACTS_SHP = os.path.join(RAW, "tracts_fl", "tl_2024_12_tract.shp")
COUNTY_SVI = os.path.join(RAW, "SVI_2022_US_county.csv")
OUT = os.path.join(RAW, "SVI_2022_FL_tract.csv")

def norm(s, n):  
    return pd.Series(s, dtype=str).str.replace(r"\D", "", regex=True).str.zfill(n)

if not os.path.exists(TRACTS_SHP):
    sys.exit("Missing Florida tracts shapefile at data/raw/tracts_fl/tl_2024_12_tract.shp")

if not os.path.exists(COUNTY_SVI):
    sys.exit("Missing county SVI at data/raw/SVI_2022_US_county.csv")

print("Loading Florida tracts…")
tracts = gpd.read_file(TRACTS_SHP)
if "GEOID" not in tracts.columns:
    sys.exit("Tracts file has no GEOID column.")
tracts["GEOID"] = norm(tracts["GEOID"], 11)
tracts["county_fips"] = tracts["GEOID"].str[:5]

print("Loading county SVI…")
svi_cty = pd.read_csv(COUNTY_SVI, dtype=str, low_memory=False)
fips_col = "FIPS" if "FIPS" in svi_cty.columns else ("COUNTYFIPS" if "COUNTYFIPS" in svi_cty.columns else None)
if fips_col is None:
    sys.exit("Could not find county FIPS column in county SVI (expected FIPS or COUNTYFIPS).")

svi_cty[fips_col] = norm(svi_cty[fips_col], 5)
svi_cty = svi_cty[svi_cty[fips_col].str.startswith("12")]  # Florida only

keep = [fips_col, "RPL_THEMES"]
for c in ["RPL_THEME1","RPL_THEME2","RPL_THEME3","RPL_THEME4"]:
    if c in svi_cty.columns: keep.append(c)
svi_cty = svi_cty[keep].rename(columns={fips_col: "county_fips", "RPL_THEMES": "SVI"})

print("Building tract-level proxy from county SVI…")
svi_fl_proxy = tracts[["GEOID","county_fips"]].merge(svi_cty, on="county_fips", how="left").drop(columns=["county_fips"])

os.makedirs(RAW, exist_ok=True)
svi_fl_proxy.to_csv(OUT, index=False)
print(f"Saved → {OUT} ({len(svi_fl_proxy)} rows)")
print(svi_fl_proxy.head())