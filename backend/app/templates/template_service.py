"""
TemplateService — generates structured responses from YAML templates.
No LLM required. Used when MODEL_PROVIDER=template or as fallback.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from app.utils.logger import get_logger

logger = get_logger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "data"

# Fallback name → drug class map when vector DB has no context
_NAME_TO_CLASS: Dict[str, str] = {
    # Analgesics
    "paracetamol": "Analgesic / Antipyretic",
    "acetaminophen": "Analgesic / Antipyretic",
    "aspirin": "NSAID",
    "ibuprofen": "NSAID",
    "naproxen": "NSAID",
    "diclofenac": "NSAID",
    "celecoxib": "NSAID",
    "indomethacin": "NSAID",
    # Antibiotics
    "amoxicillin": "Penicillin Antibiotic",
    "ampicillin": "Penicillin Antibiotic",
    "flucloxacillin": "Penicillin Antibiotic",
    "azithromycin": "Macrolide Antibiotic",
    "clarithromycin": "Macrolide Antibiotic",
    "erythromycin": "Macrolide Antibiotic",
    # Benzodiazepines
    "diazepam": "Benzodiazepine",
    "lorazepam": "Benzodiazepine",
    "clonazepam": "Benzodiazepine",
    "alprazolam": "Benzodiazepine",
    "temazepam": "Benzodiazepine",
    "midazolam": "Benzodiazepine",
    # Beta blockers
    "metoprolol": "Beta Blocker",
    "atenolol": "Beta Blocker",
    "propranolol": "Beta Blocker",
    "bisoprolol": "Beta Blocker",
    "carvedilol": "Beta Blocker",
    # Statins
    "atorvastatin": "Statin",
    "simvastatin": "Statin",
    "rosuvastatin": "Statin",
    "pravastatin": "Statin",
    # PPIs
    "omeprazole": "Proton Pump Inhibitor",
    "pantoprazole": "Proton Pump Inhibitor",
    "lansoprazole": "Proton Pump Inhibitor",
    "esomeprazole": "Proton Pump Inhibitor",
    # ACE inhibitors
    "lisinopril": "ACE Inhibitor",
    "enalapril": "ACE Inhibitor",
    "ramipril": "ACE Inhibitor",
    "perindopril": "ACE Inhibitor",
    # Antihistamines
    "cetirizine": "Antihistamine",
    "loratadine": "Antihistamine",
    "fexofenadine": "Antihistamine",
    "diphenhydramine": "Antihistamine",
    "chlorphenamine": "Antihistamine",
    "promethazine": "Antihistamine",
    "chlorpheniramine": "Antihistamine",
    "doxylamine": "First-generation Antihistamine",
    # Antibiotics continued
    "metronidazole": "Nitroimidazole Antibiotic",
    "tinidazole": "Nitroimidazole Antibiotic",
    "ciprofloxacin": "Fluoroquinolone Antibiotic",
    "levofloxacin": "Fluoroquinolone Antibiotic",
    "ofloxacin": "Fluoroquinolone Antibiotic",
    "norfloxacin": "Fluoroquinolone Antibiotic",
    "doxycycline": "Tetracycline Antibiotic",
    "tetracycline": "Tetracycline Antibiotic",
    "cefixime": "Cephalosporin Antibiotic",
    "cefuroxime": "Cephalosporin Antibiotic",
    "ceftriaxone": "Cephalosporin Antibiotic",
    "cefpodoxime": "Cephalosporin Antibiotic",
    "nitrofurantoin": "Nitrofuran Antibiotic",
    # Vitamins / supplements
    "pyridoxine": "Vitamin B6 Supplement",
    "folic acid": "Vitamin B9 (Folate) Supplement",
    "methylcobalamin": "Vitamin B12 Supplement",
    "cyanocobalamin": "Vitamin B12 Supplement",
    "cholecalciferol": "Vitamin D3 Supplement",
    "calcium carbonate": "Calcium Supplement",
    "ferrous sulphate": "Iron Supplement",
    "zinc": "Zinc Supplement",
    # Antiemetics
    "ondansetron": "5-HT3 Receptor Antagonist Antiemetic",
    "domperidone": "Dopamine Antagonist Antiemetic",
    "metoclopramide": "Dopamine Antagonist Antiemetic",
    "promethazine": "Phenothiazine Antiemetic",
    # Uterine relaxants / tocolytics
    "isoxsuprine": "Beta-adrenergic Agonist / Uterine Relaxant",
    "ritodrine": "Beta-adrenergic Agonist / Tocolytic",
    "nifedipine": "Calcium Channel Blocker",
    # Anticoagulants
    "abciximab": "Glycoprotein IIb/IIIa Inhibitor",
    "clopidogrel": "Antiplatelet Agent",
    "warfarin": "Vitamin K Antagonist",
    "heparin": "Anticoagulant",
    "aspirin": "NSAID / Antiplatelet",
    # GI medicines
    "pantoprazole": "Proton Pump Inhibitor",
    "rabeprazole": "Proton Pump Inhibitor",
    "ranitidine": "H2 Receptor Antagonist",
    "famotidine": "H2 Receptor Antagonist",
    "sucralfate": "Mucosal Protective Agent",
    "lactulose": "Osmotic Laxative",
    "bisacodyl": "Stimulant Laxative",
    # Steroids / anti-inflammatory
    "prednisolone": "Corticosteroid",
    "dexamethasone": "Corticosteroid",
    "hydrocortisone": "Corticosteroid",
    "betamethasone": "Corticosteroid",
    "methylprednisolone": "Corticosteroid",
    "mometasone": "Topical Corticosteroid",
    # Dermatology
    "tretinoin": "Topical Retinoid",
    "clindamycin": "Lincosamide Antibiotic",
    "adapalene": "Topical Retinoid",
    "benzoyl peroxide": "Topical Antibacterial",
    "ketoconazole": "Antifungal",
    "fluconazole": "Antifungal",
    "terbinafine": "Antifungal",
    # Antidiabetics
    "metformin": "Biguanide Antidiabetic",
    "glimepiride": "Sulfonylurea",
    "glibenclamide": "Sulfonylurea",
    "sitagliptin": "DPP-4 Inhibitor",
    "insulin": "Insulin",
    # ── Indian brand names → correct drug class ──────────────────────
    # These are the exact names that appear in Indian prescriptions
    # and that LLMs frequently hallucinate about
    "gestakind": "Beta-adrenergic Agonist / Uterine Relaxant (Isoxsuprine)",
    "gestakind 10/sr": "Beta-adrenergic Agonist / Uterine Relaxant (Isoxsuprine)",
    "vomilast": "Antiemetic Combination (Doxylamine + Pyridoxine + Folic Acid)",
    "zoclar": "Macrolide Antibiotic (Clarithromycin)",
    "zoclar 500": "Macrolide Antibiotic (Clarithromycin)",
    "golite osp": "Herbal / Nutraceutical Supplement",
    "golite osp capsule": "Herbal / Nutraceutical Supplement",
    "pan 40": "Proton Pump Inhibitor (Pantoprazole)",
    "combiflam": "NSAID / Analgesic Combination (Ibuprofen + Paracetamol)",
    "montair": "Leukotriene Receptor Antagonist (Montelukast)",
    "montair lc": "Leukotriene Receptor Antagonist + Antihistamine",
    "augmentin": "Penicillin + Beta-Lactamase Inhibitor (Amoxicillin-Clavulanate)",
    "taxim": "Cephalosporin Antibiotic (Cefotaxime)",
    "taxim o": "Cephalosporin Antibiotic (Cefixime)",
    "metrogyl": "Nitroimidazole Antibiotic (Metronidazole)",
    "flagyl": "Nitroimidazole Antibiotic (Metronidazole)",
    "zenflox": "Fluoroquinolone Antibiotic (Ofloxacin)",
    "ciplox": "Fluoroquinolone Antibiotic (Ciprofloxacin)",
    "dolo 650": "Analgesic / Antipyretic (Paracetamol)",
    "calpol": "Analgesic / Antipyretic (Paracetamol)",
    "crocin": "Analgesic / Antipyretic (Paracetamol)",
    "emeset": "5-HT3 Receptor Antagonist Antiemetic (Ondansetron)",
    "zofer": "5-HT3 Receptor Antagonist Antiemetic (Ondansetron)",
    "allegra": "Non-sedating Antihistamine (Fexofenadine)",
    "rantac": "H2 Receptor Antagonist (Ranitidine)",
    "pantodac": "Proton Pump Inhibitor (Pantoprazole)",
    "omez": "Proton Pump Inhibitor (Omeprazole)",
    "venusia sun aqua": "Sunscreen / Photoprotective Agent",
    "physiogel": "Emollient / Barrier Repair Moisturiser",
    "cetaphil": "Gentle Skin Cleanser / Emollient",
    "abciximab": "Glycoprotein IIb/IIIa Inhibitor (Antiplatelet)",
}


@lru_cache(maxsize=10)
def _load_yaml(filename: str) -> Dict:
    path = TEMPLATE_DIR / filename
    if not path.exists():
        logger.warning(f"Template file not found: {path}")
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class TemplateService:
    """
    Renders explanation, warning, and dosage responses from YAML templates.
    Lookup order: by drug_class → default. Language override applied if available.
    """

    def get_explanation(
        self,
        medicine_name: str,
        drug_class: str = "",
        language: str = "en",
    ) -> Dict[str, str]:
        drug_class = drug_class or _NAME_TO_CLASS.get(medicine_name.lower(), "")
        tmpl = _load_yaml("explanation_templates.yaml")
        data = self._lookup(tmpl, drug_class, language)
        return {
            "explanation": data.get("explanation", tmpl.get("default", {}).get("explanation", "")),
            "use_case": data.get("use_case", tmpl.get("default", {}).get("use_case", "")),
            "mechanism": data.get("mechanism", tmpl.get("default", {}).get("mechanism", "")),
            "how_to_take": data.get("how_to_take", tmpl.get("default", {}).get("how_to_take", "")),
            "source": "template",
        }

    def get_warnings(
        self,
        medicine_name: str,
        drug_class: str = "",
        patient_age: Optional[int] = None,
        causes_drowsiness: bool = False,
    ) -> Dict[str, Any]:
        drug_class = drug_class or _NAME_TO_CLASS.get(medicine_name.lower(), "")
        tmpl = _load_yaml("warning_templates.yaml")
        by_class = tmpl.get("by_drug_class", {}).get(drug_class, {})

        side_effects = by_class.get("side_effects") or tmpl.get("default_side_effects", [])
        serious = by_class.get("serious_side_effects") or tmpl.get("default_serious", [])
        contraindications = by_class.get("contraindications") or tmpl.get("default_contraindications", [])
        drowsy = by_class.get("drowsiness", causes_drowsiness)
        severity = by_class.get("severity", "low")

        age_warnings = []
        if patient_age is not None:
            if patient_age < 2:
                age_warnings.append(tmpl.get("by_drug_class", {}).get(drug_class, {}).get("pediatric_note", tmpl.get("pediatric_general", "")))
            elif patient_age < 12:
                age_warnings.append(tmpl.get("pediatric_general", ""))
            elif patient_age >= 65:
                age_warnings.append(tmpl.get("geriatric_general", ""))
        age_warnings = [w for w in age_warnings if w]

        return {
            "side_effects": side_effects,
            "serious_side_effects": serious,
            "causes_drowsiness": drowsy,
            "drowsiness_note": tmpl.get("drowsiness_warning", "") if drowsy else "",
            "contraindications": contraindications,
            "age_warnings": age_warnings,
            "severity_level": severity,
            "source": "template",
        }

    def get_dosage(
        self,
        medicine_name: str,
        drug_class: str = "",
        patient_age: Optional[int] = None,
    ) -> Dict[str, str]:
        drug_class = drug_class or _NAME_TO_CLASS.get(medicine_name.lower(), "")
        tmpl = _load_yaml("dosage_templates.yaml")
        by_class = tmpl.get("by_drug_class", {}).get(drug_class, {})
        default = tmpl.get("default", {})

        adult = by_class.get("adult") or default.get("adult", "Take as directed.")
        pediatric = by_class.get("pediatric") or default.get("pediatric", "")
        elderly = by_class.get("elderly") or default.get("elderly", "")
        notes = default.get("notes", "")

        # Select age-appropriate dosage
        if patient_age is not None:
            if patient_age < 18 and pediatric:
                dosage_info = pediatric
            elif patient_age >= 65 and elderly:
                dosage_info = elderly
            else:
                dosage_info = adult
        else:
            dosage_info = adult

        return {
            "dosage_info": dosage_info,
            "adult_dose": adult,
            "pediatric_dose": pediatric,
            "elderly_dose": elderly,
            "notes": notes,
            "source": "template",
        }

    def _lookup(self, tmpl: Dict, drug_class: str, language: str) -> Dict:
        # Language override takes highest priority
        lang_overrides = tmpl.get("language_overrides", {})
        if language != "en" and language in lang_overrides:
            lang_data = lang_overrides[language]
            if drug_class and drug_class in lang_data:
                return lang_data[drug_class]
            if "default" in lang_data:
                return lang_data["default"]

        # Drug class match
        if drug_class:
            by_class = tmpl.get("by_drug_class", {})
            if drug_class in by_class:
                return by_class[drug_class]

        return tmpl.get("default", {})
