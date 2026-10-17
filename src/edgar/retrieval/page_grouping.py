from dataclasses import dataclass

from edgar.retrieval.results import RetrievedEvidence


@dataclass
class PageEvidence:
    page_number: int
    score: float
    components: list[RetrievedEvidence]


class PageEvidenceGrouper:
    def group(
        self,
        evidences: list[RetrievedEvidence],
        *,
        limit: int = 5,
    ) -> list[PageEvidence]:
        if limit <= 0:
            raise ValueError("Grouping limit must be positive.")

        grouped: dict[int, list[RetrievedEvidence]] = {}

        for evidence in evidences:
            grouped.setdefault(
                evidence.page_number,
                [],
            ).append(evidence)

        pages = []

        for page_number, components in grouped.items():
            score = self._page_score(components)

            pages.append(
                PageEvidence(
                    page_number=page_number,
                    score=score,
                    components=components,
                )
            )

        pages.sort(
            key=lambda page: page.score,
            reverse=True,
        )

        return pages[:limit]

    def _page_score(
        self,
        components: list[RetrievedEvidence],
    ) -> float:
        scores = sorted(
            (component.score for component in components),
            reverse=True,
        )

        if not scores:
            return 0.0

        score = scores[0]

        for extra_score in scores[1:3]:
            score += extra_score * 0.1

        return score
