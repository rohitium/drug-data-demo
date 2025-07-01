#!/usr/bin/env python3
"""
Pull basic regulatory + label data for a small demo set of drugs
via openFDA.
"""

import os, requests, pandas as pd, re
from collections import OrderedDict
from uuid_helpers import *

BASE_DRUGSFDA = "https://api.fda.gov/drug/drugsfda.json"
BASE_LABEL    = "https://api.fda.gov/drug/label.json"
API_KEY       = os.getenv("OPENFDA_API_KEY")

DRUGS = OrderedDict([
    ("125514", "Keytruda"),   # BLA
    ("209637", "Ozempic"),    # NDA
    ("204063", "Tecfidera"),  # NDA
    ("125057", "Humira"),     # BLA
    ("761269", "Leqembi"),    # BLA
])

def call(endpoint, query):
    """Return first result or None if 404/empty."""
    params = {"search": query, "limit": "1"}
    if API_KEY:
        params["api_key"] = API_KEY
    r = requests.get(endpoint, params=params, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    results = r.json().get("results")
    return results[0] if results else None

def search_drugsfda(appl_no, brand):
    variants = [
        f"application_number:\"BLA{appl_no}\"",
        f"application_number:\"NDA{appl_no}\"",
        f"application_number:\"{appl_no}\"",
        f"openfda.brand_name:\"{brand}\"",
    ]
    for q in variants:
        hit = call(BASE_DRUGSFDA, q)
        if hit:
            return hit
    raise ValueError(f"No drugsfda record for {appl_no}/{brand}")

def search_label(appl_no, brand):
    variants = [
        f"openfda.application_number:\"BLA{appl_no}\"",
        f"openfda.application_number:\"NDA{appl_no}\"",
        f"openfda.application_number:\"{appl_no}\"",
        f"openfda.brand_name:\"{brand}\"",
    ]
    for q in variants:
        hit = call(BASE_LABEL, q)
        if hit:
            return hit
    raise ValueError(f"No label record for {appl_no}/{brand}")

def first_sentence(txt_list):
    return re.split(r"[.;\n]", txt_list[0])[0].strip() if txt_list else None

def first_items(txt_list, n=3):
    if not txt_list:
        return None
    return "; ".join(
        p.strip() for p in re.split(r"[.;\n]", txt_list[0])[:n] if p.strip()
    )

# -------- ingest & build tables --------------------------------------------
mol_seen, ind_seen, moa_seen = {}, {}, {}
drugs_rows, mol_rows, ind_rows, moa_rows = [], [], [], []
map_dm, map_di, map_dmoa = [], [], []

for appl_no, brand in DRUGS.items():
    reg = search_drugsfda(appl_no, brand)
    lbl = search_label(appl_no, brand)

    brand_name = (reg.get("openfda", {}).get("brand_name", [brand]))[0]
    active_ing = (reg["products"][0]
                     .get("active_ingredients", [{}])[0]
                     .get("name"))

    indication = first_sentence(lbl.get("indications_and_usage", []))
    moa_txt    = lbl.get("mechanism_of_action", []) or \
                 lbl.get("openfda", {}).get("pharm_class_moa", [])
    moa_txt    = moa_txt[0] if moa_txt else None

    # ---- PKs & rows -------------------------------------------------------
    drug_uuid = make_uuid(NS_DRUG, appl_no)
    drugs_rows.append({
        "drug_uuid": drug_uuid,
        "application_number": appl_no,
        "drug_name": brand_name,
    })

    if active_ing not in mol_seen:
        mol_uuid = make_uuid(NS_MOLECULE, active_ing or "NA")
        mol_seen[active_ing] = mol_uuid
        mol_rows.append({"molecule_uuid": mol_uuid,
                         "active_ingredient": active_ing})
    map_dm.append({"drug_uuid": drug_uuid,
                   "molecule_uuid": mol_seen[active_ing]})

    if indication not in ind_seen:
        ind_uuid = make_uuid(NS_INDIC, indication or "NA")
        ind_seen[indication] = ind_uuid
        ind_rows.append({"indication_uuid": ind_uuid,
                         "indication_text": indication})
    map_di.append({"drug_uuid": drug_uuid,
                   "indication_uuid": ind_seen[indication]})

    if moa_txt not in moa_seen:
        moa_uuid = make_uuid(NS_MOA, moa_txt or "NA")
        moa_seen[moa_txt] = moa_uuid
        moa_rows.append({"moa_uuid": moa_uuid,
                         "moa_text": moa_txt})
    map_dmoa.append({"drug_uuid": drug_uuid,
                     "moa_uuid": moa_seen[moa_txt]})

# -------- write parquet -----------------------------------------------------
pd.DataFrame(drugs_rows).to_parquet("drugs.parquet", index=False)
pd.DataFrame(mol_rows).to_parquet("molecules.parquet", index=False)
pd.DataFrame(ind_rows).to_parquet("indications.parquet", index=False)
pd.DataFrame(moa_rows).to_parquet("moas.parquet", index=False)
pd.DataFrame(map_dm).to_parquet("drug_molecule.parquet", index=False)
pd.DataFrame(map_di).to_parquet("drug_indication.parquet", index=False)
pd.DataFrame(map_dmoa).to_parquet("drug_moa.parquet", index=False)