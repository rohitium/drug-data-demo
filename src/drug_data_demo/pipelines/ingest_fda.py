#!/usr/bin/env python3
"""
Pull basic regulatory + label data for a small demo set of drugs
via openFDA.
"""

import tempfile, subprocess, os, pandas as pd
from collections import OrderedDict
from drug_data_demo.uuid_helpers import *
from drug_data_demo import utils as U, config as C

DRUGS = OrderedDict([
    ("125514", "Keytruda"),
    ("209637", "Ozempic"),
    ("204063", "Tecfidera"),
    ("125057", "Humira"),
    ("761269", "Leqembi"),
])

# ---------------- ingest ----------------
mol_seen = {}; ind_seen = {}; moa_seen = {}
drugs, mols, inds, moas, map_dm, map_di, map_dmoa = ([] for _ in range(7))

for appl_no, brand in DRUGS.items():
    reg = U.search_variants(
        C.BASE_DRUGSFDA,
        [f"application_number:\"{p}{appl_no}\"" for p in ("BLA","NDA","")] +
        [f"openfda.brand_name:\"{brand}\""],
        "drugsfda",
    )
    lbl = U.search_variants(
        C.BASE_LABEL,
        [f"openfda.application_number:\"{p}{appl_no}\"" for p in ("BLA","NDA","")] +
        [f"openfda.brand_name:\"{brand}\""],
        "label",
    )

    brand_name = (reg.get("openfda", {}).get("brand_name", [brand]))[0]
    active_ing = reg["products"][0]["active_ingredients"][0]["name"]
    indication = U.first_sentence(lbl.get("indications_and_usage", []))
    moa_txt    = (lbl.get("mechanism_of_action") or
                  lbl.get("openfda", {}).get("pharm_class_moa") or [None])[0]

    drug_uuid = make_uuid(NS_DRUG, appl_no)
    drugs.append({"drug_uuid": drug_uuid,
                  "application_number": appl_no,
                  "drug_name": brand_name})

    if active_ing not in mol_seen:
        mol_uuid = make_uuid(NS_MOLECULE, active_ing)
        mol_seen[active_ing] = mol_uuid
        mols.append({"molecule_uuid": mol_uuid, "active_ingredient": active_ing})
    map_dm.append({"drug_uuid": drug_uuid, "molecule_uuid": mol_seen[active_ing]})

    if indication not in ind_seen:
        ind_uuid = make_uuid(NS_INDIC, indication or "NA")
        ind_seen[indication] = ind_uuid
        inds.append({"indication_uuid": ind_uuid, "indication_text": indication})
    map_di.append({"drug_uuid": drug_uuid, "indication_uuid": ind_seen[indication]})

    if moa_txt not in moa_seen:
        moa_uuid = make_uuid(NS_MOA, moa_txt or "NA")
        moa_seen[moa_txt] = moa_uuid
        moas.append({"moa_uuid": moa_uuid, "moa_text": moa_txt})
    map_dmoa.append({"drug_uuid": drug_uuid, "moa_uuid": moa_seen[moa_txt]})

tables = {
    "drugs.parquet":           pd.DataFrame(drugs),
    "molecules.parquet":       pd.DataFrame(mols),
    "indications.parquet":     pd.DataFrame(inds),
    "moas.parquet":            pd.DataFrame(moas),
    "drug_molecule.parquet":   pd.DataFrame(map_dm),
    "drug_indication.parquet": pd.DataFrame(map_di),
    "drug_moa.parquet":        pd.DataFrame(map_dmoa),
}

# ---------------- upload ----------------
for fname, df in tables.items():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        df.to_parquet(tmp.name, index=False)
        subprocess.run(
            ["aws", "s3", "cp", tmp.name, f"{C.S3_BUCKET}{fname}",
             "--profile", C.AWS_PROFILE],
            check=True, stdout=subprocess.DEVNULL)
    os.remove(tmp.name)
    print("📤", fname, "uploaded")

print("✅  Ingest complete")