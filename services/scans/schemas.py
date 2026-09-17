from pydantic import BaseModel, ConfigDict

from uuid import UUID

from datetime import datetime

class ScanFindingResponse(BaseModel):
    id: UUID
    scan_id: UUID
    file_path: str
    line_number: int
    category: str
    algorithm: str
    line_content: str

    is_false_positive: bool
    agent_explanation: str | None
    suggested_explanation: str | None

    model_config = ConfigDict(from_attributes=True)

class ScanResponse(BaseModel):
    id: UUID
    repository_id: UUID
    status: str
    created_at: datetime
    completed_at: datetime | None
    findings: list[ScanFindingResponse] = []

    model_config = ConfigDict(from_attributes=True)
