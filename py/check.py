import re
import pandas as pd

IN  = "florida_pharmacies.csv"
OUT = "florida_pharmacies_clean.csv"

df = pd.read_csv(IN, dtype=str, low_memory=False)

def find_col(patterns, required=True):
    """
    Return the first column whose name matches ANY regex in `patterns`.
    If not found and required, raise a helpful error showing close matches.
    """
    cols = list(df.columns)
    for pat in patterns:
        rx = re.compile(pat, flags=re.IGNORECASE)
        for c in cols:
            if rx.search(c):
                return c
    if required:
        hints = [c for c in cols if any(pat.split()[0].lower() in c.lower() for pat in patterns)]
        raise KeyError(f"Could not find any of {patterns}\nClosest matches:\n  " + "\n  ".join(hints[:20]))
    return None

col_npi   = find_col([r"^NPI$"])
col_name  = find_col([r"Provider Organization Name", r"Legal Business Name"])
col_tax_code = find_col([r"Healthcare Provider Taxonomy Code[_\s]?1", r"Healthcare Provider Taxonomy Code"])
col_tax_desc = find_col([r"Healthcare Provider Taxonomy[\s_]?1(?!\s*Code)", r"Healthcare Provider Taxonomy(?!.*Code)"], required=False)

# location address pieces
col_addr1 = find_col([
    r"Provider Business Practice Location Address Line 1",
    r"Practice Location Address Line 1"
])
col_city  = find_col([
    r"Provider Business Practice Location Address City Name",
    r"Practice Location Address City Name"
])
col_state = find_col([
    r"Provider Business Practice Location Address State Name",
    r"Practice Location Address State Name"
])
col_zip   = find_col([
    r"Provider Business Practice Location Address Postal Code",
    r"Practice Location Address Postal Code"
])

# latitude / longitude 
col_lat = find_col([
    r"Practice Location Address Latitude",
    r"Provider Business Practice Location Address Latitude",
])
col_lon = find_col([
    r"Practice Location Address Longitude",
    r"Provider Business Practice Location Address Longitude",
])

print("Resolved columns:")
for lab, val in [
    ("NPI", col_npi), ("Name", col_name), ("TaxCode", col_tax_code), ("TaxDesc", col_tax_desc),
    ("Addr1", col_addr1), ("City", col_city), ("State", col_state), ("ZIP", col_zip),
    ("Lat", col_lat), ("Lon", col_lon)
]:
    print(f"  {lab}: {val}")

if "Entity Type Code" in df.columns:
    df = df[df["Entity Type Code"] == "2"]
if "NPI Deactivation Date" in df.columns:
    df = df[df["NPI Deactivation Date"].isna()]

# build slim dataframe
keep_map = {
    "NPI": col_npi,
    "name": col_name,
    "taxonomy_code": col_tax_code,
    "taxonomy_desc": col_tax_desc if col_tax_desc else col_tax_code,  # fallback
    "addr1": col_addr1,
    "city": col_city,
    "state": col_state,
    "zip": col_zip,
    "lat": col_lat,
    "lon": col_lon,
}
df_small = df[list(keep_map.values())].copy()
df_small.columns = list(keep_map.keys())

df_small["lat"] = pd.to_numeric(df_small["lat"], errors="coerce")
df_small["lon"] = pd.to_numeric(df_small["lon"], errors="coerce")
df_small.drop_duplicates(subset=["NPI","addr1","city","zip"], inplace=True)

df_small.to_csv(OUT, index=False)
print(f"Saved → {OUT}  ({len(df_small)} rows, {df_small['lat'].notna().sum()} with lat/lon)")
