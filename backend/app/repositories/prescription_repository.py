"""Prescription repository — all DB access in one place."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import AnalysisResult, Prescription
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PrescriptionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, prescription: Prescription) -> Prescription:
        self._session.add(prescription)
        await self._session.flush()
        return prescription

    async def get_by_id(self, prescription_id: str) -> Optional[Prescription]:
        result = await self._session.execute(
            select(Prescription).where(Prescription.id == prescription_id)
        )
        return result.scalar_one_or_none()

    async def update(self, prescription: Prescription) -> Prescription:
        await self._session.merge(prescription)
        await self._session.flush()
        return prescription

    async def save_analysis(self, result: AnalysisResult) -> AnalysisResult:
        self._session.add(result)
        await self._session.flush()
        return result

    async def get_analyses(self, prescription_id: str) -> List[AnalysisResult]:
        result = await self._session.execute(
            select(AnalysisResult)
            .where(AnalysisResult.prescription_id == prescription_id)
            .order_by(AnalysisResult.created_at)
        )
        return list(result.scalars().all())
