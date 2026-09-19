import hashlib
import json
from datetime import datetime
from pathlib import Path


DATASET_DIR = Path(
    "data/evaluation_dataset/processed"
)

OUTPUT_FILE = Path(
    "experiments/datasets/dataset_manifest.json"
)


def file_hash(path: Path) -> str:
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(8192),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def main():
    documents = []

    for pdf in sorted(DATASET_DIR.glob("*.pdf")):
        documents.append(
            {
                "filename": pdf.name,
                "size_bytes": pdf.stat().st_size,
                "sha256": file_hash(pdf),
            }
        )

    manifest = {
        "dataset_name": "EDGAR Evaluation Corpus",
        "version": "v1",
        "created_at": datetime.now().astimezone().isoformat(),
        "documents": documents,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("Generated:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
