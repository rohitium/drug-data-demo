#!/usr/bin/env python3
"""
Pretty-print a 5-row preview of each primary table.
"""

import pandas as pd, config as C

for tbl in C.PRIMARY:
    df = pd.read_parquet(
        f"{C.S3_BUCKET}{tbl}.parquet",
        storage_options={"profile":C.AWS_PROFILE}
        ).head()
    print(f"\n=== {tbl.upper()} (first {len(df)} rows) ===")
    print(df.to_markdown(index=False, tablefmt="github"))