from dataclasses import dataclass

from edgar.retrieval.results import RetrievedEvidence


@dataclass(frozen=True, slots=True)
class AnswerResult:
    question: str
    answer: str
    evidences: tuple[RetrievedEvidence, ...]
