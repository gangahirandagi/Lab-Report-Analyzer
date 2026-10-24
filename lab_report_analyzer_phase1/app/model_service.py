import json
import re
import os
from functools import lru_cache
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForMultimodalLM

MODEL_ID = os.getenv("MEDGEMMA_MODEL_ID", "google/medgemma-1.5-4b-it")

PROMPT = """
Extract visible laboratory results from this report for a software prototype.
Transcribe only what is visible. Do not diagnose or recommend treatment.
Never invent missing values, units, reference intervals, flags, or dates.
Preserve values and units exactly as printed. Use null for unreadable or missing fields.
Return ONLY valid JSON:
{"results":[{"test_name":"exact name","value_text":"exact value or null",
"numeric_value":12.3,"unit":"unit or null","reference_range_text":"printed range or null",
"lab_flag":"printed flag or null","collection_date":"printed date or null",
"source_page":1,"extraction_confidence":"high|medium|low|unknown"}]}
If nothing is readable, return {"results":[]}.
"""

@lru_cache(maxsize=1)
def load_model():
    # CPU inference is intentional for this machine; expect slow generation and high RAM use.
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForMultimodalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, low_cpu_mem_usage=True, device_map="cpu"
    )
    model.eval()
    return processor, model

def _parse_json(text):
    cleaned = re.sub(r"^```(?:json)?\\s*|\\s*```$", "", text.strip(), flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end+1])
        raise ValueError("Model did not return valid JSON; retry with a clearer report image.")

def extract_from_image(image: Image.Image):
    processor, model = load_model()
    messages = [{"role": "user", "content": [
        {"type": "image", "image": image.convert("RGB")},
        {"type": "text", "text": PROMPT}
    ]}]
    inputs = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True,
        return_dict=True, return_tensors="pt"
    )
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=1200, do_sample=False)
    prompt_len = inputs["input_ids"].shape[-1]
    decoded = processor.decode(output[0][prompt_len:], skip_special_tokens=True)
    parsed = _parse_json(decoded)
    results = parsed.get("results", [])
    if not isinstance(results, list):
        raise ValueError("Unexpected results structure from model.")
    return results, decoded
