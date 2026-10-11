from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from meddocass.api.schemas import DocumentSummary, HealthResponse, SearchRequest, SearchResponse
from meddocass.config import Settings
from meddocass.datastore import DocumentInfo
from meddocass.dependencies import (
    DatastoreDep,
    IndexerDep,
    RetrieverDep,
    SettingsDep,
    get_indexer,
    get_settings,
)
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


@router.post("/documents", status_code=201)
def upload_document(
    file: UploadFile, indexer: IndexerDep, datastore: DatastoreDep, settings: SettingsDep
) -> DocumentSummary:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"File larger than {settings.max_upload_mb} MB")
    if not data:
        raise HTTPException(422, "Empty file")
    filename = Path(file.filename or "upload").name
    try:
        doc = indexer.index(filename, data)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(415, str(exc)) from exc
    except IndexingError as exc:
        raise HTTPException(422, str(exc)) from exc
    datastore.add(doc.chunks)
    return DocumentSummary(
        doc_id=doc.doc_id, filename=doc.filename, pages=doc.pages, chunks=len(doc.chunks)
    )


@router.get("/documents")
def list_documents(datastore: DatastoreDep) -> list[DocumentInfo]:
    return datastore.list_documents()


@router.post("/search")
def search(body: SearchRequest, retriever: RetrieverDep) -> SearchResponse:
    return SearchResponse(
        results=retriever.retrieve(body.query, top_k=body.top_k, doc_ids=body.doc_ids)
    )
