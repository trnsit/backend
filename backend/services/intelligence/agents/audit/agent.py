from ..core.base import BaseAgent

from .schemas import FindingAuditRequest, FindingAuditResponse

class CryptoAuditAgent(BaseAgent):
    def _build_prompt(self, request: FindingAuditRequest):
        return f"""
            You are a cryptographic security expert auditing a codebase for migration to post-quantum and modern secure cryptography.
            A static analysis tool flagged a potential issue:

            - File Path: {request.file_path}
            - Line Number: {request.line_number}
            - Matched Category: {request.category}
            - Flagged Algorithm/Library: {request.algorithm}
            - Matched Line Content: "{request.matched_line}"

            Here is the surrounding code context:
            ```
            {request.code_context}
            ```

            Evaluate if this is a true security threat or a false positive:
            1. Set `is_false_positive` to true ONLY if:
                - The flagged algorithm is used for non-security purposes (e.g., MD5 for file name hashing/cache keys, UUID generation, testing/mock setups).
                - The code is just a comment, documentation, or string literal unrelated to execution.
                Otherwise, set `is_false_positive` to false.

            2. Provide a clear, developer-friendly `agent_explanation` detailing the risks (if any) or explaining why it is a false positive.
            
            3. Provide a `suggested_explanation` describing exactly what needs to be changed to fix it (e.g., "Replace MD5 with SHA-256 using hashlib" or "Migrate RSA signing to Ed25519"). If it's a false positive, write "No changes needed."
        """

    async def audit(self, request: FindingAuditRequest) -> FindingAuditResponse:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a security audit agent. You MUST reply ONLY with a JSON object matching this schema: "
                    '{"is_false_positive": boolean, "agent_explanation": "string", "suggested_explanation": "string"}'
                )
            },
            {
                "role": "user",
                "content": self._build_prompt(request)
            }
        ]

        try:
            # Call Ollama through our shared BaseAgent telephone:
            response_text = await self.chat(messages)

            return FindingAuditResponse.model_validate_json(response_text)

        except Exception as exc:
            # Graceful fallback if Ollama is offline or fails to respond
            return FindingAuditResponse(
                is_false_positive=False,
                agent_explanation=f"Error running local AI analysis: {str(exc)}",
                suggested_explanation="Review the algorithm usage manually."
            )
