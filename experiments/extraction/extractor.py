"""
NuExtract-3 extractor: prompt construction, vLLM call, and output parsing.

Given a document (page images OR text) + a list of field names, build a
verbatim-extraction prompt, call the vLLM OpenAI-compatible server, and return
`(extracted_dict, metrics_dict)`.

Prompt + parsing are adapted from the proven NER harness (`NTP/NER/vlm_runner.py`):
low-temperature verbatim extraction, "return ONLY a JSON object, null if absent".
This runs on any instruction-capable VLM; NuExtract 3 is Qwen3.5-VL-based, so it
applies directly. (NuExtract's native JSON template is an optional enhancement.)
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import time
from pathlib import Path
from typing import Any

import requests

import config

# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #
_PROMPT_TEMPLATE = """\
### Instruction:

You are an AI specialized in entity extraction from documents. Your task is to \
extract specific fields from the document using verbatim extraction principles.

### Critical extraction principles:

1. VERBATIM EXTRACTION: For every field, the value must be a character-for-character, \
verbatim copy of the text as it appears in the document. Do not paraphrase, reformat, \
normalize, or correct values.
2. FIELD VALUE, NOT THE LABEL: Extract the value associated with a field, never the \
field's printed label/caption.
3. MISSING FIELDS: If a field is not present in the document, set its value to null. \
Do not guess or hallucinate.
4. NO EXTRA FIELDS: Only extract the fields listed below; do not invent new keys.

### Fields to extract:
{fields_block}

### Output format:
Return ONLY a single valid JSON object mapping each field name to its extracted value \
(a string) or null if absent. No commentary, no markdown fences.
Example: {{"Field One": "value from document", "Field Two": null, "Total": "1,234.56"}}
"""


def build_prompt(fields: list[str]) -> str:
    return _PROMPT_TEMPLATE.format(fields_block="\n".join(f"  - {f}" for f in fields))


# --------------------------------------------------------------------------- #
# Output parsing
# --------------------------------------------------------------------------- #
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_MISSING = {"", "null", "none", "n/a", "na", "-", "not found", "not present"}


def parse_json_from_output(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    text = _THINK_RE.sub("", raw).strip()
    m = _FENCE_RE.search(text)
    if m:
        text = m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def clean_values(d: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for f in fields:
        v = d.get(f)
        if isinstance(v, str):
            vs = v.strip()
            v = None if vs.lower() in _MISSING else vs
        out[f] = v
    return out


# --------------------------------------------------------------------------- #
# vLLM client (OpenAI-compatible)
# --------------------------------------------------------------------------- #
def _image_to_data_url(path: str | Path) -> str:
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def extract(
    fields: list[str],
    *,
    images: list[str | Path] | None = None,
    text: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Run extraction for one document. Pass EITHER `images` (page-image paths) OR
    `text`. Returns (extracted_dict, metrics_dict); on failure ({}, {...,"error":...}).
    """
    if not images and not text:
        raise ValueError("extract() needs either images or text")

    prompt = build_prompt(fields)
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    if images:
        for img in images:
            content.append({"type": "image_url", "image_url": {"url": _image_to_data_url(img)}})
    else:
        # Cap very long documents so prompt+text stays under the context window.
        if text and len(text) > config.MAX_INPUT_CHARS:
            text = text[: config.MAX_INPUT_CHARS]
        content[0]["text"] = f"{prompt}\n\n### Document text:\n{text}"

    payload = {
        "model": config.MODEL_ID,
        "messages": [{"role": "user", "content": content}],
        "temperature": config.GEN_TEMPERATURE,
        "top_p": config.GEN_TOP_P,
        "max_tokens": config.GEN_MAX_TOKENS,
    }
    url = f"{config.SERVER_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {config.SERVER_API_KEY}"}

    t0 = time.perf_counter()
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {}, {"latency_s": round(time.perf_counter() - t0, 3), "error": str(e)}
    latency = time.perf_counter() - t0

    raw = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
    parsed = parse_json_from_output(raw)
    extracted = clean_values(parsed, fields)
    usage = data.get("usage", {}) or {}
    metrics = {
        "latency_s": round(latency, 3),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "parse_ok": bool(parsed),
    }
    return extracted, metrics


def health_ok() -> bool:
    """True if the vLLM server answers /v1/models."""
    try:
        return requests.get(f"{config.SERVER_BASE_URL}/models", timeout=5).ok
    except Exception:
        return False
