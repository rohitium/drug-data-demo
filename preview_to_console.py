#!/usr/bin/env python3
"""
Pretty-print a 5-row preview of each primary table.
"""

import pandas as pd, textwrap
BUCKET  = "s3://drug-data-demo-release/"
S3_OPTS = {"profile": "demo"}
PRIMARY = ["drugs","molecules","indications","moas"]

for tbl in PRIMARY:
    df = pd.read_parquet(f"{BUCKET}{tbl}.parquet", storage_options=S3_OPTS).head()
    print(f"\n=== {tbl.upper()} (first {len(df)} rows) ===")
    print(df.to_markdown(index=False, tablefmt="github"))