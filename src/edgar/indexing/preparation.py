from edgar.domain import DocumentComponent
from edgar.indexing.records import IndexRecord
from edgar.indexing.representation import build_indexable_text


def prepare_index_records(
    components: list[DocumentComponent],
) -> list[IndexRecord]:
    records = []

    for component in components:
        text = build_indexable_text(
            component,
            components,
        )

        if text is None:
            continue

        records.append(
            IndexRecord(
                component_id=component.component_id,
                doc_id=component.doc_id,
                page_index=component.page_index,
                component_type=component.component_type,
                bbox=component.bbox,
                text=text,
                text_extracted=component.text_extracted,
                visual_description=component.visual_description,
                crop_ref=component.crop_ref,
            )
        )

    return records
