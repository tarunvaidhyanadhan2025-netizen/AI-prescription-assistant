"""
Medicine Pydantic Models
Data models representing medicine records in the system.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DosageInfo(BaseModel):
    adult: str = ""
    pediatric: str = ""
    elderly: str = ""


class SideEffects(BaseModel):
    common: List[str] = Field(default_factory=list)
    serious: List[str] = Field(default_factory=list)


class AgeWarnings(BaseModel):
    pediatric: str = ""
    geriatric: str = ""
    pregnancy: str = ""


class MedicineRecord(BaseModel):
    """Full medicine record as stored in the seed database and vector store."""
    name: str
    generic_name: str = ""
    aliases: List[str] = Field(default_factory=list)
    brand_names: List[str] = Field(default_factory=list)
    drug_class: str = ""
    use_case: str = ""
    mechanism: str = ""
    dosage_forms: List[str] = Field(default_factory=list)
    common_dosages: DosageInfo = Field(default_factory=DosageInfo)
    side_effects: SideEffects = Field(default_factory=SideEffects)
    causes_drowsiness: bool = False
    contraindications: List[str] = Field(default_factory=list)
    interactions: List[str] = Field(default_factory=list)
    age_warnings: AgeWarnings = Field(default_factory=AgeWarnings)
    alternatives: List[str] = Field(default_factory=list)
    severity_level: str = "low"
    otc_available: bool = False
    schedule: str = "Not scheduled"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MedicineRecord":
        """Construct from a raw dictionary (e.g., seed JSON)."""
        dosages = data.get("common_dosages", {})
        se = data.get("side_effects", {})
        aw = data.get("age_warnings", {})
        return cls(
            name=data.get("name", ""),
            generic_name=data.get("generic_name", ""),
            aliases=data.get("aliases", []),
            brand_names=data.get("brand_names", []),
            drug_class=data.get("drug_class", ""),
            use_case=data.get("use_case", ""),
            mechanism=data.get("mechanism", ""),
            dosage_forms=data.get("dosage_forms", []),
            common_dosages=DosageInfo(
                adult=dosages.get("adult", ""),
                pediatric=dosages.get("pediatric", ""),
                elderly=dosages.get("elderly", ""),
            ),
            side_effects=SideEffects(
                common=se.get("common", []),
                serious=se.get("serious", []),
            ),
            causes_drowsiness=data.get("causes_drowsiness", False),
            contraindications=data.get("contraindications", []),
            interactions=data.get("interactions", []),
            age_warnings=AgeWarnings(
                pediatric=aw.get("pediatric", ""),
                geriatric=aw.get("geriatric", ""),
                pregnancy=aw.get("pregnancy", ""),
            ),
            alternatives=data.get("alternatives", []),
            severity_level=data.get("severity_level", "low"),
            otc_available=data.get("otc_available", False),
            schedule=data.get("schedule", "Not scheduled"),
        )
