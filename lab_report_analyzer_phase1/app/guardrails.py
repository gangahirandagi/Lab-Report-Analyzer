from .schemas import ReportAnalysis
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

def validate_analysis(analysis: ReportAnalysis) -> ReportAnalysis:
    warnings = list(analysis.warnings)
    seen = set()
    for item in analysis.results:
        key = item.biomarker.strip().casefold()
        if key in seen:
            warnings.append(f"Duplicate biomarker label detected: {item.biomarker}. Review extraction.")
        seen.add(key)
        if item.value is None:
            if item.extraction_status == "extracted":
                item.extraction_status = "missing"
            warnings.append(f"{item.biomarker}: numeric value is missing or could not be extracted.")
        if item.reference_low is not None and item.reference_high is not None and item.reference_low > item.reference_high:
            warnings.append(f"{item.biomarker}: reference bounds conflict; verify source.")
            item.extraction_status = "uncertain"
        if item.value is not None and not item.unit:
            warnings.append(f"{item.biomarker}: unit missing; interpretation/comparison may be unsafe.")
        if item.reference_low is None and item.reference_high is None and not item.reference_range_text:
            warnings.append(f"{item.biomarker}: reference range not provided by extraction.")
    if not analysis.results:
        warnings.append("No lab values were extracted. Try a clearer report or review manually.")
    analysis.warnings = list(dict.fromkeys(warnings))
    analysis.needs_human_review = True
    return analysis
