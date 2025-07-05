### Drug-Data Demo  ·  OpenFDA → ETL → S3

---

A reproducible mini-pipeline that **ingests FDA-regulated drug data**, assigns
deterministic UUIDs, auto-generates JSON Schema, validates, and publishes both
raw Parquet and human-readable previews.

🔗 **Live preview:** [https://rohitium.github.io/drug-data-demo/](https://rohitium.github.io/drug-data-demo/)

```
openFDA (REST)
        │
        ▼
ingest_fda.py ───► Parquet files ───► S3 bucket  (drug-data-demo-release)
                    (drugs, molecules, indications, moas,
                     plus mapping tables: drug_molecule / drug_indication / drug_moa)
        │                                   │
        │                                   ├─ validate.py        → QC report (schema + FK)
        │                                   └─ preview_to_*       → Markdown / HTML preview
        │
        └─ build_schema.py  → schema/*.json (draft-07, auto-derived)
```

---

## Quick-start

### 0. Prereqs

* **Conda** (Miniconda ≥ 23) and **AWS CLI** configured with profile `demo`
* Write-only access to S3 bucket `drug-data-demo-release`
* *Optional:* `OPENFDA_API_KEY` to raise rate limits

### 1. Clone & run

```bash
git clone https://github.com/rohitium/drug-data-demo.git
cd drug-data-demo
chmod +x run_ingest.sh
./run_ingest.sh
```

The script will

1. create/activate Conda env **`drug-demo`**
2. `pip install -r requirements.txt`
3. sanity-check `OPENFDA_API_KEY` and AWS credentials
4. run in order:

   * **`ingest_fda.py`** – pull 5 demo drugs, write & upload Parquet
   * **`build_schema.py`** – derive `schema/*.json` from Parquet columns
   * **`validate.py`** – JSON-Schema + FK integrity check
   * **`preview_to_console.py`** – 5-row Markdown preview to terminal
   * **`preview_to_html.py`** – rebuild `docs/index.html` for GitHub Pages

### 2. Manual commands

```bash
# refresh data
python ingest_fda.py

# re-generate JSON Schema
python build_schema.py

# validate everything directly from S3
python validate.py
```

---

## How it works — modules in 1 minute

| File                    | Purpose                                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------- |
| `uuid_helpers.py`       | Namespace UUID⁵ generator ⇒ stable keys across runs                                                       |
| `config.py`             | Central constants: S3 bucket, API URLs, table lists                                                       |
| `utils.py`              | Re-usable helpers (openFDA calls, first-sentence, schema/FK checks)                                       |
| `ingest_fda.py`         | **Core ETL**: calls openFDA, normalises into 4 primary + 3 mapping tables, streams Parquet straight to S3 |
| `build_schema.py`       | Reads each Parquet, infers JSON types, writes `schema/<table>_v0.1.0.json` (draft-07)                     |
| `validate.py`           | Loads ALL tables from S3, enforces schema + PK uniqueness + FK existence                                  |
| `preview_to_console.py` | Quick CLI snapshot                                                                                        |
| `preview_to_html.py`    | Generates `<docs/index.html>` (GitHub Pages)                                                              |
| `run_ingest.sh`         | One-click orchestrator incl. env bootstrap                                                                |

---

## Extending the pipeline

### 1 · More openFDA endpoints

* **Clinical trials:** `/drug/drugtrial.json`
* **Adverse events:** `/drug/event.json`
* **Drug interactions / contraindications / BB warnings:** additional arrays inside `/drug/label.json`
* **PK/PD & pharmacogenomics:** `/drug/ndc.json` and structured “pharm\_class\_\*” fields

Add a new extractor function in `ingest_fda.py`, append to `tables{}` dict;
`build_schema.py` + `validate.py` adapt automatically because they iterate
over `config.ALL`.

### 2 · FDA Advisory Committee documents

Scrape PDF / HTML from meeting pages (e.g. cardio-renal 10 Oct 2024) using
`requests + BeautifulSoup`, stash key metadata and the S3 object key in a new
`advisory_docs` table, map to `drug_uuid` via application number.

### 3 · PubMed / ClinicalTrials.gov fusion

* **PubMed:** Entrez API → store pmid, abstract, MeSH into `pubmed.parquet`
* **CT.gov:** bulk‐download TSV → filter by intervention, link NCT↔drug\_uuid via
  active ingredient or synonym table.

Because every table gets a deterministic UUID namespace you can attach new
mapping tables (`drug_pubmed`, `drug_clinical_trial`) without touching core
logic—validation & schema auto-generate will cover them.

---

## Security / cost notes

* Writes to S3 use **single PUT per file**; <1 MB total on the demo.
* Reads use `s3fs`’ streaming driver; no tmp files on disk.
* If you ingest thousands of drugs, move to **polars** or **DuckDB** to keep memory constant.

---