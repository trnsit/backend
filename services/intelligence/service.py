import asyncio

from .agents.audit.agent import CryptoAuditAgent
from .agents.audit.schemas import FindingAuditRequest, FindingAuditResponse, BatchAuditRequest, BatchAuditResponse

from .agents.migration.agent import MigrationPlannerAgent
from .agents.migration.executor import MigrationExecutor
from .agents.migration.schemas import MigrationPlanRequest, MigrationPlanResponse, MigrationExecuteRequest, MigrationExecuteResponse

# Service layer coordinating agent execution and throttling concurrency for local LLMs.
class IntelligenceService:
    def __init__(
        self,
        audit_agent: CryptoAuditAgent | None = None,
        migration_planner: MigrationPlannerAgent | None = None,
        max_concurrency: int = 3
    ):
        self.audit_agent = audit_agent or CryptoAuditAgent()
        self.migration_planner = migration_planner or MigrationPlannerAgent()
        self.executor = MigrationExecutor()
        self.semaphore = asyncio.Semaphore(max_concurrency) # Limits concurrent Ollama requests

    # Audit a single finding through the CryptoAuditAgent
    async def audit_finding(self, request: FindingAuditRequest) -> FindingAuditResponse:
        async with self.semaphore:
            return await self.audit_agent.audit(request)

    # Audit a list of findings concurrently
    async def batch_finding(self, request: BatchAuditRequest) -> BatchAuditResponse:
        results = await asyncio.gather(*(self.audit_finding(f) for f in request.findings))

        return BatchAuditResponse(results=results)

    # 1. Plan a post-quantum migration for a file
    async def plan_migration(self, request: MigrationPlanRequest) -> MigrationPlanResponse:
        async with self.semaphore:
            return await self.migration_planner.plan_migration(request)

    # 2. Execute approved migration to remote GitHub and wipe scratchpad
    async def execute_migration(self, request: MigrationExecuteRequest) -> MigrationExecuteResponse:
        loop = asyncio.get_running_loop()

        # Offload synchronous git operations to thread pool
        result = await loop.run_in_executor(
            None,
            self.executor.execute_remote_migration,
            request.repo_full_name,
            request.github_token,
            request.file_rel_path,
            request.migrated_file_content,
            request.branch_name
        )

        return MigrationExecuteResponse(**result)
