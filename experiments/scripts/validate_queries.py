import json
from pathlib import Path


DOCUMENTS_FILE = Path(
    "data/evaluation_dataset/metadata/documents.json"
)

QUERIES_DIR = Path(
    "data/evaluation_dataset/queries"
)

VALID_COMPONENT_TYPES = {
    "plain_text",
    "figure",
    "table",
    "isolate_formula",
}

VALID_CATEGORIES = {
    "text_retrieval",
    "visual_evidence",
    "table_retrieval",
    "multimodal_reasoning",
}


def load_documents() -> dict:
    documents = json.loads(
        DOCUMENTS_FILE.read_text(
            encoding="utf-8"
        )
    )

    return {
        document["id"]: document
        for document in documents
    }


def validate_query_file(
    path: Path,
    documents: dict,
) -> list[str]:
    errors = []

    queries = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    ids = set()

    for query in queries:
        query_id = query["id"]

        if query_id in ids:
            errors.append(
                f"{path.name}: ID duplicado {query_id}"
            )

        ids.add(query_id)

        document_id = query["document"]

        if document_id not in documents:
            errors.append(
                f"{query_id}: documento inexistente "
                f"{document_id}"
            )
            continue

        document = documents[document_id]

        page = query["expected_evidence"]["page"]

        start = document["selected_pages"]["start"]
        end = document["selected_pages"]["end"]

        if not start <= page <= end:
            errors.append(
                f"{query_id}: página {page} fora do intervalo "
                f"{start}-{end}"
            )

        component_type = (
            query["expected_evidence"]["component_type"]
        )

        if component_type not in VALID_COMPONENT_TYPES:
            errors.append(
                f"{query_id}: componente inválido "
                f"{component_type}"
            )

        category = query.get(
            "evaluation_category"
        )

        if category not in VALID_CATEGORIES:
            errors.append(
                f"{query_id}: categoria inválida "
                f"{category}"
            )

    return errors


def main():
    documents = load_documents()

    errors = []

    for query_file in sorted(
        QUERIES_DIR.glob("*_queries.json")
    ):
        print(
            "Validando:",
            query_file.name,
        )

        errors.extend(
            validate_query_file(
                query_file,
                documents,
            )
        )

    print()

    if errors:
        print(
            "ERROS ENCONTRADOS:"
        )

        for error in errors:
            print("-", error)

        raise SystemExit(1)

    print(
        "Todas as consultas são válidas."
    )


if __name__ == "__main__":
    main()
