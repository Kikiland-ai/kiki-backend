"""Dependency-free, request-local opt-in; control imports no drawing validators."""
from contextvars import ContextVar
DRAWING_RUN = ContextVar('drawing_run', default=None)
MODEL_CONTRACT = 'lab-observer-drawing/v1'
PROMPT_VERSION = 'dsb-step-observer/v5-drawing1'
