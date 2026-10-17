from edgar.retrieval.results import RetrievedEvidence


class EvidenceReranker:
    def rerank(
        self,
        evidences: list[RetrievedEvidence],
        *,
        question_type: str,
        limit: int = 5,
    ) -> list[RetrievedEvidence]:
        if limit <= 0:
            raise ValueError("Reranking limit must be positive.")

        ranked = sorted(
            evidences,
            key=lambda evidence: self._score(
                evidence,
                question_type,
            ),
            reverse=True,
        )

        return ranked[:limit]

    def _score(
        self,
        evidence: RetrievedEvidence,
        question_type: str,
    ) -> float:
        score = evidence.score

        component_type = evidence.component_type.value

        if question_type == "figure":
            if component_type == "figure":
                score *= 1.10
            elif component_type == "figure_caption":
                score *= 1.05

        elif question_type == "table":
            if component_type == "table":
                score *= 1.10
            elif component_type == "table_caption":
                score *= 1.05

        elif question_type == "formula":
            if component_type == "isolate_formula":
                score *= 1.10

        elif question_type == "text":
            if component_type == "plain_text":
                score *= 1.10

        return score
