#!/usr/bin/env python3
import pandas as pd, datetime, pathlib
from drug_data_demo import config as C

parts = ["<h1>Drug-data demo preview</h1>",
         f"<p>Generated {datetime.date.today()}</p>"]

for tbl in C.PRIMARY:
    df = pd.read_parquet(
        f"{C.S3_BUCKET}{tbl}.parquet",
        storage_options={"profile":C.AWS_PROFILE}
        ).head()
    parts.append(f"<h2>{tbl.title()}</h2>")
    parts.append(df.to_html(index=False))

html = "\n".join(parts)
pathlib.Path("docs").mkdir(exist_ok=True)
pathlib.Path("docs/index.html").write_text(html)
print("✅  docs/index.html written – push & GitHub Pages will update")
