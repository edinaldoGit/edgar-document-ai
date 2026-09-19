import json
from pathlib import Path


INPUT_FILE = Path(
    "data/evaluation_dataset/metadata/document_inspection.json"
)


def main():
    documents = json.loads(INPUT_FILE.read_text(encoding="utf-8"))

    for document in documents:
        print("=" * 80)
        print(document["filename"])
        print("Pages:", document["page_count"])

        pages = document["pages"]

        most_images = sorted(
            pages,
            key=lambda page: page["image_count"],
            reverse=True,
        )[:5]

        most_text = sorted(
            pages,
            key=lambda page: page["text_chars"],
            reverse=True,
        )[:5]

        print("\nPages with more images:")
        for page in most_images:
            print(
                f'  page {page["page_number"]}: '
                f'{page["image_count"]} images'
            )

        print("\nPages with more text:")
        for page in most_text:
            print(
                f'  page {page["page_number"]}: '
                f'{page["text_chars"]} chars'
            )

        print()


if __name__ == "__main__":
    main()
