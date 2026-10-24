"""Phase 3 helpers: FHIR R4 export, evaluation metrics, and review workflow utilities."""
from datetime import datetime, timezone
from typing import Any
from .schemas import ReportAnalysis

FHIR_SYSTEM = "https://labwise.local/CodeSystem/biomarker"


def to_fhir_bundle(report_id: str, analysis: ReportAnalysis) -> dict[str, Any]:
    """Build a minimal FHIR R4 transaction-independent collection Bundle.

    Patient identity is intentionally omitted because the app does not collect a verified
    patient identity. Numeric values are exported only when an explicit unit is present.
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    entries = []
    for index, result in enumerate(analysis.results, start=1):
        observation = {
            "resourceType": "Observation",
            "id": f"{report_id[:8]}-{index}",
            "status": "preliminary",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory", "display": "Laboratory"}]}],
            "code": {"coding": [{"system": FHIR_SYSTEM, "code": result.biomarker.strip().lower().replace(" ", "-"), "display": result.biomarker}], "text": result.biomarker},
            "note": [{"text": "AI-extracted preliminary value; verify against source report. Not clinically validated."}],
        }
        if result.value is not None and result.unit:
            observation["valueQuantity"] = {"value": result.value, "unit": result.unit, "system": "http://unitsofmeasure.org", "code": result.unit}
        elif result.value_text:
            observation["valueString"] = result.value_text
        if result.reference_low is not None or result.reference_high is not None:
            bound = {}
            if result.reference_low is not None:
                bound["low"] = {"value": result.reference_low, "unit": result.unit or "unknown", "system": "http://unitsofmeasure.org", "code": result.unit or "unknown"}
            if result.reference_high is not None:
                bound["high"] = {"value": result.reference_high, "unit": result.unit or "unknown", "system": "http://unitsofmeasure.org", "code": result.unit or "unknown"}
            observation["referenceRange"] = [bound]
        if analysis.report_date:
            observation["effectiveDateTime"] = analysis.report_date
        entries.append({"fullUrl": f"urn:uuid:{report_id[:8]}-{index}", "resource": observation})
    return {"resourceType": "Bundle", "type": "collection", "timestamp": now, "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Bundle"]}, "entry": entries}


def evaluation_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    analyses = [r.get("analysis") for r in records if r.get("analysis") is not None]
    values = [v for a in analyses for v in a.results]
    return {
        "saved_reports": len(analyses),
        "biomarkers_extracted": len(values),
        "reports_requiring_review": sum(bool(a.needs_human_review or a.warnings or any(x.extraction_status != "extracted" for x in a.results)) for a in analyses),
        "reports_with_warnings": sum(bool(a.warnings) for a in analyses),
        "missing_numeric_values": sum(x.value is None for x in values),
        "uncertain_extractions": sum(x.extraction_status == "uncertain" for x in values),
        "scope_note": "Operational counts only. These are not model-accuracy, sensitivity, or clinical-validation metrics.",
    }
