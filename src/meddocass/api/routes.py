import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from meddocass.api.schemas import (
    AskRequest,
    DocumentSummary,
    HealthResponse,
    SearchRequest,
    SearchResponse,
)
from meddocass.datastore import DocumentInfo
from meddocass.dependencies import (
    DatastoreDep,
    GeneratorDep,
    IndexerDep,
    RetrieverDep,
    SettingsDep,
)
from meddocass.generator import Answer, GenerationError
from meddocass.indexer import IndexingError, UnsupportedFileTypeError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


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


@router.post("/ask")
def ask(body: AskRequest, retriever: RetrieverDep, generator: GeneratorDep) -> Answer:
    hits = retriever.retrieve(body.question, top_k=body.top_k, doc_ids=body.doc_ids)
    try:
        return generator.generate(body.question, hits)
    except GenerationError as exc:
        logger.warning("generation failed: %s", exc)
        raise HTTPException(502, "LLM failed to produce an answer. Please try again.") from exc
