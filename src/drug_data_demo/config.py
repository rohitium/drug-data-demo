# Centralised constants
S3_BUCKET   = "s3://drug-data-demo-release/"
AWS_PROFILE = "demo"

BASE_DRUGSFDA = "https://api.fda.gov/drug/drugsfda.json"
BASE_LABEL    = "https://api.fda.gov/drug/label.json"
API_KEY       = None        # or:  os.getenv("OPENFDA_API_KEY")

PRIMARY  = ["drugs", "molecules", "indications", "moas"]
MAPPING  = ["drug_molecule", "drug_indication", "drug_moa"]
ALL      = PRIMARY + MAPPING