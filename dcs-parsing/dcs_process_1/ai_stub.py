#!/usr/bin/env python3
"""Stands in for the AI backend in the trial repo.

The real job authenticates by Workload Identity Federation, and federation rules are scoped to
the repository they were issued for -- so the genuine backend cannot run here. validate.py
already treats $DCS_VALIDATOR_AI_CMD as its highest-priority backend, so pointing that at this
script exercises the whole path (prompt built, answer parsed, diagnosis rendered, comment
posted) with no credentials anywhere.
"""
import json
import sys

sys.stdin.read()
print(json.dumps({
    "cause": "stubbed backend: this text came from ai_stub.py, not from a model",
    "fix": "n/a -- the trial repo proves the plumbing, not the model output",
    "corrected_lines": [],
    "rollback_advice": "n/a in the trial repo",
    "confidence": "low",
}))
