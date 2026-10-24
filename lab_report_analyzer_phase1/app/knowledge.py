import json
from pathlib import Path
REFERENCE_PATH = Path(__file__).resolve().parent.parent / "data" / "curated_references.json"

def answer_from_report(analysis, question: str) -> dict:
    q = question.casefold()
    matches = [r for r in analysis.results if r.biomarker.casefold() in q]
    refs = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    notes = [r["text"] for r in refs if any(term in q for term in r.get("keywords", []))]
    values = []
    for r in matches:
        value = r.value_text if r.value_text is not None else (str(r.value) if r.value is not None else "not extracted")
        values.append({"biomarker": r.biomarker, "value": value, "unit": r.unit,
                       "reference_range": r.reference_range_text or (f"{r.reference_low}–{r.reference_high}" if r.reference_low is not None and r.reference_high is not None else None),
                       "lab_flag": r.lab_flag, "extraction_status": r.extraction_status})
    if not values and not notes:
        answer = "I couldn't ground that question in a matching extracted biomarker or curated note. Specify a biomarker or ask a clinician."
    else:
        answer = "I can summarize stored report data, but I cannot diagnose or recommend treatment. Verify values and ranges against the original report."
    return {"answer": answer, "report_values": values, "curated_notes": notes,
            "guardrail": "Not for diagnosis or treatment. Ask a qualified clinician for interpretation."}
