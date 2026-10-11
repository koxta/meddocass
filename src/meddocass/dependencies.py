from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from meddocass.config import Settings, get_settings
from meddocass.datastore import Datastore
from meddocass.indexer import Indexer
from meddocass.retriever import Retriever

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_indexer() -> Indexer:
    settings = get_settings()
    return Indexer(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)


IndexerDep = Annotated[Indexer, Depends(get_indexer)]


@lru_cache
def get_datastore() -> Datastore:
    settings = get_settings()
    datastore = Datastore(
        client=QdrantClient(url=settings.qdrant_url),
        collection=settings.qdrant_collection,
        embedder=TextEmbedding(
            model_name=settings.embedding_model, cache_dir=settings.embedding_cache_dir
        ),
    )
    datastore.ensure_collection()
    return datastore


DatastoreDep = Annotated[Datastore, Depends(get_datastore)]


@lru_cache
def get_retriever() -> Retriever:
    s = get_settings()
    return Retriever(get_datastore(), top_k=s.top_k, min_score=s.min_score)


RetrieverDep = Annotated[Retriever, Depends(get_retriever)]