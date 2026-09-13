from edgar.domain import ComponentType, DocumentComponent
from edgar.indexing.records import IndexRecord
from edgar.indexing.representation import build_indexable_text

ABSORBED_CHILD_TYPES = {
    ComponentType.FIGURE_CAPTION: ComponentType.FIGURE,
    ComponentType.TABLE_CAPTION: ComponentType.TABLE,
    ComponentType.TABLE_FOOTNOTE: ComponentType.TABLE,
}


def prepare_index_records(
    components: list[DocumentComponent],
) -> list[IndexRecord]:
    records = []

    for component in components:
        if _is_absorbed_by_parent(
            component,
            components,
        ):
            continue

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


def _is_absorbed_by_parent(
    component: DocumentComponent,
    components: list[DocumentComponent],
) -> bool:
    expected_parent_type = ABSORBED_CHILD_TYPES.get(component.component_type)

    if expected_parent_type is None:
        return False

    if component.parent_component_id is None:
        return False

    parent = next(
        (
            candidate
            for candidate in components
            if candidate.component_id == component.parent_component_id
        ),
        None,
    )

    if parent is None:
        return False

    return parent.component_type == expected_parent_type
