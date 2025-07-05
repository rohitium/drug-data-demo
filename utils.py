# utils.py

import re, requests, json
from typing import List, Optional, Dict
from jsonschema import Draft7Validator
import config as C
import pandas as pd

# ---------------- openFDA helpers ----------------
def call_openfda(endpoint: str, query: str) -> Optional[Dict]:
    params = {"search": query, "limit": "1"}
    if C.API_KEY:
        params["api_key"] = C.API_KEY
    r = requests.get(endpoint, params=params, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("results", [None])[0]

def search_variants(endpoint: str, variants: List[str], label: str) -> Dict:
    for q in variants:
        hit = call_openfda(endpoint, q)
        if hit:
            return hit
    raise ValueError(f"No {label} record found")

def first_sentence(text_list: list) -> Optional[str]:
    return re.split(r"[.;\n]", text_list[0])[0].strip() if text_list else None

# ---------------- validation helpers ----------------
def validate_schema(df: pd.DataFrame, schema: dict) -> None:
    v = Draft7Validator(schema)
    for i, rec in df.iterrows():
        for err in v.iter_errors(rec.to_dict()):
            raise ValueError(f"{schema['title']} row {i}: {err.message}")

def fk_check(df: pd.DataFrame, col: str, master_set: set, table: str) -> None:
    bad = df.loc[~df[col].isin(master_set)]
    if not bad.empty:
        raise ValueError(f"{table}: {len(bad)} invalid {col}")
