import uuid

from fastembed import TextEmbedding
from pydantic import BaseModel
from qdrant_client import QdrantClient, models

from meddocass.indexer import Chunk


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    chunks: int


class Datastore:
    def __init__(self, client: QdrantClient, collection: str, embedder: TextEmbedding) -> None:
        self._client = client
        self._collection = collection
        self._embedder = embedder

    def ensure_collection(self) -> None:
        if self._client.collection_exists(self._collection):
            return
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(
                size=self._embedder.embedding_size, distance=models.Distance.COSINE
            ),
        )
        self._client.create_payload_index(
            self._collection, "doc_id", models.PayloadSchemaType.KEYWORD
        )
        self._client.create_payload_index(
            self._collection, "chunk_index", models.PayloadSchemaType.INTEGER
        )

    def add(self, chunks: list[Chunk]) -> None:
        for doc_id in {chunk.doc_id for chunk in chunks}:
            self.delete_document(doc_id)  # prevent duplicate
        vectors = self._embedder.passage_embed(
            [c.text for c in chunks]
        )
        
        points = [
            models.PointStruct(id=_point_id(c), vector=v.tolist(), payload=c.model_dump())
            for c, v in zip(chunks, vectors)
        ]
        self._client.upsert(collection_name=self._collection, points=points, wait=True)

    def search(self, query: str, limit: int, doc_ids: list[str] | None = None) -> list[ScoredChunk]:
        vector = next(iter(self._embedder.query_embed(query)))
        query_filter = (
            models.Filter(
                must=[models.FieldCondition(key="doc_id", match=models.MatchAny(any=doc_ids))]
            )
            if doc_ids
            else None
        )
        response = self._client.query_points(
            collection_name=self._collection,
            query=vector.tolist(),
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )
        return [ScoredChunk(chunk=Chunk(**p.payload), score=p.score) for p in response.points]

    def list_documents(self) -> list[DocumentInfo]:
        records, _next_page = self._client.scroll(
            collection_name=self._collection,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="chunk_index", match=models.MatchValue(value=0))]
            ),
            limit=1000,
            with_payload=["doc_id", "filename"],
        )
        return [
            DocumentInfo(
                doc_id=r.payload["doc_id"],
                filename=r.payload["filename"],
                chunks=self._count(r.payload["doc_id"]),
            )
            for r in records
        ]

    def delete_document(self, doc_id: str) -> None:
        self._client.delete(
            collection_name=self._collection,
            points_selector=models.FilterSelector(filter=_doc_filter(doc_id)),
            wait=True,
        )

    def _count(self, doc_id: str) -> int:
        return self._client.count(
            collection_name=self._collection, count_filter=_doc_filter(doc_id), exact=True
        ).count


def _doc_filter(doc_id: str) -> models.Filter:
    return models.Filter(
        must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
    )


def _point_id(chunk: Chunk) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{chunk.doc_id}:{chunk.chunk_index}"))
