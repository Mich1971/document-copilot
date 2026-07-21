# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "docling==2.96.0",
# ]
# ///
"""Convert PDF files in data/downloads/ to DoclingDocument JSON files.

Outputs are saved to data/doclingdocuments/ as .json files, one per PDF.
A manifest.json is written alongside for future UI-driven ingestion.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

INPUT_DIR = Path(__file__).resolve().parent / "downloads"
OUTPUT_DIR = Path(__file__).resolve().parent / "doclingdocuments"
CLEAR_OUTPUT_DIR = False
SKIP_EXISTING = True


def convert_pdfs_to_docling_documents() -> dict:
    if not INPUT_DIR.is_dir():
        raise FileNotFoundError(f"Missing input directory: {INPUT_DIR}")

    pdfs = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdfs:
        raise ValueError(f"No PDF files found in {INPUT_DIR}")

    if CLEAR_OUTPUT_DIR and OUTPUT_DIR.exists():
        import shutil
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    converter = DocumentConverter()
    manifest = {
        "source": "local-uploads",
        "converted_at_utc": datetime.now(UTC).isoformat(),
        "converted_count": 0,
        "documents": [],
    }

    for pdf_path in pdfs:
        stem = pdf_path.stem
        output_path = OUTPUT_DIR / f"{stem}.json"

        if SKIP_EXISTING and output_path.exists():
            print(f"Skipping existing {output_path.name}")
            manifest["documents"].append({
                "source_filename": pdf_path.name,
                "docling_document": str(output_path.name),
            })
            manifest["converted_count"] += 1
            continue

        print(f"Converting {pdf_path.name} ...")
        result = converter.convert(pdf_path)
        document: DoclingDocument = result.document

        # Persist the DoclingDocument as JSON for later ingestion.
        doc_json = json.dumps(document.export_to_dict(), ensure_ascii=False)
        output_path.write_text(doc_json, encoding="utf-8")

        manifest["documents"].append({
            "source_filename": pdf_path.name,
            "docling_document": str(output_path.name),
        })
        manifest["converted_count"] += 1

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    result = convert_pdfs_to_docling_documents()
    print(
        f"Converted {result['converted_count']} PDF(s) from {INPUT_DIR} to {OUTPUT_DIR}"
    )
    print(f"Manifest: {OUTPUT_DIR / 'manifest.json'}")
