from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastembed import TextEmbedding
from langchain.chat_models import BaseChatModel, init_chat_model
from qdrant_client import QdrantClient

from meddocass.config import Settings, get_settings
from meddocass.datastore import Datastore
from meddocass.generator import Generator
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


def build_llm(model: str, temperature: float | None, settings: Settings) -> BaseChatModel:
    if not model.startswith("anthropic:"):
        raise ValueError(f"Unsupported LLM_MODEL={model!r};")
    if settings.anthropic_api_key is None:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to .env")
    return init_chat_model(
        model,
        api_key=settings.anthropic_api_key.get_secret_value(),
        temperature=temperature,
        timeout=settings.llm_timeout_s,
        max_retries=2,
        max_tokens=settings.llm_max_tokens,
    )


@lru_cache
def get_generator() -> Generator:
    s = get_settings()
    return Generator(llm=build_llm(s.llm_model, s.llm_temperature, s), model_name=s.llm_model)


GeneratorDep = Annotated[Generator, Depends(get_generator)]
