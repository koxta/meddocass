from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str

class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    pages: int
    chunks: int