import json
from pathlib import Path

import pymupdf

INPUT_DIR = Path("data/evaluation_dataset/originals")
OUTPUT_FILE = Path("data/evaluation_dataset/metadata/toc.json")


def extract_toc(pdf_path: Path) -> dict:
    with pymupdf.open(pdf_path) as pdf:
        toc = pdf.get_toc()

        return {
            "filename": pdf_path.name,
            "page_count": len(pdf),
            "toc": [
                {
                    "level": item[0],
                    "title": item[1],
                    "page": item[2],
                }
                for item in toc
            ],
        }


def main():
    documents = []

    for pdf_path in sorted(INPUT_DIR.glob("*.pdf")):
        print("Extracting:", pdf_path.name)
        documents.append(extract_toc(pdf_path))

    OUTPUT_FILE.write_text(
        json.dumps(
            documents,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("Generated:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
