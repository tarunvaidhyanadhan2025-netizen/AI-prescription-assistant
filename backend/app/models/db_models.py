"""
SQLAlchemy ORM models for PostgreSQL.
Stores prescription metadata and analysis results.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512))
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cleaned_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_medicines: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    patient_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    analysis_done: Mapped[bool] = mapped_column(Boolean, default=False)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prescription_id: Mapped[str] = mapped_column(String(36), index=True)
    medicine_name: Mapped[str] = mapped_column(String(255))
    drug_class: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    use_case: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    side_effects: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    warnings: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    dosage_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity_level: Mapped[str] = mapped_column(String(20), default="low")
    causes_drowsiness: Mapped[bool] = mapped_column(Boolean, default=False)
    provider_used: Mapped[str] = mapped_column(String(50), default="template")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
