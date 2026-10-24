import io, logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
import fitz
from .schemas import ReportAnalysis
from .guardrails import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
from .workflow import run_guarded_analysis
from .medgemma import MedGemmaService
from .compare import compare_reports
from . import storage
from .knowledge import answer_from_report
from .phase3 import to_fhir_bundle, evaluation_metrics
from pydantic import BaseModel, Field
from typing import Literal, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lab-analyzer")
app = FastAPI(title="Lab Report Analyzer Agent — Phases 2–4", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
model_service = MedGemmaService()
FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/", response_class=HTMLResponse)
def home(): return (FRONTEND / "index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health(): return {"status":"ok", "model":model_service.status(), "history":"local SQLite; consent required to save", "orchestration":"LangGraph" if __import__("app.workflow", fromlist=["LANGGRAPH_AVAILABLE"]).LANGGRAPH_AVAILABLE else "deterministic fallback"}

def to_image(data: bytes, suffix: str) -> Image.Image:
    if suffix == ".pdf":
        try:
            doc = fitz.open(stream=data, filetype="pdf")
            if len(doc) == 0: raise ValueError("PDF has no pages")
            pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not read PDF first page.")
    try: return Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError): raise HTTPException(status_code=400, detail="Image is invalid or unreadable.")

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), consent_to_store: bool = Form(False)):
    filename = Path(file.filename or "upload").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS: raise HTTPException(status_code=415, detail="Only PDF, PNG, JPG, JPEG, and WEBP are supported.")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if not data: raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES: raise HTTPException(status_code=413, detail="File exceeds 10 MB limit.")
    image = to_image(data, suffix)
    if not model_service.enabled: raise HTTPException(status_code=503, detail="MedGemma is disabled. Set USE_MEDGEMMA=true and restart for real extraction.")
    try: analysis = run_guarded_analysis(model_service.analyze_image(image))
    except Exception as exc:
        logger.warning("Analysis failed (%s); report content intentionally not logged.", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Analysis failed. Check model access, dependencies, and available memory; verify report manually.")
    if consent_to_store: return storage.save_report(filename, analysis)
    return {"report_id":None, "filename":filename, "created_at":None, "analysis":analysis, "stored":False, "message":"Not stored because consent_to_store was false."}

@app.get("/api/reports")
def reports(): return storage.list_reports()

@app.get("/api/reports/{report_id}")
def report(report_id: str):
    result = storage.get_report(report_id)
    if not result: raise HTTPException(status_code=404, detail="Report not found in consented local history.")
    return result

@app.post("/api/compare")
def compare(payload: dict):
    prev_id, curr_id = payload.get("previous_report_id"), payload.get("current_report_id")
    if not prev_id or not curr_id: raise HTTPException(status_code=400, detail="previous_report_id and current_report_id are required.")
    prev, curr = storage.get_report(prev_id), storage.get_report(curr_id)
    if not prev or not curr: raise HTTPException(status_code=404, detail="Both reports must exist in consented local history.")
    return compare_reports(prev_id, prev["analysis"], curr_id, curr["analysis"])

@app.post("/api/chat")
def chat(payload: dict):
    report_id, question = payload.get("report_id"), payload.get("question", "")
    if not report_id or not isinstance(question, str) or not question.strip(): raise HTTPException(status_code=400, detail="report_id and non-empty question are required.")
    if len(question) > 1000: raise HTTPException(status_code=413, detail="Question must be 1000 characters or fewer.")
    record = storage.get_report(report_id)
    if not record: raise HTTPException(status_code=404, detail="Report not found in consented local history.")
    return answer_from_report(record["analysis"], question.strip())

@app.get("/api/trends/{report_id}")
def trends(report_id: str, biomarker: str):
    record = storage.get_report(report_id)
    if not record: raise HTTPException(status_code=404, detail="Report not found.")
    found = [r for r in record["analysis"].results if r.biomarker.casefold() == biomarker.casefold()]
    if not found: raise HTTPException(status_code=404, detail="Biomarker not found in this report.")
    r = found[0]
    return {"biomarker":r.biomarker,"value":r.value,"unit":r.unit,"reference_low":r.reference_low,"reference_high":r.reference_high,"note":"Single-report point only. Comparison is descriptive, not a clinical interpretation."}


class TranslationRequest(BaseModel):
    summary: str = Field(min_length=1, max_length=5000)
    language: Literal["English", "Hindi", "Kannada", "Tamil", "Telugu", "Marathi", "Bengali", "Spanish", "French"]

class ReviewRequest(BaseModel):
    status: Literal["pending", "in_review", "reviewed", "needs_correction"]
    reviewer: Optional[str] = Field(default=None, max_length=120)
    note: Optional[str] = Field(default=None, max_length=2000)

@app.post("/api/translate")
def translate(payload: TranslationRequest):
    try:
        return {"language": payload.language, "translated_summary": model_service.translate_summary(payload.summary, payload.language), "warning": "Translation may be inaccurate. Verify all values, units, and medical wording against the original report."}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

@app.get("/api/reports/{report_id}/fhir")
def export_fhir(report_id: str):
    record = storage.get_report(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found in consented local history.")
    return to_fhir_bundle(report_id, record["analysis"])

@app.get("/api/reports/{report_id}/review")
def get_review(report_id: str):
    if not storage.get_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found in consented local history.")
    return storage.get_review(report_id)

@app.put("/api/reports/{report_id}/review")
def set_review(report_id: str, payload: ReviewRequest):
    result = storage.update_review(report_id, payload.status, payload.reviewer, payload.note)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found in consented local history.")
    return result

@app.get("/api/evaluation")
def evaluation():
    records = []
    for row in storage.list_reports():
        record = storage.get_report(row["report_id"])
        if record:
            records.append(record)
    return evaluation_metrics(records)
