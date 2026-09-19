import json
from pathlib import Path

import pymupdf


DATASET_DIR = Path("data/evaluation_dataset/originals")
OUTPUT_FILE = Path(
    "data/evaluation_dataset/metadata/document_inspection.json"
)


def inspect_pdf(path: Path) -> dict:
    with pymupdf.open(path) as pdf:
        pages = []

        for index, page in enumerate(pdf):
            text = page.get_text("text").strip()
            images = page.get_images(full=True)

            pages.append(
                {
                    "page_number": index + 1,
                    "text_chars": len(text),
                    "image_count": len(images),
                    "preview": text[:200],
                }
            )

        return {
            "filename": path.name,
            "page_count": len(pdf),
            "pages": pages,
        }


def main():
    results = []

    for pdf_path in sorted(DATASET_DIR.glob("*.pdf")):
        print("Inspecting:", pdf_path.name)
        results.append(inspect_pdf(pdf_path))

    OUTPUT_FILE.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("Generated:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
