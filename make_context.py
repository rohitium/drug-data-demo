# make_context.py
import great_expectations as ge, pathlib, shutil

CTX_DIR = pathlib.Path("great_expectations")

# nuke if you’re experimenting
if CTX_DIR.exists():
    shutil.rmtree(CTX_DIR)

ctx = ge.data_context.FileDataContext._create(project_root_dir=".")
print("✨  Created GE context at:", CTX_DIR.resolve())
