import re

def _to_number(item):
    if item.get("numeric_value") is not None:
        try:
            return float(item["numeric_value"])
        except (TypeError, ValueError):
            return None
    value = item.get("value_text")
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if re.fullmatch(r"[-+]?\\d+(?:\\.\\d+)?", value):
            return float(value)
    return None

def validate_results(items):
    checked = []
    for item in items:
        result = dict(item)
        reasons = []
        if not result.get("test_name"):
            result["test_name"] = "UNKNOWN"
            reasons.append("Test name missing or unreadable")
        if result.get("value_text") is None and result.get("numeric_value") is None:
            reasons.append("Value missing or unreadable")
        if not result.get("unit"):
            reasons.append("Unit missing; verify against source report")
        if not result.get("reference_range_text"):
            reasons.append("Reference range missing or not extracted")
        if result.get("extraction_confidence", "unknown") in ("low", "unknown"):
            reasons.append("Low or unknown extraction confidence")
        result["numeric_value"] = _to_number(result)
        # No generic normal/abnormal inference: ranges depend on lab and clinical context.
        result["review_required"] = bool(reasons)
        result["review_reason"] = "; ".join(reasons) if reasons else None
        checked.append(result)
    return checked
