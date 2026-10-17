import sys
from pathlib import Path

import pymupdf

if len(sys.argv) != 2:
    raise SystemExit("Uso: python inspect_curated_document.py <pdf>")


pdf_path = Path(sys.argv[1])


with pymupdf.open(pdf_path) as pdf:
    print("Documento:", pdf_path.name)
    print("Páginas:", len(pdf))
    print()

    for index, page in enumerate(pdf):
        text = page.get_text("text").strip()

        images = len(page.get_images(full=True))

        print("=" * 80)
        print("Página:", index + 1)
        print("Caracteres:", len(text))
        print("Objetos visuais:", images)
        print()

        print(text[:500].replace("\n", " "))
        print()
