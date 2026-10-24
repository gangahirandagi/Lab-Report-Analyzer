from app.phase3 import to_fhir_bundle, evaluation_metrics
from app.schemas import ReportAnalysis, LabResult


def test_fhir_export_contains_numeric_observation_and_no_patient_identity():
    analysis = ReportAnalysis(report_date="2026-10-01", results=[LabResult(biomarker="Hemoglobin", value=13.2, unit="g/dL", reference_low=12, reference_high=16)])
    bundle = to_fhir_bundle("12345678-abcd", analysis)
    assert bundle["resourceType"] == "Bundle"
    assert bundle["entry"][0]["resource"]["valueQuantity"]["value"] == 13.2
    assert "Patient" not in str(bundle)


def test_fhir_export_does_not_invent_numeric_value():
    analysis = ReportAnalysis(results=[LabResult(biomarker="Glucose", value=None, value_text="not legible", extraction_status="uncertain")])
    obs = to_fhir_bundle("12345678", analysis)["entry"][0]["resource"]
    assert "valueQuantity" not in obs
    assert obs["valueString"] == "not legible"


def test_evaluation_metrics_are_operational_counts():
    records = [{"analysis": ReportAnalysis(results=[LabResult(biomarker="X", value=None, extraction_status="missing")], warnings=["missing"])}]
    metrics = evaluation_metrics(records)
    assert metrics["saved_reports"] == 1
    assert metrics["missing_numeric_values"] == 1
    assert metrics["reports_requiring_review"] == 1
    assert "not model-accuracy" in metrics["scope_note"]


def test_review_status_persists_in_local_sqlite(tmp_path, monkeypatch):
    from app import storage
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    saved = storage.save_report("synthetic.pdf", ReportAnalysis(results=[LabResult(biomarker="Sodium", value=140, unit="mmol/L")]))
    review = storage.update_review(saved["report_id"], "reviewed", "clinician", "Values checked against source")
    assert review["status"] == "reviewed"
    assert storage.get_review(saved["report_id"])["reviewer"] == "clinician"
