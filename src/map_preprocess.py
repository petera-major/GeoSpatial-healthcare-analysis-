import os, re
import pandas as pd
import geopandas as gpd

TRACTS_SHP = "data/raw/tracts_fl/tl_2024_12_tract.shp"
SVI_TRACT  = "data/raw/SVI_2022_FL_tract.csv"         
MUA_SHP    = "data/raw/mua/MUA_SHP_DET_CUR_VX.shp"                 
OUT_GEOJSON = "data/processed/tracts_fl_equity.geojson"

os.makedirs("data/processed", exist_ok=True)

print("Loading Florida tracts…")
tracts = gpd.read_file(TRACTS_SHP)

if "GEOID" not in tracts.columns:
    geoid_col = next((c for c in tracts.columns if c.upper().startswith("GEOID")), None)
    if not geoid_col:
        raise ValueError(f"No GEOID column found. Columns: {list(tracts.columns)[:20]}")
    tracts = tracts.rename(columns={geoid_col: "GEOID"})
tracts["GEOID"] = tracts["GEOID"].astype(str).str.zfill(11)

keep_cols = [c for c in ["STATEFP","COUNTYFP","TRACTCE","GEOID","NAME","ALAND","AWATER"] if c in tracts.columns]
tracts = tracts[keep_cols + ["geometry"]]

print("Loading SVI 2022 TRACT CSV…")
svi = pd.read_csv(SVI_TRACT, dtype=str, low_memory=False)

fips_candidates = ["GEOID", "FIPS", "TRACTFIPS", "TRACT_FIPS"]
fips_col = next((c for c in fips_candidates if c in svi.columns), None)
if fips_col is None:
    maybe = [c for c in svi.columns if re.search(r"FIPS|GEOID", c, re.I)]
    raise KeyError(f"SVI tract ID column not found. Tried {fips_candidates}. Candidates: {maybe[:10]}")
svi[fips_col] = svi[fips_col].astype(str).str.replace(r"\D","", regex=True).str.zfill(11)

overall_candidates = ["SVI", "RPL_THEMES", "RPL_THEMES_2022", "RPL_THEMES20", "RPL_THEMES22"]
overall_col = next((c for c in overall_candidates if c in svi.columns), None)
if overall_col is None:
    for fb in ["RPL_THEME1","RPL_THEME2","RPL_THEME3","RPL_THEME4"]:
        if fb in svi.columns:
            overall_col = fb
            break
if overall_col is None:
    raise KeyError(f"No overall SVI column found. Looked for {overall_candidates} or RPL_THEME1-4.")

keep = [fips_col, overall_col] + [c for c in ["RPL_THEME1","RPL_THEME2","RPL_THEME3","RPL_THEME4"] if c in svi.columns]
svi = svi[keep].copy().rename(columns={fips_col:"GEOID", overall_col:"SVI"})
svi["GEOID"] = svi["GEOID"].astype(str).str.zfill(11)

print("Joining SVI to tracts…")
tracts = tracts.merge(svi, on="GEOID", how="left")

print("Loading HRSA MUA/P shapefile…")
mua = gpd.read_file(MUA_SHP)

state_field = next((c for c in ["STATE","STATEFP","State","STATE_NAME"] if c in mua.columns), None)
if state_field is not None:
    mua_fl = mua[mua[state_field].astype(str).str.upper().isin(["FL","12"])]
else:
    mua_fl = mua

tracts_3857 = tracts.to_crs(3857)
mua_3857 = mua_fl.to_crs(3857)

print("Flagging tracts that intersect a MUA/P…")
mua_union = mua_3857.unary_union
tracts_3857["in_mua"] = tracts_3857.geometry.intersects(mua_union)

out = tracts_3857.to_crs(4326)
print(f"Saving → {OUT_GEOJSON}")
out.to_file(OUT_GEOJSON, driver="GeoJSON")

print("Done")
print("Columns:", [c for c in out.columns if c != "geometry"])
print("Rows:", len(out))
print("Florida-ish bounds:", out.total_bounds) 
