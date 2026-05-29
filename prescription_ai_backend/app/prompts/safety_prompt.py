"""
Safety Prompt Templates
LangChain prompt templates for medicine safety evaluation,
side effect analysis, and contraindication detection.
"""

# ── Main Safety Analysis System Prompt ────────────────────────────────────
SAFETY_SYSTEM_PROMPT = """You are a senior clinical pharmacist conducting a comprehensive 
medicine safety evaluation. Your primary duty is patient safety.

Guidelines:
- Be thorough but concise
- Flag ALL potential risks clearly
- Use clinical evidence; do not speculate
- For paediatric and geriatric patients, apply stricter scrutiny
- Respond ONLY with valid JSON. No additional text.
"""

# ── Comprehensive Safety Human Prompt ─────────────────────────────────────
SAFETY_ANALYSIS_PROMPT = """
Medicine: {medicine_name}
Patient Age: {patient_age}
Prescription Context (from clinical database):
---
{rag_context}
---
Response Language: {language}

Provide a comprehensive safety evaluation. Return ONLY this JSON:
{{
  "side_effects": ["<common side effect 1>", "<common side effect 2>", ...],
  "serious_side_effects": ["<serious effect 1>", ...],
  "causes_drowsiness": <true/false>,
  "drowsiness_note": "<advice if drowsy, else empty string>",
  "dosage_info": "<standard dose summary for the patient's age group>",
  "dosage_safe": <true/false — assume prescribed dose is standard if unknown>,
  "dosage_notes": ["<note 1>", "<note 2>"],
  "age_warnings": ["<age-specific warning if applicable>"],
  "contraindications": ["<contraindication 1>", ...],
  "drug_interactions": ["<interaction 1>", ...],
  "alternatives": ["<alternative medicine 1>", "<alternative 2>", ...],
  "severity_level": "<low|medium|high|critical>",
  "important_notes": ["<important clinical note 1>", ...]
}}
"""

# ── Interaction Check Prompt ───────────────────────────────────────────────
INTERACTION_CHECK_PROMPT = """
As a clinical pharmacist, check for drug-drug interactions between:
Medicines: {medicine_list}

Return ONLY a JSON array:
[
  {{
    "drug1": "<name>",
    "drug2": "<name>",
    "severity": "<mild|moderate|severe|contraindicated>",
    "mechanism": "<brief mechanism>",
    "clinical_effect": "<what happens clinically>",
    "management": "<how to manage>"
  }}
]
If no interactions, return [].
"""

# ── Age-Specific Warning Prompt ────────────────────────────────────────────
AGE_WARNING_PROMPT = """
Medicine: {medicine_name}
Patient Age: {age} years

As a clinical pharmacist, provide age-specific safety warnings.
Return ONLY JSON:
{{
  "age_appropriate": <true/false>,
  "warnings": ["<warning 1>", ...],
  "dose_adjustment_needed": <true/false>,
  "recommended_action": "<what prescriber/patient should do>",
  "severity": "<low|medium|high|critical>"
}}
"""

# ── Dosage Safety Prompt ───────────────────────────────────────────────────
DOSAGE_SAFETY_PROMPT = """
Medicine: {medicine_name}
Prescribed Dose: {prescribed_dose}
Patient Age: {patient_age}
Clinical Context: {context}

Evaluate dosage safety. Return ONLY JSON:
{{
  "is_safe": <true/false>,
  "prescribed_dose_mg": <number or null>,
  "standard_adult_dose": "<standard dose>",
  "max_daily_dose": "<max daily>",
  "warnings": ["<warning>"],
  "recommendations": ["<recommendation>"],
  "assessment": "<one sentence clinical assessment>"
}}
"""
