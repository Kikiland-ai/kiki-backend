"""Async Gemini adapter. A model finding is a candidate, never checkpoint evidence."""

import base64
import json
import os
import re
import time

import httpx
from pydantic import ValidationError

from contracts.lab_tracking import LabAnalysis
from .definition import DEFINITION
from .procedure import PROCEDURES, OBSERVER_PROMPT, OBSERVER_VERSION

MODEL = "gemini-3.5-flash-lite"
PROMPT_VERSION = OBSERVER_VERSION
PROMPT = OBSERVER_PROMPT


from .provider import AnalysisFailure, ProviderPool


def generation_config(model, schema, tokens=2600):
    if not re.fullmatch(r"[a-z0-9.-]+", model):
        raise AnalysisFailure("invalid_model_configuration")
    return {"maxOutputTokens": tokens, "thinkingConfig": {"thinkingLevel": "minimal" if "flash-lite" in model else "low"},
            "responseMimeType": "application/json", "responseJsonSchema": schema}


class AnalysisFindings(dict):
    """Validated findings with private per-request metrics outside model JSON."""
    def __init__(self, value, metrics):
        super().__init__(value)
        self.metrics = metrics


def build_request(pixels, checkpoint, state, model=MODEL):
    schema = LabAnalysis.model_json_schema()
    schema["$defs"]["CriterionFinding"]["properties"]["criterion_id"]["enum"] = [c["id"] for c in checkpoint["completion_criteria"]]
    schema["$defs"]["ActionFinding"]["properties"]["action_id"]["enum"] = [a["id"] for a in PROCEDURES[checkpoint["id"]]]
    schema["required"].append("action_findings")
    context = {"procedure": PROCEDURES[checkpoint["id"]],"checkpoint": checkpoint, "condition": state["workspace"]["condition"],
               "selected_model_name": state['workspace'].get('model_name'),
               "authored_model": DEFINITION["model"],
               "accepted_current_criteria": [c["criterion_id"] for c in state["steps"][checkpoint["id"]]["criteria"] if c["state"] == "satisfied" and c.get('completion_basis') not in ('screen_inferred','student_report_unassessed')],
               "student_reports": [r for r in state["responses"] if r["visit_id"] == state["current_visit_id"]][-2:]}
    return {"systemInstruction": {"parts": [{"text": PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps(context)},
                         {"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(pixels).decode()}}]}],
            "generationConfig": generation_config(model, schema, 2600)}


def validate_result(value, checkpoint):
    try:
        result = LabAnalysis.model_validate(value)
    except ValidationError:
        raise AnalysisFailure("invalid_output") from None
    ids = [v.criterion_id for v in result.criteria]
    action_ids = [v.action_id for v in result.action_findings]
    if (not result.summary.strip() or len(ids) != len(set(ids))
            or set(ids) != {c["id"] for c in checkpoint["completion_criteria"]}
            or any(len(v) > 150 for v in result.uncertainties)
            or any(v.status != 'unknown' and not v.evidence.strip() for v in [*result.criteria, *result.action_findings])
            or (action_ids and (len(action_ids) != len(set(action_ids)) or set(action_ids) != {a['id'] for a in PROCEDURES[checkpoint['id']]}))):
        raise AnalysisFailure("invalid_output")
    return result.model_dump()


class GeminiAnalyzer:
    model = MODEL
    prompt_version = PROMPT_VERSION

    def __init__(self, api_key=None, transport=None, model=None):
        self.model = model or os.environ.get("GEMINI_LAB_MODEL") or os.environ.get("GEMINI_SCREEN_MODEL") or MODEL
        self.api_key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY", "")
        self.transport = transport
        self.provider = ProviderPool(api_key=api_key, transport=transport)

    @property
    def configured(self):
        return self.provider.configured

    async def analyze(self, pixels, checkpoint, state):
        if not self.configured:
            raise AnalysisFailure("provider_not_configured")
        try:
            started=time.monotonic()
            response = await self.provider.post(self.model, build_request(pixels, checkpoint, state, self.model))
            provider_ms=round((time.monotonic()-started)*1000)
            raw = response.json()
            candidate = raw.get("candidates", [{}])[0]
            if candidate.get("finishReason") != "STOP":
                raise AnalysisFailure("incomplete_output")
            text = "".join(p["text"] for p in candidate.get("content", {}).get("parts", []) if isinstance(p.get("text"), str) and not p.get("thought"))
            return AnalysisFindings(validate_result(json.loads(text), checkpoint), {"provider_ms":provider_ms,"output_tokens":raw.get("usageMetadata",{}).get("candidatesTokenCount"),"wire_format":"lab-observer-json/v3"})
        except AnalysisFailure:
            raise
        except (httpx.HTTPError, TimeoutError):
            raise AnalysisFailure("provider_timeout_or_network_error") from None
        except (ValueError, KeyError, TypeError, IndexError):
            raise AnalysisFailure("invalid_output") from None
