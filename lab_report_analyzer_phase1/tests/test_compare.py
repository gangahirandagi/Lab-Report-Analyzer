from app.schemas import ReportAnalysis, LabResult
from app.compare import compare_reports

def test_same_units_comparison():
    old=ReportAnalysis(results=[LabResult(biomarker="Hemoglobin",value=12,unit="g/dL")])
    new=ReportAnalysis(results=[LabResult(biomarker="Hemoglobin",value=13,unit="g/dL")])
    item=compare_reports("old",old,"new",new).items[0]
    assert item.status=="comparable" and item.change==1 and item.change_percent==8.33

def test_unit_conflict_does_not_convert():
    old=ReportAnalysis(results=[LabResult(biomarker="Glucose",value=90,unit="mg/dL")])
    new=ReportAnalysis(results=[LabResult(biomarker="Glucose",value=5,unit="mmol/L")])
    item=compare_reports("old",old,"new",new).items[0]
    assert item.status=="unit_conflict" and item.change is None
