from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class LabResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    biomarker: str = Field(min_length=1, max_length=120)
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_range_text: Optional[str] = None
    lab_flag: Optional[Literal["low", "high", "normal", "critical", "unknown"]] = "unknown"
    extraction_status: Literal["extracted", "missing", "uncertain"] = "extracted"
    source_snippet: Optional[str] = Field(default=None, max_length=300)

class ReportAnalysis(BaseModel):
    report_date: Optional[str] = None
    lab_name: Optional[str] = None
    results: list[LabResult] = Field(default_factory=list)
    summary: str = "Extraction is preliminary; verify all values against the original report."
    warnings: list[str] = Field(default_factory=list)
    needs_human_review: bool = True

class CompareItem(BaseModel):
    biomarker: str
    previous_value: Optional[float] = None
    current_value: Optional[float] = None
    previous_unit: Optional[str] = None
    current_unit: Optional[str] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    status: Literal["comparable", "unit_conflict", "missing_previous", "missing_current", "missing_value"]
    note: str

class CompareResponse(BaseModel):
    previous_report_id: str
    current_report_id: str
    items: list[CompareItem]
    safety_note: str = "Numerical changes are descriptive only and are not a diagnosis."
