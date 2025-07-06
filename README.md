### Drug-Data Demo · OpenFDA → ETL → S3

---

A reproducible mini-pipeline that **ingests FDA-regulated drug data**, assigns
deterministic UUIDs, auto-generates JSON-Schema, validates, and publishes both
raw Parquet and human-readable previews.

🔗 **Live preview:** [https://rohitium.github.io/drug-data-demo/](https://rohitium.github.io/drug-data-demo/)

```
openFDA (REST)
        │
        ▼
src/drug_data_demo/pipelines/ingest_fda.py
        │                 ┌──── Parquet ──► S3  bucket  (drug-data-demo-release)
        │                 │                └── 4 primary + 3 mapping tables
        │                 │
        │                 ├─ build_schema.py       → schema/*.json  (draft-07)
        │                 ├─ validate.py           → JSON-Schema + FK QC
        │                 ├─ preview_to_console.py → Markdown in terminal
        │                 └─ preview_to_html.py    → docs/index.html (GitHub Pages)
        │
scripts/run_ingest.sh  – one-click orchestrator (env + pipeline)
```

---

## Quick-start

### 0 · Prerequisites

| Need        | Notes                                                                   |
| ----------- | ----------------------------------------------------------------------- |
| **Conda**   | Miniconda ≥ 23 ( `conda` on PATH )                                      |
| **AWS CLI** | profile **`demo`** with write access to `drug-data-demo-release` bucket |
| *Optional*  | `export OPENFDA_API_KEY=…` to avoid rate limits                         |

### 1 · Clone & run

```bash
git clone https://github.com/rohitium/drug-data-demo.git
cd drug-data-demo
chmod +x scripts/run_ingest.sh
./scripts/run_ingest.sh
```

The helper script will

1. create / activate Conda env **`drug-demo`**
2. `pip install -r requirements.txt && pip install -e .`
3. verify `OPENFDA_API_KEY` (if any) and AWS profile
4. execute, in order:

   | step              | module                                                  |
   | ----------------- | ------------------------------------------------------- |
   | ingest            | `python -m drug_data_demo.pipelines.ingest_fda`         |
   | schema            | `python -m drug_data_demo.pipelines.build_schema`       |
   | validate          | `python -m drug_data_demo.pipelines.validate`           |
   | preview (console) | `python -m drug_data_demo.pipelines.preview_to_console` |
   | preview (HTML)    | `python -m drug_data_demo.pipelines.preview_to_html`    |

### 2 · Manual commands

```bash
# pull fresh data & upload parquet
python -m drug_data_demo.pipelines.ingest_fda

# regenerate draft-07 JSON-Schema
python -m drug_data_demo.pipelines.build_schema

# QC directly from S3
python -m drug_data_demo.pipelines.validate
```

---

## Code tour (src/)

| Path                                 | Purpose                                                                     |
| ------------------------------------ | --------------------------------------------------------------------------- |
| **`drug_data_demo/config.py`**       | Central constants: S3 bucket, API URLs, table lists                         |
| **`drug_data_demo/uuid_helpers.py`** | Namespace-UUID generator ⇒ stable keys across runs                          |
| **`drug_data_demo/utils.py`**        | Shared helpers (openFDA call wrapper, first-sentence, schema/FK validators) |
| **pipelines/**                       | five runnable modules (ingest / schema / validate / previews)               |
| **schema/**                          | auto-derived draft-07 JSON-Schema files                                     |
| **docs/**                            | GitHub Pages site (written by `preview_html.py`)                            |
| **scripts/run_ingest.sh**            | one-click pipeline + env bootstrap                                          |

---

## Extending the pipeline

### 1 · More openFDA endpoints

* Clinical trials `/drug/drugtrial.json`
* Adverse events `/drug/event.json`
* Interactions / BB warnings inside `/drug/label.json`
* PK/PD & pharmacogenomics `/drug/ndc.json`

Add an extractor in **`ingest_fda.py`**, append to the `tables` dict; schema and
validation adapt automatically because they iterate over `config.ALL`.

### 2 · FDA Advisory-Committee documents

Scrape PDFs from meeting pages (e.g. cardio-renal - Oct 2024) with
`requests + beautifulsoup4`, upload to S3, and store metadata in a new
`advisory_docs` table keyed by `drug_uuid`.

### 3 · PubMed / ClinicalTrials.gov fusion

* **PubMed Entrez** → store `pmid`, abstract, MeSH in `pubmed.parquet`
* **CT.gov bulk TSV** → link `nct_id` ↔ `drug_uuid` via active-ingredient map

Each new table can be primary or mapping; deterministic UUID namespaces keep PK
and FK logic intact and auto-schema continues to work.

---

## Security & cost

* Upload: **one PUT per table**, < 1 MB total for the demo
* Read: streaming via `s3fs` (no local temp files)
* For thousands of drugs, swap `pandas` for **Polars** or **DuckDB** to stay
  memory-efficient.

PRs welcome!