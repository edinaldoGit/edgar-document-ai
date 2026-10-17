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

DATASET_FILE = PROJECT_ROOT / "data" / "evaluation_dataset" / "metadata" / "documents.json"

PDF_DIR = PROJECT_ROOT / "data" / "evaluation_dataset" / "processed"

RUNS_ROOT = PROJECT_ROOT / "experiments" / "runs"

STORAGE_ROOT = PROJECT_ROOT / "storage" / "experiments"


def git_commit():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def write_json(path, data):
    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main():
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")

    run_id = f"{timestamp}_corpus_ingestion"

    run_dir = RUNS_ROOT / run_id
    storage_dir = STORAGE_ROOT / run_id

    run_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    storage_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    documents = json.loads(DATASET_FILE.read_text(encoding="utf-8"))

    runner = build_indexing_runner(
        storage_root=storage_dir,
        qdrant_path=storage_dir / "qdrant",
    )

    results = []

    total_start = perf_counter()

    for item in documents:
        pdf_path = PDF_DIR / f"{item['id']}.pdf"

        print(
            "Processing:",
            pdf_path.name,
        )

        with pymupdf.open(pdf_path) as pdf:
            page_count = pdf.page_count

        document = Document(
            filename=pdf_path.name,
            source_ref=str(pdf_path),
            page_count=page_count,
            doc_id=uuid4(),
        )

        start = perf_counter()

        records = runner.run(document)

        elapsed = perf_counter() - start

        counts = Counter(record.record.component_type.value for record in records)

        results.append(
            {
                "document_id": item["id"],
                "filename": pdf_path.name,
                "pages": page_count,
                "indexed_records": len(records),
                "elapsed_seconds": round(
                    elapsed,
                    3,
                ),
                "records_by_component_type": dict(sorted(counts.items())),
            }
        )

    total_elapsed = perf_counter() - total_start

    report = {
        "run_id": run_id,
        "experiment": "corpus_ingestion_and_indexing",
        "git_commit": git_commit(),
        "documents": len(results),
        "total_elapsed_seconds": round(
            total_elapsed,
            3,
        ),
        "results": results,
    }

    write_json(
        run_dir / "corpus_ingestion_report.json",
        report,
    )

    summary = [
        "# EDGAR Corpus Ingestion Experiment",
        "",
        f"- Run ID: `{run_id}`",
        f"- Git commit: `{report['git_commit']}`",
        f"- Documents processed: {len(results)}",
        f"- Total time: {total_elapsed:.2f}s",
        "",
        "## Documents",
        "",
    ]

    for result in results:
        summary.extend(
            [
                f"### {result['document_id']}",
                "",
                f"- Pages: {result['pages']}",
                f"- Records: {result['indexed_records']}",
                f"- Time: {result['elapsed_seconds']}s",
                "",
            ]
        )

    (run_dir / "summary.md").write_text(
        "\n".join(summary),
        encoding="utf-8",
    )

    print()
    print("Experiment completed:")
    print(run_id)


if __name__ == "__main__":
    main()
