import logging
import time

from meddocass.datastore import Datastore, ScoredChunk

logger = logging.getLogger(__name__)


class Retriever:
    """get most relevant chunk."""

    def __init__(self, datastore: Datastore, top_k: int = 5, min_score: float = 0.0) -> None:
        self._datastore = datastore
        self._top_k = top_k
        self._min_score = min_score

    def retrieve(
        self, question: str, top_k: int | None = None, doc_ids: list[str] | None = None
    ) -> list[ScoredChunk]:
        query = " ".join(question.split())  # collapse whitespace and newlines
        if not query:
            raise ValueError("question must not be empty")
        hits = self._datastore.search(query, limit=top_k or self._top_k, doc_ids=doc_ids)
        kept = [h for h in hits if h.score >= self._min_score]
        return kept
