import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pymupdf
import streamlit as st
from PIL import Image, ImageDraw

from edgar.application.client_background import (
    IngestionProgress,
    answer_client_question,
    process_client_document,
)
from edgar.domain import Document

CLIENT_STORAGE = Path("storage/client_app")


def move_page(delta: int) -> None:
    document = st.session_state.get("edgar_document")
    if document is None:
        return

    current = int(st.session_state.get("edgar_page_number", 1))
    st.session_state["edgar_page_number"] = max(
        1,
        min(current + delta, document.page_count),
    )


st.set_page_config(
    page_title="EDGAR | Chat com PDF",
    page_icon="📚",
    layout="wide",
)

st.title("EDGAR")
st.caption("Análise inteligente de documentos PDF")

pdf_column, chat_column = st.columns(
    [1.2, 1],
    gap="large",
)

with chat_column:
    st.subheader("Chat com o documento")

    uploaded = st.file_uploader(
        "Selecione um documento PDF",
        type=["pdf"],
        accept_multiple_files=False,
        disabled=(
            st.session_state.get("edgar_ingestion_future") is not None
            or st.session_state.get("edgar_answer_future") is not None
        ),
    )

if uploaded is None:
    session = st.session_state.pop("edgar_client_session", None)
    if session is not None:
        session.close()

    for key in (
        "edgar_upload_digest",
        "edgar_document",
        "edgar_storage_root",
        "edgar_page_number",
        "edgar_ingested",
        "edgar_indexed_count",
        "edgar_ingestion_future",
        "edgar_ingestion_executor",
        "edgar_ingestion_error",
        "edgar_ingestion_progress",
        "edgar_answer_future",
        "edgar_answer_executor",
        "edgar_chat_history",
        "edgar_chat_error",
        "edgar_selected_evidence",
    ):
        st.session_state.pop(key, None)

    with pdf_column:
        st.subheader("Leitor de PDF")
        st.info("O documento aparecerá aqui após o upload.")

    with chat_column:
        st.info("Envie um PDF para começar.")

    st.stop()

pdf_bytes = uploaded.getvalue()

if not pdf_bytes:
    st.error("O arquivo enviado está vazio.")
    st.stop()

try:
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        if pdf.needs_pass:
            st.error("PDFs protegidos por senha não são suportados.")
            st.stop()

        page_count = pdf.page_count

except Exception as error:
    st.error(f"Não foi possível abrir o PDF: {error}")
    st.stop()

digest = hashlib.sha256(pdf_bytes).hexdigest()

if st.session_state.get("edgar_upload_digest") != digest:
    previous_session = st.session_state.pop(
        "edgar_client_session",
        None,
    )

    if previous_session is not None:
        previous_session.close()

    storage_root = CLIENT_STORAGE / str(uuid4())
    storage_root.mkdir(parents=True, exist_ok=True)

    source_path = storage_root / "uploaded.pdf"
    source_path.write_bytes(pdf_bytes)

    document = Document(
        filename=uploaded.name,
        source_ref=str(source_path.resolve()),
        page_count=page_count,
    )

    st.session_state["edgar_upload_digest"] = digest
    st.session_state["edgar_document"] = document
    st.session_state["edgar_storage_root"] = str(storage_root)
    st.session_state["edgar_page_number"] = 1
    st.session_state["edgar_ingested"] = False
    st.session_state["edgar_indexed_count"] = 0
    st.session_state["edgar_ingestion_error"] = None
    st.session_state["edgar_chat_history"] = []
    st.session_state["edgar_chat_error"] = None
    st.session_state["edgar_selected_evidence"] = None

document = st.session_state["edgar_document"]


def select_evidence(evidence) -> None:
    st.session_state["edgar_page_number"] = evidence.page_number
    st.session_state["edgar_selected_evidence"] = evidence


@st.fragment(run_every="2s")
def show_ingestion_status() -> None:
    future = st.session_state.get("edgar_ingestion_future")

    if future is None:
        return

    if not future.done():
        progress = st.session_state.get("edgar_ingestion_progress")

        if progress is None:
            st.info("Iniciando processamento...")
        else:
            stage, completed, total = progress.snapshot()

            if stage == "rasterizing":
                st.info("Preparando as páginas do PDF...")

            elif stage == "processing" and total > 0:
                st.progress(min(completed / total, 1.0))
                st.caption(f"Páginas processadas: {completed} de {total}")

            elif stage == "indexing":
                st.info("Páginas analisadas. Gerando embeddings e salvando no Qdrant...")

            else:
                st.info("Iniciando processamento...")

        st.caption("Você pode continuar navegando pelo PDF.")
        return

    executor = st.session_state.pop("edgar_ingestion_executor", None)
    st.session_state.pop("edgar_ingestion_future", None)
    st.session_state.pop("edgar_ingestion_progress", None)

    if executor is not None:
        executor.shutdown(wait=False)

    try:
        indexed_count = future.result()
    except Exception as error:
        st.session_state["edgar_ingested"] = False
        st.session_state["edgar_indexed_count"] = 0
        st.session_state["edgar_ingestion_error"] = f"{type(error).__name__}: {error}"
    else:
        st.session_state["edgar_indexed_count"] = indexed_count
        st.session_state["edgar_ingested"] = True
        st.session_state["edgar_ingestion_error"] = None

    st.rerun()


with chat_column:
    st.caption(f"Arquivo: {document.filename} | {document.page_count} páginas")

    if st.session_state.get("edgar_ingestion_future") is not None:
        show_ingestion_status()

    elif st.session_state.get("edgar_ingested", False):
        count = st.session_state["edgar_indexed_count"]
        st.success(f"Documento processado! {count} registros indexados.")
        st.info("O chat será conectado na próxima etapa.")

    else:
        error = st.session_state.get("edgar_ingestion_error")
        if error:
            st.error(f"Falha no processamento: {error}")

        st.info(
            "Documento carregado. Inicie o processamento para disponibilizar o conteúdo ao EDGAR."
        )

        if st.button(
            "Processar documento",
            type="primary",
            use_container_width=True,
        ):
            storage_root = Path(st.session_state["edgar_storage_root"])

            progress = IngestionProgress()

            executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="edgar-ingestion",
            )

            try:
                future = executor.submit(
                    process_client_document,
                    document=document,
                    storage_root=storage_root,
                    progress=progress,
                )
            except Exception:
                executor.shutdown(wait=False)
                raise

            st.session_state["edgar_ingestion_executor"] = executor
            st.session_state["edgar_ingestion_future"] = future
            st.session_state["edgar_ingestion_progress"] = progress
            st.session_state["edgar_ingestion_error"] = None

            st.rerun()


@st.fragment(run_every="2s")
def show_answer_status() -> None:
    future = st.session_state.get("edgar_answer_future")

    if future is None:
        return

    if not future.done():
        st.info("O EDGAR está buscando evidências e gerando a resposta...")
        return

    executor = st.session_state.pop("edgar_answer_executor", None)
    st.session_state.pop("edgar_answer_future", None)

    if executor is not None:
        executor.shutdown(wait=False)

    try:
        result = future.result()
    except Exception as error:
        st.session_state["edgar_chat_error"] = f"{type(error).__name__}: {error}"
    else:
        st.session_state["edgar_chat_history"].append(
            {
                "role": "assistant",
                "content": result.answer,
                "evidences": result.evidences,
            }
        )
        st.session_state["edgar_chat_error"] = None

    st.rerun()


with chat_column:
    if st.session_state.get("edgar_ingested", False):
        st.divider()
        st.subheader("Converse com o PDF")

        history = st.session_state.setdefault("edgar_chat_history", [])

        for message_index, message in enumerate(history):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                evidences = message.get("evidences", ())

                if evidences:
                    with st.expander(f"Evidências recuperadas ({len(evidences)})"):
                        for rank, evidence in enumerate(evidences, start=1):
                            st.button(
                                f"📍 Evidência {rank} · "
                                f"Página {evidence.page_number} · "
                                f"{evidence.component_type.value}",
                                key=(
                                    f"edgar_evidence_{message_index}_{rank}_{evidence.component_id}"
                                ),
                                on_click=select_evidence,
                                args=(evidence,),
                                use_container_width=True,
                            )

                            st.caption(evidence.text[:200])

        if st.session_state.get("edgar_chat_error"):
            st.error(st.session_state["edgar_chat_error"])

        pending = st.session_state.get("edgar_answer_future")

        if pending is not None:
            show_answer_status()

        question = st.chat_input(
            "Faça uma pergunta sobre o PDF...",
            disabled=pending is not None,
        )

        if question and question.strip():
            st.session_state["edgar_chat_history"].append(
                {
                    "role": "user",
                    "content": question.strip(),
                }
            )
            st.session_state["edgar_chat_error"] = None

            executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="edgar-answer",
            )

            try:
                future = executor.submit(
                    answer_client_question,
                    question=question.strip(),
                    document=document,
                    storage_root=Path(st.session_state["edgar_storage_root"]),
                    limit=8,
                )
            except Exception:
                executor.shutdown(wait=False)
                raise

            st.session_state["edgar_answer_executor"] = executor
            st.session_state["edgar_answer_future"] = future

            st.rerun()

with pdf_column:
    st.subheader("Leitor de PDF")

    current_page = st.session_state["edgar_page_number"]

    previous_column, number_column, next_column = st.columns(
        [1, 1.2, 1],
    )

    with previous_column:
        st.button(
            "◀ Anterior",
            disabled=current_page <= 1,
            on_click=move_page,
            args=(-1,),
            use_container_width=True,
        )

    with number_column:
        st.number_input(
            "Página",
            min_value=1,
            max_value=document.page_count,
            step=1,
            key="edgar_page_number",
        )

    with next_column:
        st.button(
            "Próxima ▶",
            disabled=current_page >= document.page_count,
            on_click=move_page,
            args=(1,),
            use_container_width=True,
        )

    page_number = int(st.session_state["edgar_page_number"])

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:
        page = pdf[page_number - 1]
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(1.5, 1.5),
            alpha=False,
        )

    rendered_image = pixmap.tobytes("png")

    selected = st.session_state.get("edgar_selected_evidence")

    if (
        selected is not None
        and selected.doc_id == document.doc_id
        and selected.page_number == page_number
    ):
        indexed_page_path = (
            Path(st.session_state["edgar_storage_root"])
            / "documents"
            / str(document.doc_id)
            / "pages"
            / f"page_{page_number:04d}.png"
        )

        if indexed_page_path.is_file():
            with Image.open(indexed_page_path) as indexed_page:
                source_width, source_height = indexed_page.size

            scale_x = pixmap.width / source_width
            scale_y = pixmap.height / source_height

            bbox = selected.bbox

            left = max(0, min(pixmap.width - 1, round(bbox.x1 * scale_x)))
            top = max(0, min(pixmap.height - 1, round(bbox.y1 * scale_y)))
            right = max(left, min(pixmap.width - 1, round(bbox.x2 * scale_x)))
            bottom = max(top, min(pixmap.height - 1, round(bbox.y2 * scale_y)))

            image = Image.frombytes(
                "RGB",
                (pixmap.width, pixmap.height),
                pixmap.samples,
            )

            draw = ImageDraw.Draw(image)
            draw.rectangle(
                (left, top, right, bottom),
                outline="red",
                width=max(3, pixmap.width // 180),
            )

            rendered_image = image

            st.caption(
                f"📍 Evidência selecionada: "
                f"{selected.component_type.value} "
                f"· Página {selected.page_number}"
            )
        else:
            st.warning(
                "Imagem da página indexada não encontrada. Não foi possível destacar a evidência."
            )

    st.image(
        rendered_image,
        use_container_width=True,
    )
