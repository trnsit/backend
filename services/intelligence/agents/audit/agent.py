from ...rag.vector_store import VectorStore
from ..core.base import BaseAgent
from .schemas import FindingAuditRequest, FindingAuditResponse

class CryptoAuditAgent(BaseAgent):
    def __init__(self, model_name: str | None = None, base_url: str | None = None, vector_store: VectorStore | None = None):
        super().__init__(model_name=model_name, base_url=base_url)

        self.vector_store = vector_store or VectorStore()

    def _build_prompt(self, request: FindingAuditRequest, rag_context: str) -> str:
        return f"""
            You are a cryptographic security expert auditing a codebase for migration to post-quantum and modern secure cryptography.
            A static analysis tool flagged a potential issue:

            - File Path: {request.file_path}
            - Line Number: {request.line_number}
            - Matched Category: {request.category}
            - Flagged Algorithm/Library: {request.algorithm}
            - Matched Line Content: '{request.matched_line}'

            Surrounding Code Context:
            ```
            {request.code_context}
            ```

            Authoritative Cryptographic Standards & Guidelines (Retrieved from Knowledge Base):
            \"\"\"
            {rag_context}
            \"\"\"

            Evaluate if this is a true security threat or a false positive:
            1. Set `is_false_positive` to true ONLY if:
                - The flagged algorithm is used for non-security purposes (e.g., MD5 for file name hashing/cache keys, UUID generation, testing/mock setups).
                - The code is just a comment, documentation, or string literal unrelated to execution.
                Otherwise, set `is_false_positive` to false.

            2. Provide a clear, developer-friendly `agent_explanation` detailing the risks (if any) or explaining why it is a false positive.
            
            3. Provide a `suggested_explanation` describing exactly what needs to be changed to fix it. 
               CRITICAL: You MUST ground your recommendation in the Authoritative Cryptographic Standards retrieved above (cite standards like NIST FIPS 203, FIPS 204, etc., when applicable). If it's a false positive, write "No changes needed."
        """

    async def audit(self, request: FindingAuditRequest) -> FindingAuditResponse:
        # 1. RAG Search: Retrieve top 2 matching standards from Qdrant

        rag_context = 'No specific reference documents found.'

        try:
            search_query = f'{request.algorithm} {request.category} migration replacement'
            docs = await self.vector_store.search(search_query, limit=2)

            if docs:
                rag_context = "\n\n".join([
                    f"[{doc.get('source')} - {doc.get('title')}]:\n{doc.get('content')}"
                    for doc in docs
                ])

        except Exception as e:
            print(f'Warning: RAG lookup failed, proceeding without context: {e}')

        # 2. Build Prompt with RAG context
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are a security audit agent. You MUST reply ONLY with a JSON object matching this schema: '
                    "{'is_false_positive': boolean, 'agent_explanation': 'string', 'suggested_explanation': 'string'}"
                )
            },
            {
                'role': 'user',
                'content': self._build_prompt(request, rag_context)
            }
        ]

        try:
            # 3. Call LLM (Ollama)
            response_text = await self.chat(messages)

            return FindingAuditResponse.model_validate_json(response_text)

        except Exception as exc:
            return FindingAuditResponse(
                is_false_positive=False,
                agent_explanation=f'Error running local AI analysis: {str(exc)}',
                suggested_explanation='Review the algorithm usage manually.'
            )
