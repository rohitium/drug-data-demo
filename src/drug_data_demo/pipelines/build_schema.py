#!/usr/bin/env python3
"""
Generate JSON-Schema files for every Parquet table in data-demo.

Usage:
    python build_schema.py            # after ingest_fda.py
"""

from pathlib import Path
import json, pandas as pd

from drug_data_demo import config as C

SCHEMA_DIR = Path("schema")
SCHEMA_DIR.mkdir(exist_ok=True)

# --- simple dtype → JSON type mapping -------------------------------------
def json_type(dtype) -> str:
    if pd.api.types.is_integer_dtype(dtype):
        return "integer"
    if pd.api.types.is_float_dtype(dtype):
        return "number"
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    return "string"        # default

for tbl in C.ALL:
    df = pd.read_parquet(
        f"{C.S3_BUCKET}{tbl}.parquet",
        storage_options={"profile": C.AWS_PROFILE},
    )

    props = {}
    req   = []
    for col in df.columns:
        prop = {"type": json_type(df[col].dtype)}
        if col.endswith("_uuid"):
            prop["format"] = "uuid"
        props[col] = prop
        req.append(col)

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": tbl,
        "type": "object",
        "properties": props,
        "required": req,
        "additionalProperties": False,
    }

    out = SCHEMA_DIR / f"{tbl}_v0.1.0.json"
    out.write_text(json.dumps(schema, indent=2))
    print("📝  wrote", out)

print("✅  Schema generation complete")
