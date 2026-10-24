from app.schemas import ReportAnalysis, LabResult
from app.guardrails import validate_analysis

def test_missing_value_gets_warning():
    a=validate_analysis(ReportAnalysis(results=[LabResult(biomarker="Sodium",value=None,unit="mmol/L")]))
    assert a.needs_human_review and any("missing" in w.lower() for w in a.warnings)

def test_bad_reference_bounds_are_flagged():
    a=validate_analysis(ReportAnalysis(results=[LabResult(biomarker="X",value=2,reference_low=10,reference_high=1)]))
    assert any("bounds conflict" in w for w in a.warnings)
