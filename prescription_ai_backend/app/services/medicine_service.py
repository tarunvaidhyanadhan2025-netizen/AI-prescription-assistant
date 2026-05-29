"""
Medicine Service
Provides medicine data lookup from the local seed database
and enrichment via OpenAI when data is not available locally.
"""

import json
import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Path to the local seed database
SEED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "medicine_seed.json")


class MedicineService:
    """
    Provides:
    - Local medicine lookup (seed JSON)
    - OpenAI-powered enrichment for unknown medicines
    - Drug-drug interaction checks
    - Classification helpers
    """

    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._local_db: Dict[str, Dict[str, Any]] = {}
        self._load_local_db()

    # ── Public API ─────────────────────────────────────────────────────────

    def get_local(self, medicine_name: str) -> Optional[Dict[str, Any]]:
        """
        Case-insensitive local seed lookup.
        Returns None if not found.
        """
        key = medicine_name.lower().strip()
        return self._local_db.get(key)

    async def get_medicine_info(self, medicine_name: str) -> Dict[str, Any]:
        """
        Fetch medicine information.
        1. Try local seed first (fast, free).
        2. Fall back to OpenAI structured call.
        """
        local = self.get_local(medicine_name)
        if local:
            logger.debug(f"Local hit for '{medicine_name}'")
            return local

        logger.info(f"No local record for '{medicine_name}', querying OpenAI...")
        return await self._fetch_from_openai(medicine_name)

    async def get_interactions(self, medicines: List[str]) -> List[Dict[str, Any]]:
        """
        Check drug-drug interactions for a list of medicines.
        Returns a list of interaction objects.
        """
        if len(medicines) < 2:
            return []

        medicine_list = ", ".join(medicines)
        prompt = (
            f"As a clinical pharmacist, list all known drug-drug interactions "
            f"between these medicines: {medicine_list}. "
            "For each interaction, return JSON with keys: "
            "'drug1', 'drug2', 'severity' (mild/moderate/severe), 'description'. "
            "Return ONLY a JSON array. If no interactions, return []."
        )

        try:
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a clinical pharmacist. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            return data.get("interactions", []) if isinstance(data, dict) else data
        except Exception as exc:
            logger.error(f"Interaction check failed: {exc}")
            return []

    # ── Internal ───────────────────────────────────────────────────────────

    def _load_local_db(self):
        """Load the seed JSON into memory."""
        try:
            with open(SEED_FILE, "r", encoding="utf-8") as f:
                records: List[Dict[str, Any]] = json.load(f)
            for record in records:
                name_key = record.get("name", "").lower().strip()
                if name_key:
                    self._local_db[name_key] = record
                    # Also index by generic_name and aliases
                    for alias in record.get("aliases", []):
                        self._local_db[alias.lower().strip()] = record
            logger.info(f"Loaded {len(self._local_db)} medicine records from seed.")
        except FileNotFoundError:
            logger.warning(f"Seed file not found at {SEED_FILE}. Starting with empty local DB.")
        except json.JSONDecodeError as exc:
            logger.error(f"Seed file JSON parse error: {exc}")

    async def _fetch_from_openai(self, medicine_name: str) -> Dict[str, Any]:
        """
        Ask OpenAI for structured medicine data.
        Returns a dict matching the seed schema.
        """
        system_prompt = (
            "You are a clinical pharmacist. "
            "Respond ONLY with a single valid JSON object, no preamble, no markdown."
        )
        user_prompt = f"""
Provide detailed information about the medicine "{medicine_name}" in this exact JSON format:
{{
  "name": "{medicine_name}",
  "generic_name": "<generic/INN name>",
  "brand_names": ["<brand1>", "<brand2>"],
  "drug_class": "<pharmacological class>",
  "use_case": "<primary therapeutic indication>",
  "mechanism": "<brief mechanism of action>",
  "dosage_forms": ["<form1>", "<form2>"],
  "common_dosages": {{
    "adult": "<typical adult dose>",
    "pediatric": "<typical pediatric dose or 'Not recommended'>",
    "elderly": "<elderly adjustment or 'Use with caution'>"
  }},
  "side_effects": {{
    "common": ["<side_effect1>", "<side_effect2>"],
    "serious": ["<serious1>", "<serious2>"]
  }},
  "causes_drowsiness": <true or false>,
  "contraindications": ["<contra1>", "<contra2>"],
  "interactions": ["<drug1>", "<drug2>"],
  "age_warnings": {{
    "pediatric": "<warning or empty string>",
    "geriatric": "<warning or empty string>",
    "pregnancy": "<category and warning>"
  }},
  "alternatives": ["<alt1>", "<alt2>"],
  "severity_level": "<low|medium|high>",
  "otc_available": <true or false>,
  "schedule": "<controlled substance schedule or 'Not scheduled'>"
}}
"""

        try:
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception as exc:
            logger.error(f"OpenAI medicine fetch failed for '{medicine_name}': {exc}")
            return {
                "name": medicine_name,
                "generic_name": medicine_name,
                "use_case": "Information not available",
                "side_effects": {"common": [], "serious": []},
                "causes_drowsiness": False,
                "age_warnings": {},
                "alternatives": [],
                "severity_level": "unknown",
            }
