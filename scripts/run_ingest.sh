#!/usr/bin/env bash
# End-to-end pipeline: env bootstrap → ingest → schema → validate → previews

set -euo pipefail

ENV=drug-demo
AWS_PROFILE=demo

# ─── 1. Conda env ──────────────────────────────────────────────────────────
if ! command -v conda &>/dev/null; then
  echo "❌  Conda not found. Please install Miniconda / Anaconda." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"

if conda info --envs | awk '{print $1}' | grep -qx "$ENV"; then
  echo "🔄  Activating env '$ENV'"
else
  echo "✨  Creating env '$ENV'"
  conda create -y -n "$ENV" python=3.11
fi
conda activate "$ENV"

# ─── 2. Install Python deps (editable) ─────────────────────────────────────
pip install --upgrade -r requirements.txt
pip install -e .  # install package for clean imports

# ─── 3. Credential checks ─────────────────────────────────────────────────
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &>/dev/null; then
  echo "❌  AWS profile '$AWS_PROFILE' invalid or missing." >&2
  exit 1
fi
echo "✅  AWS profile '$AWS_PROFILE' OK"

if [[ -z "${OPENFDA_API_KEY:-}" ]]; then
  echo "⚠️  OPENFDA_API_KEY not set – you may hit rate limits."
else
  echo "✅  OPENFDA_API_KEY present"
fi

# ─── 4. Run pipeline modules (no CLI wrapper) ──────────────────────────────
PY="python -m drug_data_demo.pipelines"

echo -e "\n▶ ingest_fda.py"
$PY.ingest_fda

echo -e "\n▶ build_schema.py"
$PY.build_schema

echo -e "\n▶ validate.py"
$PY.validate

echo -e "\n▶ preview_to_console.py"
$PY.preview_to_console

echo -e "\n▶ preview_to_html.py"
$PY.preview_to_html

echo -e "\n🎉  Pipeline finished successfully"