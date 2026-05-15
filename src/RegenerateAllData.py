import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

GEN_DIR = BASE_DIR / "synth_scripts" / "gen"
VAL_DIR = BASE_DIR / "synth_scripts" / "val"

PIPELINE = [
    GEN_DIR / "suppliermaster.ipynb",
    GEN_DIR / "purchaseorder.ipynb",
    GEN_DIR / "shipments.ipynb",
    GEN_DIR / "qualityinspection.ipynb",
    GEN_DIR / "inventory.ipynb",
    GEN_DIR / "supplieraudit.ipynb",
    GEN_DIR / "incident.ipynb",
    VAL_DIR / "Validate_synthetic_data.ipynb",
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