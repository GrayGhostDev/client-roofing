"""
iSwitch Roofs CRM - 16-Touch Follow-Up Campaign (scaffolding)
Version: 0.1 (stub)
Date: 2025-10-05

Naming note:
- The root TODO referenced `backend/app/workflows/16_touch_campaign.py`. Python modules
  cannot start with a digit, so this scaffold is created as `touch_16_campaign.py`.

Contract:
- run_for_lead(lead_id: str, context: dict) -> dict
- enqueue_for_segment(segment_filter: dict) -> str

Behavioral notes (from TODO.md):
- Day 1: Immediate response (2 minutes)
- Day 1: Follow-up email (4 hours later)
- Day 2: SMS check-in
- Day 3: Value proposition email
- Day 5: Case study email
- Day 7: Phone call
- Day 10: Limited-time offer email
- Day 14: Educational content
- Day 17: Testimonial showcase
- Day 21: Phone call #2
- Day 25: Referral request
- Day 30: Final offer email
- Day 35: Break-up email
- Day 40: Last chance email
- Day 60: Re-engagement attempt
- Day 90: Cold lead nurture

Feature flags:
- Enable/disable via Config (e.g., ENABLE_AUTOMATED_FOLLOW_UP)
"""

from __future__ import annotations
from typing import Dict


def run_for_lead(lead_id: str, context: Dict) -> Dict:
    """Execute (or simulate) the 16-touch workflow for a single lead.

    Returns a result payload (e.g., queued tasks), but is not yet implemented.
    """
    raise NotImplementedError("run_for_lead is not implemented yet")


def enqueue_for_segment(segment_filter: Dict) -> str:
    """Enqueue the workflow for a segment of leads matching filters.

    Returns a batch/job id, but is not yet implemented.
    """
    raise NotImplementedError("enqueue_for_segment is not implemented yet")
