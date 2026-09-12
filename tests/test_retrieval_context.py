from uuid import uuid4

from edgar.domain import BoundingBox, ComponentType
from edgar.retrieval.context import build_evidence_context
from edgar.retrieval.results import RetrievedEvidence


def evidence(
    *,
    page_index,
    component_type,
    text,
    score,
    bbox,
):
    return RetrievedEvidence(
        component_id=uuid4(),
        doc_id=uuid4(),
        page_index=page_index,
        component_type=component_type,
        bbox=bbox,
        text=text,
        score=score,
    )


def test_builds_ranked_traceable_evidence_context():
    first = evidence(
        page_index=2,
        component_type=ComponentType.PLAIN_TEXT,
        text="O OCR é usado como fallback.",
        score=0.91234,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=300,
            y2=120,
        ),
    )

    second = evidence(
        page_index=4,
        component_type=ComponentType.TABLE,
        text="Columns: Critério | EDGAR",
        score=0.80123,
        bbox=BoundingBox(
            x1=100,
            y1=200,
            x2=800,
            y2=600,
        ),
    )

    result = build_evidence_context(
        [
            first,
            second,
        ]
    )

    assert result == (
        "Evidence 1 | page=3 | type=plain_text | "
        "score=0.9123 | bbox=(10,20,300,120)\n"
        "O OCR é usado como fallback.\n\n"
        "Evidence 2 | page=5 | type=table | "
        "score=0.8012 | bbox=(100,200,800,600)\n"
        "Columns: Critério | EDGAR"
    )


def test_returns_none_without_evidence():
    assert build_evidence_context([]) is None
