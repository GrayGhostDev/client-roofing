"""
iSwitch Roofs CRM - Referral Automation Workflow (scaffolding)
Version: 0.1 (stub)
Date: 2025-10-05

Contract:
- run_for_lead(lead_id: str, context: dict) -> dict
- enqueue_for_segment(segment_filter: dict) -> str

Behavioral notes (from TODO.md):
- Request referral 7 days after positive review
- Track referral rewards; send thank you messages
- Referral status updates

Feature flags:
- Controlled via Config flags (e.g., ENABLE_EMAIL_CAMPAIGNS)
"""

from __future__ import annotations
from typing import Dict


def run_for_lead(lead_id: str, context: Dict) -> Dict:
    """Execute (or simulate) the referral automation for a single lead/customer."""
    raise NotImplementedError("run_for_lead is not implemented yet")


def enqueue_for_segment(segment_filter: Dict) -> str:
    """Enqueue the referral automation workflow for a segment."""
    raise NotImplementedError("enqueue_for_segment is not implemented yet")
