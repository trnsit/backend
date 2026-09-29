from fastapi import Depends, APIRouter, status

from app.core.dependencies import verify_internal_token, get_current_user, CurrentUser

from .agents.audit.schemas import FindingAuditRequest, FindingAuditResponse, BatchAuditRequest, BatchAuditResponse
from .agents.migration.schemas import MigrationPlanRequest, MigrationPlanResponse, MigrationExecuteRequest, MigrationExecuteResponse
from .service import IntelligenceService
from .dependencies import get_intelligence_service

router = APIRouter(
    prefix='/intelligence',
    tags=['intelligence']
)

# INTERNAL SCANNER AUDIT ENDPOINTS
@router.post('/audit', response_model=FindingAuditResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(verify_internal_token)])
async def audit_finding(
    request: FindingAuditRequest,
    service: IntelligenceService = Depends(get_intelligence_service)
) -> FindingAuditResponse:
    return await service.audit_finding(request)

@router.post('/audit/batch', response_model=BatchAuditResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(verify_internal_token)])
async def audit_batch(
    request: BatchAuditRequest,
    service: IntelligenceService = Depends(get_intelligence_service)
) -> BatchAuditResponse:
    return await service.batch_finding(request)

# USER-FACING MIGRATION ENDPOINTS (Authenticated via JWT)
@router.post('/migration/plan', response_model=MigrationPlanResponse, status_code=status.HTTP_200_OK)
async def plan_migration(
    request: MigrationPlanRequest,
    user: CurrentUser = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> MigrationPlanResponse:
    return await service.plan_migration(request)

@router.post('/migration/execute', response_model=MigrationExecuteResponse, status_code=status.HTTP_200_OK)
async def execute_migration(
    request: MigrationExecuteRequest,
    user: CurrentUser = Depends(get_current_user),
    service: IntelligenceService = Depends(get_intelligence_service)
) -> MigrationExecuteResponse:
    return await service.execute_migration(request)
