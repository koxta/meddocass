from pydantic import BaseModel, ConfigDict, Field

from meddocass.datastore import ScoredChunk


class HealthResponse(BaseModel):
    status: str

class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    pages: int
    chunks: int

class SearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)# "   " becomes ""

    query: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    doc_ids: list[str] | None = None


class SearchResponse(BaseModel):
    results: list[ScoredChunk]