import json
from pathlib import Path

import pymupdf


METADATA_FILE = Path(
    "data/evaluation_dataset/metadata/documents.json"
)

INPUT_DIR = Path(
    "data/evaluation_dataset/originals"
)

OUTPUT_DIR = Path(
    "data/evaluation_dataset/processed"
)


def create_subset(
    source: Path,
    output: Path,
    start_page: int,
    end_page: int,
) -> None:
    source_pdf = pymupdf.open(source)
    output_pdf = pymupdf.open()

    for page_number in range(
        start_page - 1,
        end_page,
    ):
        output_pdf.insert_pdf(
            source_pdf,
            from_page=page_number,
            to_page=page_number,
        )

    output_pdf.save(output)
    output_pdf.close()
    source_pdf.close()


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    documents = json.loads(
        METADATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    for document in documents:
        pages = document["selected_pages"]

        source = INPUT_DIR / document["original_file"]

        output = (
            OUTPUT_DIR /
            f'{document["id"]}.pdf'
        )

        print(
            f'Creating {output.name}: '
            f'pages {pages["start"]}-{pages["end"]}'
        )

        create_subset(
            source,
            output,
            pages["start"],
            pages["end"],
        )

    print()
    print("Curated dataset generated.")


if __name__ == "__main__":
    main()
