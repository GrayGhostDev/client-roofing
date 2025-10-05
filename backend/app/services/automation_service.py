"""
iSwitch Roofs CRM - Automation Service (scaffolding)
Version: 0.1 (stub)
Date: 2025-10-05

This module defines the contract for automation-related workflows.
Implementation will be provided in a subsequent PR (Phase 2B/Phase 4.3).
"""

from __future__ import annotations
from typing import Literal, Optional, List, Dict
from datetime import datetime


class AutomationService:
    """
    Contract for automation workflows (follow-ups, campaigns, escalations).
    """

    def schedule_follow_up(
        self,
        lead_id: str,
        when_utc: datetime,
        channel: Literal["sms", "email", "call"],
        template_id: str,
        actor_user_id: str,
    ) -> str:
        """
        Schedule a follow-up task via the configured channel.

        Returns a task_id.
        """
        raise NotImplementedError("schedule_follow_up is not implemented yet")

    def run_campaign(
        self,
        campaign_key: str,
        lead_ids: List[str],
        start_utc: Optional[datetime] = None,
        dry_run: bool = False,
    ) -> Dict:
        """
        Run or schedule an outbound campaign for a batch of leads.
        """
        raise NotImplementedError("run_campaign is not implemented yet")

    def cancel_scheduled_tasks(self, lead_id: str, campaign_key: Optional[str] = None) -> int:
        """
        Cancel scheduled automation tasks for a given lead and optional campaign.
        Returns the number of cancelled tasks.
        """
        raise NotImplementedError("cancel_scheduled_tasks is not implemented yet")


# Global instance (do not remove; relied upon by planned code paths)
automation_service = AutomationService()
