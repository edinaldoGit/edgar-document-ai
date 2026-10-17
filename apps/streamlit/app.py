import json
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw

from edgar.application.bootstrap import build_retriever
from edgar.generation.prompts import build_grounded_answer_prompt
from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)
from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator
from edgar.retrieval.context import build_evidence_context

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPERIMENT_ROOT = REPO_ROOT / "storage" / "experiments" / "20260919_182500_corpus_ingestion"

QDRANT_PATH = EXPERIMENT_ROOT / "qdrant"

QUERY_DIR = REPO_ROOT / "data" / "evaluation_dataset" / "queries"

DOCUMENTS_PATH = REPO_ROOT / "experiments" / "datasets" / "documents.json"

QUERY_FILES = (
    "calculus_queries.json",
    "graphs_queries.json",
    "physics_queries.json",
    "statistics_queries.json",
)


@st.cache_data
def load_queries() -> dict[str, dict]:
    queries = {}

    for filename in QUERY_FILES:
        path = QUERY_DIR / filename
        data = json.loads(path.read_text(encoding="utf-8"))

        for query in data:
            queries[query["id"]] = query

    return queries


@st.cache_data
def load_document_ids() -> dict[str, str]:
    data = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))

    return {item["document_id"]: item["qdrant_doc_id"] for item in data}


@st.cache_resource
def get_retriever():
    return build_retriever(
        qdrant_path=QDRANT_PATH,
    )


@st.cache_resource
def get_generator():
    return ModalAnswerGenerator(
        client=ModalAnswerGenerationClient(),
        max_new_tokens=256,
    )


def resolve_crop_path(
    crop_ref: str | None,
) -> Path | None:
    if crop_ref is None:
        return None

    path = Path(crop_ref)

    if path.is_absolute():
        return path

    return EXPERIMENT_ROOT / path


def resolve_page_path(
    doc_id,
    page_number: int,
) -> Path:
    return EXPERIMENT_ROOT / "documents" / str(doc_id) / "pages" / f"page_{page_number:04d}.png"


def page_with_bbox(evidence) -> Image.Image | None:
    page_path = resolve_page_path(
        evidence.doc_id,
        evidence.page_number,
    )

    if not page_path.is_file():
        return None

    with Image.open(page_path) as source:
        image = source.convert("RGB")

    draw = ImageDraw.Draw(image)
    bbox = evidence.bbox

    draw.rectangle(
        (
            bbox.x1,
            bbox.y1,
            bbox.x2,
            bbox.y2,
        ),
        outline="red",
        width=8,
    )

    return image


def evidence_status(
    evidence,
    *,
    expected_doc_id: str,
    expected_page: int,
    expected_type: str,
) -> str:
    document_matches = str(evidence.doc_id) == expected_doc_id

    page_matches = evidence.page_number == expected_page

    type_matches = evidence.component_type.value == expected_type

    if document_matches and page_matches and type_matches:
        return "EXACT HIT"

    if document_matches and page_matches:
        return "PAGE HIT"

    if page_matches:
        return "PAGE NUMBER COLLISION"

    return "OTHER"


def first_matching_rank(
    evidences,
    *,
    expected_doc_id: str,
    expected_page: int,
    expected_type: str | None = None,
) -> int | None:
    for rank, evidence in enumerate(
        evidences,
        start=1,
    ):
        if str(evidence.doc_id) != expected_doc_id:
            continue

        if evidence.page_number != expected_page:
            continue

        if expected_type is not None and evidence.component_type.value != expected_type:
            continue

        return rank

    return None


def render_evidence(
    evidence,
    *,
    rank: int,
    expected_doc_id: str,
    expected_page: int,
    expected_type: str,
) -> None:
    status = evidence_status(
        evidence,
        expected_doc_id=expected_doc_id,
        expected_page=expected_page,
        expected_type=expected_type,
    )

    title = (
        f"Evidence {rank} | "
        f"página {evidence.page_number} | "
        f"{evidence.component_type.value} | "
        f"score={evidence.score:.4f} | "
        f"{status}"
    )

    with st.expander(
        title,
        expanded=(rank == 1),
    ):
        st.markdown(
            f"""
**component_id:** `{evidence.component_id}`\\
**doc_id:** `{evidence.doc_id}`\\
**page_index:** `{evidence.page_index}`\\
**page_number:** `{evidence.page_number}`\\
**component_type:** `{evidence.component_type.value}`\\
**bbox:** `({evidence.bbox.x1}, {evidence.bbox.y1}, {evidence.bbox.x2}, {evidence.bbox.y2})`\\
**score:** `{evidence.score:.6f}`\\
**gold status:** `{status}`
"""
        )

        st.markdown("**Representação indexada**")
        st.write(evidence.text)

        if evidence.text_extracted:
            st.markdown("**Texto extraído**")
            st.write(evidence.text_extracted)

        if evidence.visual_description:
            st.markdown("**Descrição visual**")
            st.write(evidence.visual_description)

        left, right = st.columns(2)

        with left:
            st.markdown("**Crop do componente**")

            crop_path = resolve_crop_path(evidence.crop_ref)

            if crop_path is not None and crop_path.is_file():
                st.image(
                    str(crop_path),
                    use_container_width=True,
                )
                st.caption(evidence.crop_ref)
            else:
                st.info("Este componente não possui crop disponível.")

        with right:
            st.markdown("**Página com bbox recuperada**")

            page_image = page_with_bbox(evidence)

            if page_image is not None:
                st.image(
                    page_image,
                    use_container_width=True,
                )
            else:
                st.warning("Imagem da página não encontrada.")


st.set_page_config(
    page_title="EDGAR - Validação",
    layout="wide",
)

st.title("EDGAR")
st.caption("Cliente de validação do snapshot oficial 20260919_182500_corpus_ingestion")

queries = load_queries()
document_ids = load_document_ids()
query_ids = sorted(queries)

selected_id = st.selectbox(
    "Query oficial",
    query_ids,
)

query = queries[selected_id]
gold = query["expected_evidence"]
expected_doc_id = document_ids[query["document"]]

st.markdown("### Consulta")

st.write(query["question"])

metadata_left, metadata_right = st.columns(2)

with metadata_left:
    st.markdown(
        f"""
**ID:** `{query["id"]}`\\
**Documento:** `{query["document"]}`\\
**Categoria:** `{query["evaluation_category"]}`\\
**Dificuldade:** `{query["difficulty"]}`
"""
    )

with metadata_right:
    st.markdown(
        f"""
**Gold document UUID:** `{expected_doc_id}`\\
**Gold page:** `{gold["page"]}`\\
**Source page:** `{gold["source_page"]}`\\
**Gold component:** `{gold["component_type"]}`
"""
    )

if gold.get("description"):
    st.markdown("**Descrição da evidência gold**")
    st.write(gold["description"])

with st.expander(
    "Resposta de referência",
):
    st.write(query["reference_answer"])

limit = st.slider(
    "Top-k para inspeção",
    min_value=1,
    max_value=20,
    value=20,
)

retrieval_key = (
    selected_id,
    limit,
)

if st.button(
    "Recuperar evidências",
    type="primary",
):
    with st.spinner("Executando retrieval..."):
        evidences = tuple(
            get_retriever().retrieve(
                query["question"],
                limit=limit,
            )
        )

    st.session_state["retrieval_key"] = retrieval_key

    st.session_state["retrieved_evidences"] = evidences

    st.session_state.pop(
        "generated_answer",
        None,
    )


current_key = st.session_state.get("retrieval_key")

evidences = st.session_state.get("retrieved_evidences")

if current_key == retrieval_key and evidences is not None:
    page_rank = first_matching_rank(
        evidences,
        expected_doc_id=expected_doc_id,
        expected_page=gold["page"],
    )

    component_rank = first_matching_rank(
        evidences,
        expected_doc_id=expected_doc_id,
        expected_page=gold["page"],
        expected_type=gold["component_type"],
    )

    st.markdown("### Resultado do retrieval")

    summary_left, summary_middle, summary_right = st.columns(3)

    with summary_left:
        st.metric(
            "Evidências",
            len(evidences),
        )

    with summary_middle:
        st.metric(
            "Primeiro Page Hit",
            (page_rank if page_rank is not None else "MISS"),
        )

    with summary_right:
        st.metric(
            "Primeiro Component Hit",
            (component_rank if component_rank is not None else "MISS"),
        )

    if component_rank is not None:
        st.success(f"O componente gold foi recuperado no rank {component_rank}.")
    elif page_rank is not None:
        st.warning(
            "A página gold foi recuperada, mas o tipo de componente gold não apareceu neste top-k."
        )
    else:
        st.error("A página gold não apareceu neste top-k.")

    st.caption(
        "A marcação acima reproduz o critério "
        "estrito atual de página + tipo. "
        "A inspeção visual deve verificar "
        "também componentes semanticamente "
        "equivalentes."
    )

    st.markdown("### Evidências")

    for rank, evidence in enumerate(
        evidences,
        start=1,
    ):
        render_evidence(
            evidence,
            rank=rank,
            expected_doc_id=expected_doc_id,
            expected_page=gold["page"],
            expected_type=gold["component_type"],
        )

    st.markdown("### Geração opcional")

    st.caption(
        "Esta geração serve apenas para "
        "validação funcional do cliente. "
        "Ela não substitui o run oficial "
        "de geração do experimento."
    )

    if st.button("Gerar resposta com estas evidências"):
        evidence_context = build_evidence_context(evidences)

        if evidence_context is None:
            st.warning("Não há evidências suficientes para gerar uma resposta.")
        else:
            prompt = build_grounded_answer_prompt(
                question=query["question"],
                evidence_context=(evidence_context),
            )

            with st.spinner("Gerando resposta..."):
                answer = get_generator().generate(prompt=prompt).strip()

            st.session_state["generated_answer"] = answer

    answer = st.session_state.get("generated_answer")

    if answer:
        st.markdown("**Resposta gerada**")
        st.write(answer)
