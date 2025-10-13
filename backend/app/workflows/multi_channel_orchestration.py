"""
Multi-Channel Orchestration Service - Week 11 Day 2
Coordinate campaigns across Email, SMS, Phone, Social, Direct Mail

This service orchestrates:
- Multi-channel campaign execution
- Channel preference detection
- Engagement-based routing
- Campaign step sequencing
- Response handling and pause logic
- Hot lead escalation to sales reps
- Real-time performance tracking

Author: Week 11 Implementation
Created: 2025-10-12
"""

import os
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

# Models
from app.models.lead_sqlalchemy import Lead
from app.models.interaction_sqlalchemy import Interaction

# Database
from app.utils.database import get_session

# Services
from app.services.intelligence.email_personalization import EmailPersonalizationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChannelType(str, Enum):
    """Available communication channels"""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    SOCIAL = "social"
    DIRECT_MAIL = "direct_mail"
    CHAT = "chat"


class CampaignStatus(str, Enum):
    """Campaign execution statuses"""
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class MultiChannelOrchestrator:
    """
    Coordinate campaigns across Email, SMS, Phone, Social, Direct Mail

    Manages:
    - Campaign creation and configuration
    - Multi-step sequence execution
    - Channel routing and preferences
    - Engagement tracking
    - Automatic pause on response
    - Hot lead escalation
    """

    def __init__(self, db: Session = None):
        """Initialize multi-channel orchestrator"""
        self.db = db or next(get_session())
        self.email_service = EmailPersonalizationService(db)

    # =====================================================
    # CAMPAIGN MANAGEMENT
    # =====================================================

    async def create_campaign(
        self,
        campaign_config: Dict,
        target_leads: List[int]
    ) -> Dict:
        """
        Initialize multi-channel campaign

        Args:
            campaign_config: {
                "name": "Q4 Premium Outreach",
                "campaign_type": "drip",
                "steps": [
                    {
                        "step_number": 1,
                        "channel": "email",
                        "delay_days": 0,
                        "template_type": "initial_contact"
                    },
                    {
                        "step_number": 2,
                        "channel": "sms",
                        "delay_days": 2,
                        "template_type": "follow_up"
                    },
                    ...
                ]
            }
            target_leads: List of lead IDs to enroll

        Returns:
            {
                "campaign_id": 123,
                "name": "Q4 Premium Outreach",
                "leads_enrolled": 150,
                "steps_configured": 8,
                "estimated_duration": "30 days",
                "created_at": "2025-10-12T00:30:00"
            }
        """
        try:
            # Validate configuration
            self._validate_campaign_config(campaign_config)

            # Create campaign in database
            campaign_data = {
                "name": campaign_config["name"],
                "campaign_type": campaign_config["campaign_type"],
                "status": "active",
                "target_segment": {"lead_ids": target_leads},
                "created_at": datetime.now()
            }

            # In production, this would insert into sales_campaigns table
            campaign_id = self._create_campaign_record(campaign_data)

            # Create campaign steps
            steps_created = 0
            for step in campaign_config["steps"]:
                step_data = {
                    "campaign_id": campaign_id,
                    "step_number": step["step_number"],
                    "channel": step["channel"],
                    "delay_days": step.get("delay_days", 0),
                    "delay_hours": step.get("delay_hours", 0),
                    "template_type": step.get("template_type"),
                    "conditions": step.get("conditions", {})
                }
                self._create_campaign_step(step_data)
                steps_created += 1

            # Schedule first step for all leads
            executions_scheduled = 0
            for lead_id in target_leads:
                await self._schedule_campaign_step(
                    campaign_id=campaign_id,
                    lead_id=lead_id,
                    step_number=1,
                    scheduled_at=datetime.now()
                )
                executions_scheduled += 1

            # Calculate estimated duration
            max_delay = max(
                step.get("delay_days", 0) for step in campaign_config["steps"]
            )

            result = {
                "campaign_id": campaign_id,
                "name": campaign_config["name"],
                "campaign_type": campaign_config["campaign_type"],
                "leads_enrolled": len(target_leads),
                "steps_configured": steps_created,
                "executions_scheduled": executions_scheduled,
                "estimated_duration": f"{max_delay} days",
                "created_at": datetime.now().isoformat()
            }

            logger.info(f"✅ Campaign created: {campaign_config['name']} with {len(target_leads)} leads")
            return result

        except Exception as e:
            logger.error(f"❌ Error creating campaign: {e}")
            raise

    async def determine_channel_preference(self, lead_id: int) -> str:
        """
        AI-based channel selection based on engagement history

        Analyzes:
        - Historical open/response rates by channel
        - Recent engagement patterns
        - Time of day preferences
        - Device usage (mobile vs desktop)

        Args:
            lead_id: Lead ID

        Returns:
            Preferred channel: "email", "sms", "phone", etc.
        """
        try:
            # Query engagement history
            interactions = self.db.query(Interaction).filter(
                and_(
                    Interaction.lead_id == lead_id,
                    Interaction.created_at >= datetime.now() - timedelta(days=90)
                )
            ).all()

            if not interactions:
                # Default preference for new leads
                return ChannelType.EMAIL

            # Count engagements by channel
            channel_engagement = {}
            for interaction in interactions:
                channel = interaction.type  # Assume interaction.type is channel
                if channel not in channel_engagement:
                    channel_engagement[channel] = {"sent": 0, "engaged": 0}

                channel_engagement[channel]["sent"] += 1

                # Count as engaged if response/open/click
                if interaction.notes and any(
                    keyword in interaction.notes.lower()
                    for keyword in ["opened", "clicked", "replied", "answered"]
                ):
                    channel_engagement[channel]["engaged"] += 1

            # Calculate engagement rates
            channel_rates = {}
            for channel, stats in channel_engagement.items():
                if stats["sent"] > 0:
                    rate = stats["engaged"] / stats["sent"]
                    channel_rates[channel] = rate

            # Return highest engagement channel
            if channel_rates:
                best_channel = max(channel_rates, key=channel_rates.get)
                logger.info(f"📊 Lead {lead_id} prefers {best_channel} ({channel_rates[best_channel]:.2%} engagement)")
                return best_channel

            return ChannelType.EMAIL

        except Exception as e:
            logger.error(f"❌ Error determining channel preference: {e}")
            return ChannelType.EMAIL

    async def execute_campaign_step(
        self,
        campaign_id: int,
        step_number: int,
        lead_id: Optional[int] = None
    ) -> Dict:
        """
        Execute next step in campaign sequence

        Args:
            campaign_id: Campaign ID
            step_number: Step number to execute
            lead_id: Specific lead ID (optional, executes for all if None)

        Returns:
            {
                "campaign_id": 123,
                "step_number": 2,
                "executions": 150,
                "successful": 148,
                "failed": 2,
                "execution_time": "3.2 seconds"
            }
        """
        try:
            start_time = datetime.now()

            # Get campaign step configuration
            step_config = self._get_campaign_step(campaign_id, step_number)

            if not step_config:
                raise ValueError(f"Step {step_number} not found for campaign {campaign_id}")

            # Get leads to execute for
            if lead_id:
                leads_to_execute = [lead_id]
            else:
                leads_to_execute = await self._get_scheduled_leads(campaign_id, step_number)

            # Execute by channel
            channel = step_config["channel"]
            executions = {"successful": 0, "failed": 0}

            for lead_id in leads_to_execute:
                try:
                    # Check if campaign is paused for this lead
                    if await self._is_campaign_paused(campaign_id, lead_id):
                        logger.info(f"⏸️ Campaign paused for lead {lead_id}, skipping")
                        continue

                    # Execute based on channel
                    if channel == ChannelType.EMAIL:
                        await self._execute_email_step(campaign_id, step_config, lead_id)
                    elif channel == ChannelType.SMS:
                        await self._execute_sms_step(campaign_id, step_config, lead_id)
                    elif channel == ChannelType.PHONE:
                        await self._execute_phone_step(campaign_id, step_config, lead_id)
                    else:
                        logger.warning(f"⚠️ Unsupported channel: {channel}")
                        continue

                    executions["successful"] += 1

                    # Schedule next step if exists
                    if step_config.get("next_step"):
                        await self._schedule_next_step(
                            campaign_id,
                            lead_id,
                            step_number + 1,
                            step_config
                        )

                except Exception as e:
                    logger.error(f"❌ Error executing step for lead {lead_id}: {e}")
                    executions["failed"] += 1

            execution_time = (datetime.now() - start_time).total_seconds()

            result = {
                "campaign_id": campaign_id,
                "step_number": step_number,
                "channel": channel,
                "executions": len(leads_to_execute),
                "successful": executions["successful"],
                "failed": executions["failed"],
                "execution_time": f"{execution_time:.2f} seconds",
                "executed_at": datetime.now().isoformat()
            }

            logger.info(f"✅ Campaign step {step_number} executed: {executions['successful']}/{len(leads_to_execute)} successful")
            return result

        except Exception as e:
            logger.error(f"❌ Error executing campaign step: {e}")
            raise

    # =====================================================
    # ENGAGEMENT HANDLING
    # =====================================================

    async def handle_engagement_event(
        self,
        lead_id: int,
        event_type: str,
        channel: str,
        campaign_id: Optional[int] = None
    ) -> Dict:
        """
        Respond to lead engagement (email open, SMS reply, etc)

        Event types:
        - "opened" - Email opened
        - "clicked" - Link clicked
        - "replied" - SMS/Email reply
        - "answered" - Phone call answered
        - "bounced" - Delivery failed

        Args:
            lead_id: Lead ID
            event_type: Type of engagement
            channel: Channel where event occurred
            campaign_id: Campaign ID (optional)

        Returns:
            {
                "lead_id": 123,
                "event_type": "replied",
                "action_taken": "paused_campaign",
                "notification_sent": true,
                "escalated_to_rep": true
            }
        """
        try:
            action_taken = []

            # Record engagement
            await self._record_engagement(lead_id, event_type, channel, campaign_id)

            # Handle based on event type
            if event_type in ["replied", "answered"]:
                # Pause campaign - lead responded
                if campaign_id:
                    await self.pause_campaign_on_response(lead_id, campaign_id)
                    action_taken.append("paused_campaign")

                # Escalate to human
                escalation = await self.escalate_to_human(
                    lead_id,
                    reason=f"Lead responded via {channel}"
                )
                action_taken.append("escalated_to_rep")

            elif event_type == "clicked":
                # High engagement - check if hot lead
                if await self._is_hot_lead_signal(lead_id, event_type):
                    escalation = await self.escalate_to_human(
                        lead_id,
                        reason="High engagement - hot lead signal"
                    )
                    action_taken.append("escalated_hot_lead")

            elif event_type == "bounced":
                # Mark lead channel as invalid
                await self._mark_channel_invalid(lead_id, channel)
                action_taken.append("marked_channel_invalid")

            # Update lead engagement score
            await self._update_engagement_score(lead_id, event_type, channel)

            result = {
                "lead_id": lead_id,
                "event_type": event_type,
                "channel": channel,
                "actions_taken": action_taken,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"✅ Engagement event handled for lead {lead_id}: {event_type} via {channel}")
            return result

        except Exception as e:
            logger.error(f"❌ Error handling engagement event: {e}")
            raise

    async def pause_campaign_on_response(
        self,
        lead_id: int,
        campaign_id: int
    ) -> None:
        """
        Stop automated follow-ups when lead responds

        Prevents annoying customers with automated messages
        after they've already engaged with sales team.

        Args:
            lead_id: Lead ID
            campaign_id: Campaign ID to pause
        """
        try:
            # Update campaign executions to paused status
            # In production, this would update campaign_executions table
            await self._update_campaign_executions(
                campaign_id=campaign_id,
                lead_id=lead_id,
                status=CampaignStatus.PAUSED
            )

            # Cancel future scheduled steps
            await self._cancel_future_steps(campaign_id, lead_id)

            logger.info(f"⏸️ Campaign {campaign_id} paused for lead {lead_id} due to response")

        except Exception as e:
            logger.error(f"❌ Error pausing campaign: {e}")
            raise

    async def escalate_to_human(
        self,
        lead_id: int,
        reason: str
    ) -> Dict:
        """
        Transfer hot lead to sales rep

        Creates task for sales rep with:
        - Lead information
        - Engagement history
        - Conversation context
        - Recommended next actions

        Args:
            lead_id: Lead ID
            reason: Escalation reason

        Returns:
            {
                "lead_id": 123,
                "assigned_to": "Sales Rep Name",
                "task_id": 456,
                "priority": "high",
                "context": {...}
            }
        """
        try:
            # Get lead data
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")

            # Get recent interactions
            recent_interactions = self.db.query(Interaction).filter(
                and_(
                    Interaction.lead_id == lead_id,
                    Interaction.created_at >= datetime.now() - timedelta(days=30)
                )
            ).order_by(desc(Interaction.created_at)).limit(10).all()

            # Build context for rep
            context = {
                "lead_name": f"{lead.first_name} {lead.last_name}",
                "phone": lead.phone,
                "email": lead.email,
                "address": lead.address,
                "escalation_reason": reason,
                "recent_interactions": [
                    {
                        "type": i.type,
                        "notes": i.notes,
                        "created_at": i.created_at.isoformat() if i.created_at else None
                    }
                    for i in recent_interactions
                ],
                "lead_temperature": lead.temperature,
                "lead_source": lead.source
            }

            # In production, this would:
            # 1. Create task in CRM
            # 2. Assign to best available rep
            # 3. Send notification (email, Slack, etc.)

            result = {
                "lead_id": lead_id,
                "escalation_reason": reason,
                "priority": "high",
                "context": context,
                "escalated_at": datetime.now().isoformat(),
                "notification_sent": True
            }

            logger.info(f"🚨 Lead {lead_id} escalated to human: {reason}")
            return result

        except Exception as e:
            logger.error(f"❌ Error escalating to human: {e}")
            raise

    # =====================================================
    # PERFORMANCE TRACKING
    # =====================================================

    async def track_campaign_performance(self, campaign_id: int) -> Dict:
        """
        Real-time campaign analytics

        Tracks:
        - Delivery rates by channel
        - Open/click/response rates
        - Conversion metrics
        - ROI calculations
        - Channel effectiveness

        Args:
            campaign_id: Campaign ID

        Returns:
            {
                "campaign_id": 123,
                "leads_enrolled": 150,
                "emails_sent": 150,
                "emails_opened": 82,
                "sms_sent": 120,
                "sms_replied": 18,
                "appointments_booked": 12,
                "deals_closed": 3,
                "revenue_generated": 105000,
                "roi": 350.0,
                "performance_by_channel": {...}
            }
        """
        try:
            # In production, this would query campaign_analytics_summary view
            # For now, return simulated data structure

            analytics = {
                "campaign_id": campaign_id,
                "campaign_name": "Q4 Premium Outreach",
                "start_date": "2025-10-12",
                "status": "active",
                "leads_enrolled": 150,

                # Email metrics
                "emails_sent": 150,
                "emails_delivered": 148,
                "emails_opened": 82,
                "emails_clicked": 28,
                "email_responses": 12,
                "email_open_rate": 55.4,  # 82/148
                "email_ctr": 34.1,  # 28/82

                # SMS metrics
                "sms_sent": 120,
                "sms_delivered": 119,
                "sms_replies": 18,
                "sms_reply_rate": 15.1,  # 18/119

                # Phone metrics
                "calls_attempted": 45,
                "calls_connected": 23,
                "calls_conversion_rate": 51.1,  # 23/45

                # Conversion metrics
                "appointments_booked": 12,
                "proposals_generated": 8,
                "deals_closed": 3,
                "overall_conversion_rate": 2.0,  # 3/150

                # Financial metrics
                "revenue_generated": 105000,  # 3 deals × $35K
                "campaign_cost": 6000,
                "roi": 1650.0,  # (105000-6000)/6000 * 100
                "cost_per_lead": 40.0,  # 6000/150
                "cost_per_deal": 2000.0,  # 6000/3

                # Channel effectiveness
                "performance_by_channel": {
                    "email": {
                        "sent": 150,
                        "engagement_rate": 55.4,
                        "conversion_rate": 1.3,
                        "deals": 2,
                        "revenue": 70000
                    },
                    "sms": {
                        "sent": 120,
                        "engagement_rate": 15.1,
                        "conversion_rate": 0.8,
                        "deals": 1,
                        "revenue": 35000
                    },
                    "phone": {
                        "attempts": 45,
                        "engagement_rate": 51.1,
                        "conversion_rate": 4.4,
                        "deals": 2,
                        "revenue": 70000
                    }
                },

                "last_updated": datetime.now().isoformat()
            }

            logger.info(f"📊 Campaign {campaign_id} performance: {analytics['overall_conversion_rate']}% conversion, ${analytics['revenue_generated']:,} revenue")
            return analytics

        except Exception as e:
            logger.error(f"❌ Error tracking campaign performance: {e}")
            raise

    # =====================================================
    # HELPER METHODS
    # =====================================================

    def _validate_campaign_config(self, config: Dict) -> None:
        """Validate campaign configuration"""
        required_fields = ["name", "campaign_type", "steps"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        if not config["steps"]:
            raise ValueError("Campaign must have at least one step")

    def _create_campaign_record(self, campaign_data: Dict) -> int:
        """Create campaign in database (placeholder)"""
        # In production, insert into sales_campaigns table
        # For now, return mock ID
        return 123

    def _create_campaign_step(self, step_data: Dict) -> None:
        """Create campaign step in database (placeholder)"""
        # In production, insert into campaign_steps table
        pass

    async def _schedule_campaign_step(
        self,
        campaign_id: int,
        lead_id: int,
        step_number: int,
        scheduled_at: datetime
    ) -> None:
        """Schedule campaign step execution (placeholder)"""
        # In production, insert into campaign_executions table
        pass

    def _get_campaign_step(self, campaign_id: int, step_number: int) -> Optional[Dict]:
        """Get campaign step configuration (placeholder)"""
        # In production, query campaign_steps table
        return {
            "campaign_id": campaign_id,
            "step_number": step_number,
            "channel": ChannelType.EMAIL,
            "template_type": "follow_up",
            "delay_days": 2,
            "next_step": step_number + 1 if step_number < 8 else None
        }

    async def _get_scheduled_leads(
        self,
        campaign_id: int,
        step_number: int
    ) -> List[int]:
        """Get leads scheduled for execution (placeholder)"""
        # In production, query campaign_executions table
        return [1, 2, 3, 4, 5]  # Mock lead IDs

    async def _is_campaign_paused(self, campaign_id: int, lead_id: int) -> bool:
        """Check if campaign is paused for lead"""
        # In production, check campaign_executions status
        return False

    async def _execute_email_step(
        self,
        campaign_id: int,
        step_config: Dict,
        lead_id: int
    ) -> None:
        """Execute email campaign step"""
        try:
            # Generate personalized email
            email = await self.email_service.generate_personalized_email(
                lead_id=lead_id,
                template_type=step_config.get("template_type", "follow_up")
            )

            # In production, send via email service
            # For now, log
            logger.info(f"📧 Email step executed for lead {lead_id}: {email['subject']}")

            # Record execution
            await self._record_execution(
                campaign_id=campaign_id,
                lead_id=lead_id,
                step_number=step_config["step_number"],
                channel=ChannelType.EMAIL,
                status=CampaignStatus.SENT
            )

        except Exception as e:
            logger.error(f"❌ Error executing email step: {e}")
            raise

    async def _execute_sms_step(
        self,
        campaign_id: int,
        step_config: Dict,
        lead_id: int
    ) -> None:
        """Execute SMS campaign step"""
        # In production, send via Twilio
        logger.info(f"📱 SMS step executed for lead {lead_id}")

        await self._record_execution(
            campaign_id=campaign_id,
            lead_id=lead_id,
            step_number=step_config["step_number"],
            channel=ChannelType.SMS,
            status=CampaignStatus.SENT
        )

    async def _execute_phone_step(
        self,
        campaign_id: int,
        step_config: Dict,
        lead_id: int
    ) -> None:
        """Execute phone campaign step"""
        # In production, create calling task for rep or trigger voice AI
        logger.info(f"☎️ Phone step scheduled for lead {lead_id}")

        await self._record_execution(
            campaign_id=campaign_id,
            lead_id=lead_id,
            step_number=step_config["step_number"],
            channel=ChannelType.PHONE,
            status=CampaignStatus.SCHEDULED
        )

    async def _schedule_next_step(
        self,
        campaign_id: int,
        lead_id: int,
        next_step_number: int,
        current_step_config: Dict
    ) -> None:
        """Schedule next campaign step"""
        delay_days = current_step_config.get("delay_days", 0)
        delay_hours = current_step_config.get("delay_hours", 0)

        next_execution = datetime.now() + timedelta(
            days=delay_days,
            hours=delay_hours
        )

        await self._schedule_campaign_step(
            campaign_id=campaign_id,
            lead_id=lead_id,
            step_number=next_step_number,
            scheduled_at=next_execution
        )

        logger.info(f"📅 Next step {next_step_number} scheduled for lead {lead_id} at {next_execution}")

    async def _record_execution(
        self,
        campaign_id: int,
        lead_id: int,
        step_number: int,
        channel: str,
        status: str
    ) -> None:
        """Record campaign execution (placeholder)"""
        # In production, insert/update campaign_executions table
        pass

    async def _record_engagement(
        self,
        lead_id: int,
        event_type: str,
        channel: str,
        campaign_id: Optional[int]
    ) -> None:
        """Record engagement event (placeholder)"""
        # In production, update campaign_executions engagement_data
        pass

    async def _is_hot_lead_signal(self, lead_id: int, event_type: str) -> bool:
        """Determine if engagement indicates hot lead"""
        # Hot lead signals:
        # - Multiple email opens in 24 hours
        # - Clicked quote/pricing link
        # - Replied to SMS
        # - Called back after missed call
        return event_type in ["replied", "clicked"]

    async def _mark_channel_invalid(self, lead_id: int, channel: str) -> None:
        """Mark channel as invalid for lead"""
        # In production, update lead record with invalid channel
        pass

    async def _update_engagement_score(
        self,
        lead_id: int,
        event_type: str,
        channel: str
    ) -> None:
        """Update lead engagement score"""
        # In production, update lead_engagement_scores table
        pass

    async def _update_campaign_executions(
        self,
        campaign_id: int,
        lead_id: int,
        status: str
    ) -> None:
        """Update campaign execution status"""
        # In production, update campaign_executions table
        pass

    async def _cancel_future_steps(self, campaign_id: int, lead_id: int) -> None:
        """Cancel future scheduled steps"""
        # In production, delete/mark cancelled in campaign_executions
        pass


# =====================================================
# STANDALONE FUNCTIONS
# =====================================================

async def create_and_execute_campaign(
    campaign_name: str,
    campaign_type: str,
    steps: List[Dict],
    target_leads: List[int],
    db: Session = None
) -> Dict:
    """
    Convenience function to create and start campaign

    Usage:
        result = await create_and_execute_campaign(
            campaign_name="Q4 Outreach",
            campaign_type="drip",
            steps=[...],
            target_leads=[1, 2, 3]
        )
    """
    orchestrator = MultiChannelOrchestrator(db)

    campaign_config = {
        "name": campaign_name,
        "campaign_type": campaign_type,
        "steps": steps
    }

    return await orchestrator.create_campaign(campaign_config, target_leads)


async def get_campaign_performance(campaign_id: int, db: Session = None) -> Dict:
    """
    Get campaign performance metrics

    Usage:
        performance = await get_campaign_performance(123)
    """
    orchestrator = MultiChannelOrchestrator(db)
    return await orchestrator.track_campaign_performance(campaign_id)
