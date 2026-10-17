import json
from pathlib import Path

INPUT = Path("data/evaluation_dataset/metadata/document_inspection.json")


documents = json.loads(INPUT.read_text(encoding="utf-8"))


for document in documents:
    print("=" * 80)
    print(document["filename"])

    pages = sorted(
        document["pages"],
        key=lambda x: x["image_count"],
        reverse=True,
    )[:10]

    for page in pages:
        print(f"page={page['page_number']} images={page['image_count']} text={page['text_chars']}")
        print("preview:", page["preview"][:100].replace("\n", " "))
        print()
