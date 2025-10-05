"""
iSwitch Roofs CRM - Review Automation Workflow (scaffolding)
Version: 0.1 (stub)
Date: 2025-10-05

Contract:
- run_for_lead(lead_id: str, context: dict) -> dict
- enqueue_for_segment(segment_filter: dict) -> str

Behavioral notes (from TODO.md):
- Trigger review request N days after project completion (default 3)
- Reminders if no review after 7 and 14 days
- Internal alert if negative review received
- Automated thank you for positive reviews

Feature flags:
- Controlled via Config flags (e.g., ENABLE_EMAIL_CAMPAIGNS, ENABLE_SMS_NOTIFICATIONS)
"""

from __future__ import annotations
from typing import Dict


def run_for_lead(lead_id: str, context: Dict) -> Dict:
    """Execute (or simulate) the review automation for a single lead/customer."""
    raise NotImplementedError("run_for_lead is not implemented yet")


def enqueue_for_segment(segment_filter: Dict) -> str:
    """Enqueue the review automation workflow for a segment."""
    raise NotImplementedError("enqueue_for_segment is not implemented yet")
