#!/usr/bin/env python3
"""
Validate Parquet tables against JSON Schema.
"""

import pandas as pd, json
from drug_data_demo import config as C, utils as U

dfs = {t: pd.read_parquet(f"{C.S3_BUCKET}{t}.parquet",
                          storage_options={"profile": C.AWS_PROFILE})
       for t in C.ALL}

# 1 – JSON Schema
for t, df in dfs.items():
    schema = json.load(open(f"schema/{t}_v0.1.0.json"))
    U.validate_schema(df, schema)

# 2 – PK uniqueness
for p in C.PRIMARY:
    pk = f"{p[:-1]}_uuid"
    if dfs[p][pk].duplicated().any():
        raise ValueError(f"{p}: duplicate {pk}")

# 3 – FK integrity
sets = {p: set(dfs[p][f"{p[:-1]}_uuid"]) for p in C.PRIMARY}
U.fk_check(dfs["drug_molecule"], "drug_uuid",     sets["drugs"],      "drug_molecule")
U.fk_check(dfs["drug_molecule"], "molecule_uuid", sets["molecules"],  "drug_molecule")
U.fk_check(dfs["drug_indication"], "drug_uuid",   sets["drugs"],      "drug_indication")
U.fk_check(dfs["drug_indication"], "indication_uuid", sets["indications"], "drug_indication")
U.fk_check(dfs["drug_moa"], "drug_uuid",          sets["drugs"],      "drug_moa")
U.fk_check(dfs["drug_moa"], "moa_uuid",           sets["moas"],       "drug_moa")

print("✅  Validation passed")