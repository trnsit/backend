from pydantic import BaseModel, Field

class MigrationPlanRequest(BaseModel):
    file_path: str
    line_number: int
    algorithm: str
    category: str
    code_context: str
    target_standard: str | None = None  # eg. ML-DSA-65 (FIPS 204)

class MigrationPlanResponse(BaseModel):
    original_code: str = Field(description='The exact snippet of code to be replaced')
    migrated_code: str = Field(description='The modern, quantum-safe replacement code')
    unified_diff: str = Field(description='A git-style unified diff showing lines removed with - and lines added with +')
    explanation: str = Field(description='Clear explanation of the changes made and any new imports required')
    library_required: str = Field(description="Python package or dependency required, e.g. 'oqs-python' or 'cryptography'")
    complexity: str = Field(description='Migration complexity: LOW, MEDIUM, or HIGH')
