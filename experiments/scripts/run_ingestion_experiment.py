import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import pymupdf

from edgar.application.bootstrap import build_indexing_runner
from edgar.domain import Document

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = PROJECT_ROOT / "experiments" / "runs"
STORAGE_ROOT = PROJECT_ROOT / "storage" / "experiments"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run an EDGAR document ingestion/indexing experiment."
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the PDF document.",
    )
    return parser.parse_args()


def git_commit():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def make_run_id(pdf_path):
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    document_name = pdf_path.stem.lower().replace(" ", "_")

    return f"{timestamp}_{document_name}_ingestion"


def write_json(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main():
    args = parse_args()
    pdf_path = args.pdf_path.expanduser().resolve()

    if not pdf_path.is_file():
        raise SystemExit(f"PDF not found: {pdf_path}")

    with pymupdf.open(pdf_path) as pdf:
        page_count = pdf.page_count

    run_id = make_run_id(pdf_path)
    run_dir = RUNS_ROOT / run_id
    processing_dir = STORAGE_ROOT / run_id

    run_dir.mkdir(parents=True, exist_ok=False)
    processing_dir.mkdir(parents=True, exist_ok=True)

    document = Document(
        filename=pdf_path.name,
        source_ref=str(pdf_path),
        page_count=page_count,
        doc_id=uuid4(),
    )

    runner = build_indexing_runner(
        storage_root=processing_dir,
    )

    started_at = datetime.now().astimezone()

    start = perf_counter()
    records = runner.run(document)
    elapsed = perf_counter() - start

    finished_at = datetime.now().astimezone()

    type_counts = Counter(record.record.component_type.value for record in records)

    config = {
        "run_id": run_id,
        "experiment": "document_ingestion_and_indexing",
        "document": {
            "filename": pdf_path.name,
            "source_path": str(pdf_path),
            "page_count": page_count,
        },
        "git_commit": git_commit(),
        "started_at": started_at.isoformat(),
        "processing_storage": str(processing_dir),
    }

    ingestion_report = {
        "run_id": run_id,
        "document_id": str(document.doc_id),
        "page_count": page_count,
        "indexed_records": len(records),
        "records_by_component_type": dict(sorted(type_counts.items())),
        "elapsed_seconds": round(elapsed, 3),
        "finished_at": finished_at.isoformat(),
    }

    summary = f"""# EDGAR Ingestion Experiment

## Run

- Run ID: `{run_id}`
- Git commit: `{config["git_commit"]}`
- Started: {started_at.isoformat()}
- Finished: {finished_at.isoformat()}

## Document

- File: `{pdf_path.name}`
- Pages: {page_count}

## Results

- Indexed records: {len(records)}
- Total processing time: {elapsed:.2f} seconds
- Average time per page: {elapsed / page_count:.2f} seconds

## Indexed records by component type

"""

    for component_type, count in sorted(type_counts.items()):
        summary += f"- {component_type}: {count}\n"

    summary += """
## Generated artifacts

- `config.json`: configuration and provenance of the run.
- `ingestion_report.json`: quantitative ingestion/indexing results.
- `summary.md`: human-readable experiment summary.
"""

    write_json(run_dir / "config.json", config)
    write_json(run_dir / "ingestion_report.json", ingestion_report)

    (run_dir / "summary.md").write_text(
        summary,
        encoding="utf-8",
    )

    print(f"Experiment completed: {run_id}")
    print(f"Report directory: {run_dir}")


if __name__ == "__main__":
    main()
