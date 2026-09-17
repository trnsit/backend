import asyncio

from .agents.audit.agent import CryptoAuditAgent
from .agents.audit.schemas import FindingAuditRequest, FindingAuditResponse, BatchAuditRequest, BatchAuditResponse

# Service layer coordinating agent execution and throttling hardware concurrency for local LLMs.
class IntelligenceService:
    def __init__(self, audit_agent: CryptoAuditAgent | None = None, max_concurrency: int = 3):
        self.audit_agent = audit_agent or CryptoAuditAgent()
        self.semaphore = asyncio.Semaphore(max_concurrency) # Limits concurrent Ollama requests to 3

    # Audit a single finding through the CryptoAuditAgent
    async def audit_finding(self, request: FindingAuditRequest) -> FindingAuditResponse:
        async with self.semaphore:
            return await self.audit_agent.audit(request)

    # Audit a list of findings concurrently, safely throttled by the internal semaphore
    async def batch_finding(self, request: BatchAuditRequest) -> BatchAuditResponse:
        results = await asyncio.gather(*(self.audit_finding(f) for f in request.findings))

        return BatchAuditResponse(results=results)
