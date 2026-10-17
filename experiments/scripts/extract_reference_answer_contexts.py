import json
from pathlib import Path

import pymupdf

QUERIES_DIR = Path("data/evaluation_dataset/queries")

PDF_DIR = Path("data/evaluation_dataset/processed")

OUTPUT_FILE = Path("experiments/datasets/reference_answer_contexts.json")


def main() -> None:
    results = []

    for query_file in sorted(QUERIES_DIR.glob("*_queries.json")):
        queries = json.loads(query_file.read_text(encoding="utf-8"))

        for query in queries:
            document_id = query["document"]
            page_number = query["expected_evidence"]["page"]

            pdf_path = PDF_DIR / f"{document_id}.pdf"

            with pymupdf.open(pdf_path) as pdf:
                page = pdf[page_number - 1]

                page_text = " ".join(page.get_text().split())

            results.append(
                {
                    "id": query["id"],
                    "document": document_id,
                    "question": query["question"],
                    "expected_page": page_number,
                    "expected_component_type": query["expected_evidence"]["component_type"],
                    "expected_description": query["expected_evidence"]["description"],
                    "page_text": page_text,
                }
            )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Contextos extraídos: {len(results)}")
    print(f"Arquivo: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
