import json
from pathlib import Path


FILE = Path(
    "data/evaluation_dataset/metadata/toc.json"
)


documents = json.loads(FILE.read_text(encoding="utf-8"))


for doc in documents:
    print("=" * 80)
    print(doc["filename"])
    print("Pages:", doc["page_count"])
    print()

    for item in doc["toc"]:
        if item["level"] <= 2:
            print(
                f'level={item["level"]} '
                f'page={item["page"]} '
                f'{item["title"]}'
            )

    print()
