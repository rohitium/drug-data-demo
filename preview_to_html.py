#!/usr/bin/env python3
import pandas as pd, datetime, pathlib
BUCKET  = "s3://drug-data-demo-release/"
S3_OPTS = {"profile": "demo"}
PRIMARY = ["drugs","molecules","indications","moas"]

parts = ["<h1>Drug-data demo preview</h1>",
         f"<p>Generated {datetime.date.today()}</p>"]

for tbl in PRIMARY:
    df = pd.read_parquet(f"{BUCKET}{tbl}.parquet", storage_options=S3_OPTS).head()
    parts.append(f"<h2>{tbl.title()}</h2>")
    parts.append(df.to_html(index=False))

html = "\n".join(parts)
pathlib.Path("docs").mkdir(exist_ok=True)
pathlib.Path("docs/index.html").write_text(html)
print("✅  docs/index.html written – push & GitHub Pages will update")
