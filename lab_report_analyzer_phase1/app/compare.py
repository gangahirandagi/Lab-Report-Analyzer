from .schemas import ReportAnalysis, CompareItem, CompareResponse

def compare_reports(previous_id: str, previous: ReportAnalysis, current_id: str, current: ReportAnalysis) -> CompareResponse:
    prev = {r.biomarker.strip().casefold(): r for r in previous.results}
    curr = {r.biomarker.strip().casefold(): r for r in current.results}
    items = []
    for key in sorted(set(prev) | set(curr)):
        p, c = prev.get(key), curr.get(key)
        label = (c or p).biomarker
        if p is None:
            items.append(CompareItem(biomarker=label, current_value=c.value, current_unit=c.unit, status="missing_previous", note="No matching biomarker found in previous report."))
        elif c is None:
            items.append(CompareItem(biomarker=label, previous_value=p.value, previous_unit=p.unit, status="missing_current", note="No matching biomarker found in current report."))
        elif p.value is None or c.value is None:
            items.append(CompareItem(biomarker=label, previous_value=p.value, current_value=c.value, previous_unit=p.unit, current_unit=c.unit, status="missing_value", note="One or both numeric values are missing; no change calculated."))
        elif not p.unit or not c.unit or p.unit.strip().casefold() != c.unit.strip().casefold():
            items.append(CompareItem(biomarker=label, previous_value=p.value, current_value=c.value, previous_unit=p.unit, current_unit=c.unit, status="unit_conflict", note="Units differ or are missing. No conversion or comparison was attempted."))
        else:
            change = c.value - p.value
            pct = change / abs(p.value) * 100 if p.value != 0 else None
            items.append(CompareItem(biomarker=label, previous_value=p.value, current_value=c.value, previous_unit=p.unit, current_unit=c.unit, change=round(change, 6), change_percent=round(pct, 2) if pct is not None else None, status="comparable", note="Descriptive arithmetic only; verify the original reports."))
    return CompareResponse(previous_report_id=previous_id, current_report_id=current_id, items=items)
