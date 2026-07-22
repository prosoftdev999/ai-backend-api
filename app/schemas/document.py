import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    stored_filename: str
    content_type: str
    file_size: int
    status: str
    error_message: str | None
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


class DocumentTaskResponse(BaseModel):
    document: DocumentResponse
    task_id: str
