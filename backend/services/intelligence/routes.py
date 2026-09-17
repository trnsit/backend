from fastapi import Depends, APIRouter, status

from .agents.audit.schemas import FindingAuditRequest, FindingAuditResponse, BatchAuditRequest, BatchAuditResponse
from .service import IntelligenceService
from .dependencies import get_intelligence_service

router = APIRouter(
    prefix='/intelligence',
    tags=['intelligence']
)

@router.post('/audit', response_model=FindingAuditResponse, status_code=status.HTTP_200_OK)
# Audit a single cryptographic code finding
async def audit_finding(
        request: FindingAuditRequest,
        service: IntelligenceService = Depends(get_intelligence_service)
):
    return await service.audit_finding(request)

@router.post('/audit/batch', response_model=BatchAuditResponse, status_code=status.HTTP_200_OK)
# Audit a batch of cryptographic code findings with controlled concurrency
async def audit_batch(
        request: BatchAuditRequest,
        service: IntelligenceService = Depends(get_intelligence_service)
):
    return await service.batch_finding(request)
