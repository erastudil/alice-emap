"""export_csr.py - Standalone entrypoint for exporting Alice 1.0 EMap CSR binary."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_emap_graph import export_csr, get_db

if __name__ == "__main__":
    db = get_db()
    bytes_exported = export_csr(db)
    print(f"CSR binary successfully compiled: {bytes_exported} bytes")