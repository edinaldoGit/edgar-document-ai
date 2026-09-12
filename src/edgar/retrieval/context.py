from edgar.retrieval.results import RetrievedEvidence


def build_evidence_context(
    evidences: list[RetrievedEvidence],
) -> str | None:
    if not evidences:
        return None

    blocks = []

    for rank, evidence in enumerate(
        evidences,
        start=1,
    ):
        bbox = evidence.bbox

        metadata = (
            f"Evidence {rank} | "
            f"page={evidence.page_number} | "
            f"type={evidence.component_type.value} | "
            f"score={evidence.score:.4f} | "
            f"bbox=({bbox.x1},{bbox.y1},{bbox.x2},{bbox.y2})"
        )

        blocks.append(f"{metadata}\n{evidence.text}")

    return "\n\n".join(blocks)
