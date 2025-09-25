import pandas as pd
import os, csv

# File path to the big NPPES provider file
FILE = "npidata_pfile_20050523-20250907.csv"
OUT  = "florida_pharmacies.csv"
chunksize = 100000 

wrote_header = False
total_rows = 0
kept_rows = 0

for i, chunk in enumerate(pd.read_csv(FILE, chunksize=chunksize, dtype=str, low_memory=False)):
    # filter pharmacies (any taxonomy col starting with 3336)
    tax_cols = [c for c in chunk.columns if "Healthcare Provider Taxonomy Code" in c]
    is_pharm = chunk[tax_cols].apply(lambda s: s.str.startswith("3336", na=False)).any(axis=1)
    # Florida mailing state
    is_fl = chunk["Provider Business Mailing Address State Name"] == "FL"
    fl = chunk[is_pharm & is_fl]

    total_rows += len(chunk)
    kept_rows  += len(fl)

    # write incrementally so the file exists even if you stop early
    if len(fl):
        mode = "a"
        header = not wrote_header
        fl.to_csv(OUT, index=False, mode=mode, header=header, quoting=csv.QUOTE_MINIMAL)
        wrote_header = True

    if (i+1) % 10 == 0:
        print(f"Processed ~{total_rows:,} rows… kept {kept_rows:,} so far.")

print(f"\nDONE. Saved → {OUT}  (rows: {kept_rows:,})")
print("File location:", os.path.join(os.getcwd(), OUT))