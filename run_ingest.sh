#!/usr/bin/env bash

set -euo pipefail

ENV_NAME="drug-demo"
AWS_PROFILE="demo"

# --- 1. activate or create conda env --------------------------------------
if ! command -v conda &>/dev/null; then
  echo "❌  Conda not found. Install Miniconda or Anaconda first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"

if conda info --envs | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "🔄  Activating existing conda env '$ENV_NAME'"
else
  echo "✨  Creating conda env '$ENV_NAME'"
  conda create -y -n "$ENV_NAME" python=3.11
fi
conda activate "$ENV_NAME"

# --- 2. install / upgrade Python deps -------------------------------------
pip install --upgrade -r requirements.txt

# --- 3. sanity-check external credentials ---------------------------------
: "${OPENFDA_API_KEY:=}"
if [[ -z $OPENFDA_API_KEY ]]; then
  echo "⚠️  OPENFDA_API_KEY not set; requests will be rate-limited."
else
  echo "✅  OPENFDA_API_KEY detected"
fi

if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &>/dev/null; then
  echo "❌  AWS CLI profile '$AWS_PROFILE' is missing or invalid." >&2
  exit 1
fi
echo "✅  AWS CLI profile '$AWS_PROFILE' looks good"

# --- 4. run the pipeline ---------------------------------------------------
echo -e "\n▶  ingest_fda.py"
python ingest_fda.py

echo -e "\n▶  build_schema.py"
python build_schema.py

echo -e "\n▶  validate.py"
python validate.py

echo -e "\n▶  preview_to_console.py"
python preview_to_console.py

echo -e "\n▶  preview_to_html.py"
python preview_to_html.py

echo -e "\n🎉  Pipeline finished successfully"
