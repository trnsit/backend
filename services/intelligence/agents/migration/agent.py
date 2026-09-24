from ...rag.vector_store import VectorStore
from ..core.base import BaseAgent
from .schemas import MigrationPlanRequest, MigrationPlanResponse

class MigrationPlannerAgent(BaseAgent):
    def __init__(self, model_name: str | None = None, base_url: str | None = None, vector_store: VectorStore | None = None):
        super().__init__(model_name=model_name, base_url=base_url)

        self.vector_store = vector_store or VectorStore()

    def _build_prompt(self, request: MigrationPlanRequest, rag_guidance: str) -> str:
        return f"""
            You are an expert cryptographic software engineer generating an automated migration plan to transition legacy code to Post-Quantum Cryptography (PQC).
            Vulnerable Finding Details:
            - File Path: {request.file_path}
            - Line Number: {request.line_number}
            - Current Algorithm: {request.algorithm}
            - Vulnerability Category: {request.category}
            Surrounding Code Context:
            ```
            {request.code_context}
            ```
            Authoritative Migration Guidance (from Knowledge Base):
            \"\"\"
            {rag_guidance}
            \"\"\"
            Task:
            Generate a concrete, syntactically valid code migration that replaces the legacy cryptographic usage with the approved post-quantum or secure alternative.
            Rules:
            1. `original_code` must match the exact block in the context that needs replacement.
            2. `migrated_code` must be clean, production-grade replacement code.
            3. `unified_diff` must be formatted like a standard git diff:
               --- a/{request.file_path}
               +++ b/{request.file_path}
               - <old lines>
               + <new lines>
            4. `library_required`: Specify the library used (e.g., 'oqs-python', 'cryptography', 'hashlib').
            5. `complexity`: Rate complexity as 'LOW' (drop-in swap), 'MEDIUM' (requires import/key handling change), or 'HIGH' (architectural change).
        """

    async def plan_migration(self, request: MigrationPlanRequest) -> MigrationPlanResponse:
        # 1. RAG Search: Retrieve the best migration playbook from Qdrant
        rag_guidance = 'Migrate to modern approved standard.'

        try:
            query = f'Migration guidance replacing {request.algorithm} in {request.category}'
            docs = await self.vector_store.search(query, limit=2)

            if docs:
                rag_guidance = "\n\n".join([f"[{d.get('title')}]: {d.get('content')}" for d in docs])

        except Exception as e:
            print(f"Warning: Qdrant lookup failed during migration planning: {e}")

        # 2. Build Agent Messages
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a migration planning agent. You MUST reply ONLY with a valid JSON object matching this schema: '
                    "{'original_code': 'string', 'migrated_code': 'string', 'unified_diff': 'string', "
                    "'explanation': 'string', 'library_required': 'string', 'complexity': 'string'}"
                )
            },
            {
                'role': 'user',
                'content': self._build_prompt(request, rag_guidance)
            }
        ]

        # 3. Call LLM
        response_text = await self.chat(messages)

        return MigrationPlanResponse.model_validate_json(response_text)
