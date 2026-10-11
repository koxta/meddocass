import hashlib
from io import BytesIO
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from pypdf import PdfReader


class IndexingError(ValueError):
    """The file can't be indexed."""


class UnsupportedFileTypeError(IndexingError):
    """Only real .pdf and .txt files are accepted."""


class Chunk(BaseModel):
    doc_id: str
    filename: str
    page: int | None
    chunk_index: int
    text: str


class IndexedDocument(BaseModel):
    doc_id: str
    filename: str
    pages: int
    chunks: list[Chunk]


class Indexer:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def index(self, filename: str, data: bytes) -> IndexedDocument:
        doc_id = hashlib.sha256(data).hexdigest()[:16]
        pages = self._extract_pages(filename, data)
        chunks: list[Chunk] = []

        for page_number, text in pages:
            for piece in self._splitter.split_text(text):
                chunks.append(
                    Chunk(
                        doc_id=doc_id,
                        filename=filename,
                        page=page_number,
                        chunk_index=len(chunks),
                        text=piece,
                    )
                )

        if not chunks:
            raise IndexingError("This file can't be indexed.")

        return IndexedDocument(
            doc_id=doc_id, filename=filename, pages=len(pages), chunks=chunks
        )

    def _extract_pages(self, filename: str, data: bytes) -> list[tuple[int | None, str]]:
        suffix = Path(filename).suffix.lower()

        if suffix == ".pdf":
            if not data.startswith(b"%PDF"):
                raise UnsupportedFileTypeError("File is not a PDF")
            try:
                reader = PdfReader(BytesIO(data))
                return [
                    (n, page.extract_text() or "")
                    for n, page in enumerate(reader.pages, start=1)
                ]
            except (
                Exception
            ) as exc:
                # might be other error
                raise IndexingError(f"Unreadable PDF: {exc}") from exc
        if suffix == ".txt":
            return [(None, data.decode("utf-8", errors="replace"))]
        raise UnsupportedFileTypeError(f"Unsupported file type {suffix!r}; upload .pdf or .txt")
