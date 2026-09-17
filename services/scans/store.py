from uuid import UUID

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Scan, ScanFinding

class ScanStore:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, scan_id: UUID, user_id: UUID) -> Scan | None:
        result = await self.session.execute(
            select(Scan)
            .options(selectinload(Scan.findings))
            .where(
                Scan.id == scan_id,
                Scan.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def list_by_repository(self, repository_id: UUID, user_id: UUID) -> list[Scan]:
        result = await self.session.execute(
            select(Scan)
            .options(selectinload(Scan.findings))
            .where(
                Scan.repository_id == repository_id,
                Scan.user_id == user_id
            )
            .order_by(Scan.created_at.desc())
        )

        return list(result.scalars().all())

    async def create(self, repository_id: UUID, user_id: UUID) -> Scan:
        scan = Scan(
            repository_id=repository_id,
            user_id=user_id,
            status='pending'
        )

        self.session.add(scan)
        await self.session.commit()
        await self.session.refresh(scan)

        return scan

    async def update_status(self, scan_id: UUID, status: str, completed_at: datetime | None = None) -> Scan | None:
        result = await self.session.execute(
            select(Scan).where(Scan.id == scan_id)
        )

        scan = result.scalar_one_or_none()

        if not scan:
            return None
            
        scan.status = status

        if completed_at:
            scan.completed_at = completed_at
            
        await self.session.commit()
        await self.session.refresh(scan)

        return scan

    async def save_findings(self, scan_id: UUID, findings_data: list[dict]) -> list[ScanFinding]:
        findings = [
            ScanFinding(
                scan_id=scan_id,
                file_path=item["file"],
                line_number=item["line_number"],
                category=item["category"],
                algorithm=item["algorithm"],
                line_content=item["line_content"],

                # Add these three lines to store agent outputs:
                is_false_positive=item.get("is_false_positive", False),
                agent_explanation=item.get("agent_explanation"),
                suggested_explanation=item.get("suggested_explanation")
            ) for item in findings_data
        ]

        self.session.add_all(findings)
        await self.session.commit()

        return findings
