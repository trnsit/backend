from pydantic import BaseModel

# Define the exact data fields the scanner produces
class FindingAuditRequest(BaseModel):
    file_path: str
    line_number: int
    category: str
    algorithm: str
    matched_line: str
    code_context: str

# Guarantee a typed response with boolean false-positive verdict, agent reasoning, and migration advice
class FindingAuditResponse(BaseModel):
    is_false_positive: bool
    agent_explanation: str
    suggested_explanation: str

class BatchAuditRequest(BaseModel):
    findings: list[FindingAuditRequest]

# Prepares us to audit an entire scan in a single network request
class BatchAuditResponse(BaseModel):
    results: list[FindingAuditResponse]
