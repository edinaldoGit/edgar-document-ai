from uuid import uuid4

from edgar.domain import BoundingBox, ComponentType, DocumentComponent
from edgar.ingestion.caption_association import associate_figure_captions


def test_associate_figure_caption_sets_parent_component_id():
    doc_id = uuid4()

    figure = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=466,
            y1=1068,
            x2=754,
            y2=1259,
        ),
    )

    caption = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FIGURE_CAPTION,
        bbox=BoundingBox(
            x1=384,
            y1=1276,
            x2=833,
            y2=1309,
        ),
    )

    components = [figure, caption]

    result = associate_figure_captions(components)

    assert result is components
    assert caption.parent_component_id == figure.component_id
    assert figure.parent_component_id is None


def test_unmatched_figure_caption_keeps_parent_empty():
    doc_id = uuid4()

    caption = DocumentComponent(
        doc_id=doc_id,
        page_index=0,
        component_type=ComponentType.FIGURE_CAPTION,
        bbox=BoundingBox(
            x1=100,
            y1=100,
            x2=300,
            y2=130,
        ),
    )

    associate_figure_captions([caption])

    assert caption.parent_component_id is None
