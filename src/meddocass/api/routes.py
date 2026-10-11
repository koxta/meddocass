from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from meddocass.api.schemas import HealthResponse
from meddocass.config import Settings
from meddocass.dependencies import get_indexer, get_settings
from meddocass.indexer import IndexedDocument, Indexer, IndexingError, UnsupportedFileTypeError

router = APIRouter()


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/index")
def index_document(
    file: UploadFile,
    indexer: Annotated[Indexer, Depends(get_indexer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> IndexedDocument:
    data = file.file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB")

    try:
        return indexer.index(file.filename or "upload", data)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(415, str(exc)) from exc
    except IndexingError as exc:
        raise HTTPException(422, str(exc)) from exc
