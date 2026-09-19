import json
from pathlib import Path

import pymupdf


METADATA_FILE = Path(
    "data/evaluation_dataset/metadata/documents.json"
)

PDF_DIR = Path(
    "data/evaluation_dataset/processed"
)

OUTPUT_JSON = Path(
    "experiments/datasets/corpus_report.json"
)

OUTPUT_MD = Path(
    "experiments/datasets/corpus_summary.md"
)


def analyze_pdf(path: Path) -> dict:
    with pymupdf.open(path) as pdf:
        total_images = 0
        total_text_chars = 0

        for page in pdf:
            total_images += len(page.get_images(full=True))
            total_text_chars += len(
                page.get_text("text")
            )

        return {
            "pages": len(pdf),
            "images": total_images,
            "text_characters": total_text_chars,
            "file_size_mb": round(
                path.stat().st_size / (1024 * 1024),
                2,
            ),
        }


def main():
    documents = json.loads(
        METADATA_FILE.read_text(
            encoding="utf-8"
        )
    )

    report = []

    for document in documents:
        pdf_path = (
            PDF_DIR /
            f'{document["id"]}.pdf'
        )

        print(
            "Analyzing:",
            pdf_path.name,
        )

        analysis = analyze_pdf(pdf_path)

        report.append(
            {
                "id": document["id"],
                "title": document["title"],
                "domain": document["domain"],
                "source_file": document["original_file"],
                "selected_pages": document["selected_pages"],
                "selection_reason": document["selection_reason"],
                "statistics": analysis,
            }
        )

    OUTPUT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    markdown = [
        "# Corpus Experimental de Avaliação do EDGAR",
        "",
        "## Documentos Avaliados",
        "",
        "O corpus experimental foi construído a partir de materiais "
        "didáticos em formato PDF, selecionados por apresentarem "
        "elementos multimodais relevantes para avaliação da arquitetura "
        "EDGAR.",
        "",
        "Os documentos foram previamente curados por meio da seleção "
        "de intervalos de páginas contendo maior relevância para a "
        "recuperação de informações textuais e visuais.",
        "",
    ]

    for item in report:
        stats = item["statistics"]

        markdown.extend(
            [
                f'## {item["title"]}',
                "",
                f'- Identificador: `{item["id"]}`',
                f'- Domínio: {item["domain"]}',
                f'- Documento original: `{item["source_file"]}`',
                f'- Intervalo selecionado: páginas '
                f'{item["selected_pages"]["start"]}-'
                f'{item["selected_pages"]["end"]}',
                f'- Quantidade de páginas: {stats["pages"]}',
                f'- Objetos visuais detectados no PDF: '
                f'{stats["images"]}',
                f'- Quantidade de caracteres textuais extraídos: '
                f'{stats["text_characters"]}',
                f'- Tamanho do arquivo: {stats["file_size_mb"]} MB',
                "",
                "### Justificativa da seleção",
                "",
                item["selection_reason"],
                "",
            ]
        )

    OUTPUT_MD.write_text(
        "\n".join(markdown),
        encoding="utf-8",
    )

    print()
    print("Generated:")
    print(OUTPUT_JSON)
    print(OUTPUT_MD)


if __name__ == "__main__":
    main()
