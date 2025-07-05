#!/usr/bin/env python3
"""
Pull basic regulatory + label data for a small demo set of drugs
via openFDA.
"""

import os, re, requests, tempfile, subprocess, pandas as pd
from collections import OrderedDict
from uuid_helpers import *

API_KEY = os.getenv("OPENFDA_API_KEY")
BASE_DRUGSFDA = "https://api.fda.gov/drug/drugsfda.json"
BASE_LABEL    = "https://api.fda.gov/drug/label.json"
S3_BUCKET     = "s3://drug-data-demo-release/"
AWS_PROFILE   = "demo"

DRUGS = OrderedDict([
    ("125514", "Keytruda"),
    ("209637", "Ozempic"),
    ("204063", "Tecfidera"),
    ("125057", "Humira"),
    ("761269", "Leqembi"),
])

# ---------- helpers --------------------------------------------------------
def call(endpoint, query):
    params = {"search": query, "limit": "1"}
    if API_KEY:
        params["api_key"] = API_KEY
    r = requests.get(endpoint, params=params, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json().get("results", [None])[0]

def search(endpoint, variants, err_msg):
    for q in variants:
        hit = call(endpoint, q)
        if hit:
            return hit
    raise ValueError(err_msg)

def first_sentence(txt_list):
    return re.split(r"[.;\n]", txt_list[0])[0].strip() if txt_list else None

# ---------- ingest ---------------------------------------------------------
mol_seen, ind_seen, moa_seen = {}, {}, {}
drugs, mols, inds, moas = [], [], [], []
map_dm, map_di, map_dmoa = [], [], []

for appl_no, brand in DRUGS.items():
    reg = search(
        BASE_DRUGSFDA,
        [
            f"application_number:\"BLA{appl_no}\"",
            f"application_number:\"NDA{appl_no}\"",
            f"application_number:\"{appl_no}\"",
            f"openfda.brand_name:\"{brand}\"",
        ],
        f"No drugsfda record for {appl_no}/{brand}",
    )
    lbl = search(
        BASE_LABEL,
        [
            f"openfda.application_number:\"BLA{appl_no}\"",
            f"openfda.application_number:\"NDA{appl_no}\"",
            f"openfda.application_number:\"{appl_no}\"",
            f"openfda.brand_name:\"{brand}\"",
        ],
        f"No label record for {appl_no}/{brand}",
    )

    brand_name = (reg.get("openfda", {}).get("brand_name", [brand]))[0]
    active_ing = (reg["products"][0].get("active_ingredients", [{}])[0].get("name"))
    indication = first_sentence(lbl.get("indications_and_usage", []))
    moa_txt = (lbl.get("mechanism_of_action") or
               lbl.get("openfda", {}).get("pharm_class_moa") or [None])[0]

    drug_uuid = make_uuid(NS_DRUG, appl_no)
    drugs.append({"drug_uuid": drug_uuid,
                  "application_number": appl_no,
                  "drug_name": brand_name})

    if active_ing not in mol_seen:
        mol_uuid = make_uuid(NS_MOLECULE, active_ing or "NA")
        mol_seen[active_ing] = mol_uuid
        mols.append({"molecule_uuid": mol_uuid,
                     "active_ingredient": active_ing})
    map_dm.append({"drug_uuid": drug_uuid,
                   "molecule_uuid": mol_seen[active_ing]})

    if indication not in ind_seen:
        ind_uuid = make_uuid(NS_INDIC, indication or "NA")
        ind_seen[indication] = ind_uuid
        inds.append({"indication_uuid": ind_uuid,
                     "indication_text": indication})
    map_di.append({"drug_uuid": drug_uuid,
                   "indication_uuid": ind_seen[indication]})

    if moa_txt not in moa_seen:
        moa_uuid = make_uuid(NS_MOA, moa_txt or "NA")
        moa_seen[moa_txt] = moa_uuid
        moas.append({"moa_uuid": moa_uuid,
                     "moa_text": moa_txt})
    map_dmoa.append({"drug_uuid": drug_uuid,
                     "moa_uuid": moa_seen[moa_txt]})

tables = {
    "drugs.parquet":            pd.DataFrame(drugs),
    "molecules.parquet":        pd.DataFrame(mols),
    "indications.parquet":      pd.DataFrame(inds),
    "moas.parquet":             pd.DataFrame(moas),
    "drug_molecule.parquet":    pd.DataFrame(map_dm),
    "drug_indication.parquet":  pd.DataFrame(map_di),
    "drug_moa.parquet":         pd.DataFrame(map_dmoa),
}

# ---------- stream each table to S3 ----------------------------------------
for fname, df in tables.items():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        df.to_parquet(tmp.name, index=False)
        subprocess.run(
            ["aws", "s3", "cp", tmp.name, S3_BUCKET + fname, "--profile", AWS_PROFILE],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    os.remove(tmp.name)
    print(f"📤  {fname} uploaded")

print("✅  All tables ingested and pushed to S3")
