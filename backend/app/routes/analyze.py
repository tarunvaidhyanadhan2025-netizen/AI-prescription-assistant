import os

from fastapi import APIRouter, UploadFile, File

from app.agents.ocr_agent import OCRAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.explanation_agent import ExplanationAgent

from app.services.medicine_service import MedicineService

from app.config.settings import settings

router = APIRouter(
    prefix="/analyze",
    tags=["Analyze"]
)

medicine_service = MedicineService()


@router.post("/")
async def analyze_prescription(
    file: UploadFile = File(...)
):

    upload_path = os.path.join(
        settings.UPLOAD_DIR,
        file.filename
    )

    with open(upload_path, "wb") as f:
        f.write(await file.read())

    extracted_text = OCRAgent.run(upload_path)

    medicines = medicine_service.extract_medicines(
        extracted_text
    )

    results = []

    for med in medicines:

        explanation = ExplanationAgent.generate(med)

        safety = SafetyAgent.analyze(med)

        results.append({
            "medicine": med,
            "explanation": explanation,
            "safety": safety
        })

    return {
        "extracted_text": extracted_text,
        "results": results
    }
