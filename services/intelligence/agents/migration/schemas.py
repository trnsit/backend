from pydantic import BaseModel, Field

class MigrationPlanRequest(BaseModel):
    file_path: str
    line_number: int
    algorithm: str
    category: str
    code_content: str # Full file content
    target_standard: str | None = None  # eg. ML-DSA-65 (FIPS 204)

class MigrationPlanResponse(BaseModel):
    migrated_file_content: str = Field(description='The complete, updated file content with modern imports and quantum-safe code')
    explanation: str = Field(default='Migrated to post-quantum cryptography.', description='Clear explanation of the changes made and any new imports required')
    library_required: str = Field(default='oqs-python', description="Python package or dependency required, e.g. 'oqs-python' or 'cryptography'")
    complexity: str = Field(default='LOW', description='Migration complexity: LOW, MEDIUM, or HIGH')
