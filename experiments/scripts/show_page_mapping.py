from pathlib import Path
import sys


if len(sys.argv) != 4:
    raise SystemExit(
        "Uso: python show_page_mapping.py <inicio> <fim> <pagina_original>"
    )


start = int(sys.argv[1])
end = int(sys.argv[2])
original = int(sys.argv[3])


if not start <= original <= end:
    print("Página fora do intervalo selecionado.")
else:
    dataset_page = original - start + 1

    print(
        f"Página original: {original}"
    )

    print(
        f"Página no dataset: {dataset_page}"
    )
