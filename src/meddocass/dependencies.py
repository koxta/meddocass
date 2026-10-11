from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from meddocass.config import Settings, get_settings
from meddocass.indexer import Indexer

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_indexer() -> Indexer:
    settings = get_settings()
    return Indexer(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)


IndexerDep = Annotated[Indexer, Depends(get_indexer)]
