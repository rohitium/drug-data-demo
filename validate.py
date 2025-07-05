#!/usr/bin/env python3
"""
Validate Parquet tables against JSON Schema + simple data rules.
Only deps: pandas, jsonschema (install once:  pip install jsonschema)
"""

import json, sys, pandas as pd
from jsonschema import Draft7Validator

BUCKET = "s3://drug-data-demo-release/"
S3_OPTS = {"profile": "demo"}          # use your CLI profile

TABLES = [
    "drugs", "molecules", "indications", "moas",
    "drug_molecule", "drug_indication", "drug_moa",
]

def load_schema(name):
    with open(f"schema/{name}_v0.1.0.json") as fp:
        return json.load(fp)

def validate_schema(df, schema):
    v = Draft7Validator(schema)
    for i, rec in df.iterrows():
        for err in v.iter_errors(rec.to_dict()):
            raise ValueError(f"{schema['title']} row {i}: {err.message}")

def fk_check(df, fk_col, master_set, table):
    bad = df.loc[~df[fk_col].isin(master_set)]
    if not bad.empty:
        raise ValueError(f"{table}: {len(bad)} invalid {fk_col}")

def main():
    dfs = {
        t: pd.read_parquet(f"{BUCKET}{t}.parquet", storage_options=S3_OPTS)
        for t in TABLES
    }

    # 1. JSON Schema compliance
    for t, df in dfs.items():
        validate_schema(df, load_schema(t))

    # 2. PK uniqueness
    for base in ["drugs", "molecules", "indications", "moas"]:
        pk = f"{base[:-1]}_uuid"
        if dfs[base][pk].duplicated().any():
            raise ValueError(f"{base}: duplicate {pk}")

    # 3. Non-null FK columns
    for m in ["drug_molecule", "drug_indication", "drug_moa"]:
        if dfs[m].isna().any().any():
            raise ValueError(f"{m}: NULL values not allowed")

    # 4. FK existence
    sets = {b: set(dfs[b][f"{b[:-1]}_uuid"]) for b in ["drugs","molecules","indications","moas"]}
    fk_check(dfs["drug_molecule"], "drug_uuid",      sets["drugs"],       "drug_molecule")
    fk_check(dfs["drug_molecule"], "molecule_uuid",  sets["molecules"],   "drug_molecule")
    fk_check(dfs["drug_indication"], "drug_uuid",    sets["drugs"],       "drug_indication")
    fk_check(dfs["drug_indication"], "indication_uuid", sets["indications"], "drug_indication")
    fk_check(dfs["drug_moa"], "drug_uuid",           sets["drugs"],       "drug_moa")
    fk_check(dfs["drug_moa"], "moa_uuid",            sets["moas"],        "drug_moa")

    print("✅  All validations passed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌  Validation failed: {e}")
        sys.exit(1)