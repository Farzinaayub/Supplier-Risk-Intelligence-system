import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent[0]

GEN_DIR = BASE_DIR / "synth_scripts" / "gen"
VAL_DIR = BASE_DIR / "synth_scripts" / "val"

PIPELINE = [
    GEN_DIR / "suppliermaster.py",
    GEN_DIR / "purchaseorder.py",
    GEN_DIR / "shipments.py",
    GEN_DIR / "qualityinspection.py",
    GEN_DIR / "inventory.py",
    GEN_DIR / "supplieraudit.py",
    GEN_DIR / "incident.py",
    VAL_DIR / "validate.py",
]

for notebook_path in PIPELINE:
    print(f"\nRunning: {notebook_path}")

    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(
        timeout=1200,
        kernel_name="python3"
    )

    ep.preprocess(
        nb,
        {"metadata": {"path": str(Path(notebook_path).parent)}}
    )

    print(f"Completed: {notebook_path}")

print("\nPipeline completed successfully.")