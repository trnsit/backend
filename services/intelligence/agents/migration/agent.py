from ...rag.vector_store import VectorStore
from ..core.base import BaseAgent
from .schemas import MigrationPlanRequest, MigrationPlanResponse

class MigrationPlannerAgent(BaseAgent):
    def __init__(self, model_name: str | None = None, base_url: str | None = None, vector_store: VectorStore | None = None):
        super().__init__(model_name=model_name, base_url=base_url)

        self.vector_store = vector_store or VectorStore()

    def _build_prompt(self, request: MigrationPlanRequest, rag_guidance: str) -> str:
        return f"""
            You are an expert cryptographic software engineer performing an automated Post-Quantum Cryptography (PQC) migration.

            Vulnerability Details:
            - File Path: {request.file_path}
            - Line Number: {request.line_number}
            - Flagged Algorithm: {request.algorithm} ({request.category})

            Original File Content:
            ```
            {request.code_content}
            ```

            Authoritative Migration Guidance (from Knowledge Base):
            \"\"\"
            {rag_guidance}
            \"\"\"

            Task:
            Rewrite the entire file to migrate from the legacy algorithm to the approved post-quantum alternative.
            1. Add all necessary new imports at the top of the file (e.g. from oqs or cryptography).
            2. Remove any obsolete/deprecated imports if no longer needed.
            3. Rewrite the vulnerable function so it uses post-quantum cryptography.
            4. Preserve the overall logic and return types so other files in the project don't break.

            Output ONLY a valid JSON object matching this exact format:
            {{
              "migrated_file_content": "<escaped string of the full updated python file>",
              "explanation": "<brief explanation of the changes>",
              "library_required": "oqs-python",
              "complexity": "LOW"
            }}
        """

    async def plan_migration(self, request: MigrationPlanRequest) -> MigrationPlanResponse:
        rag_guidance = 'Migrate to modern approved standard.'

        try:
            query = f'Migration guidance replacing {request.algorithm} in {request.category}'
            docs = await self.vector_store.search(query, limit=2)

            if docs:
                rag_guidance = '\n\n'.join([f'[{d.get('title')}]: {d.get('content')}' for d in docs])

        except Exception as e:
            print(f'Warning: Qdrant lookup failed during migration planning: {e}')

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a migration planning agent. You MUST reply ONLY with a valid JSON object matching this schema: "
                    '{"migrated_file_content": "string", "explanation": "string", "library_required": "string", "complexity": "string"}'
                )
            },
            {
                "role": "user",
                "content": self._build_prompt(request, rag_guidance)
            }
        ]

        response_text = await self.chat(messages)

        return MigrationPlanResponse.model_validate_json(response_text)
