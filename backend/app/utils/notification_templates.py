"""
Notification Templates
Version: 1.0.0

Pre-defined notification templates for email and SMS messages.
"""

import html
import logging
from string import Template
from typing import Any

logger = logging.getLogger(__name__)


class NotificationTemplates:
    """Notification template manager."""

    def __init__(self):
        """Initialize notification templates."""
        self.email_templates = self._load_email_templates()
        self.sms_templates = self._load_sms_templates()

    def _load_email_templates(self) -> dict[str, dict[str, str]]:
        """Load email templates."""
        return {
            # Lead notifications
            "lead_created": {
                "subject": "New Lead Alert: ${first_name} ${last_name}",
                "html": """
                <h2>New Lead Received!</h2>
                <p><strong>Name:</strong> ${first_name} ${last_name}</p>
                <p><strong>Phone:</strong> ${phone}</p>
                <p><strong>Email:</strong> ${email}</p>
                <p><strong>Source:</strong> ${source}</p>
                <p><strong>Lead Score:</strong> ${lead_score} (${temperature})</p>
                <p><strong>Property:</strong> ${street_address}, ${city}, ${state} ${zip_code}</p>
                <p><strong>Project Description:</strong></p>
                <p>${project_description}</p>
                <hr>
                <p><a href="${lead_url}" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Lead</a></p>
                """,
                "plain": """
                New Lead Received!

                Name: ${first_name} ${last_name}
                Phone: ${phone}
                Email: ${email}
                Source: ${source}
                Lead Score: ${lead_score} (${temperature})
                Property: ${street_address}, ${city}, ${state} ${zip_code}

                Project Description:
                ${project_description}

                View Lead: ${lead_url}
                """,
            },
            "lead_hot": {
                "subject": "🔥 HOT Lead Alert - Immediate Action Required!",
                "html": """
                <div style="border: 3px solid #ef4444; padding: 20px; border-radius: 10px;">
                    <h1 style="color: #ef4444;">🔥 HOT LEAD ALERT!</h1>
                    <h3>Respond within 2 minutes for best conversion rate!</h3>

                    <div style="background: #fee2e2; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <p><strong>Name:</strong> ${first_name} ${last_name}</p>
                        <p><strong>Phone:</strong> <a href="tel:${phone}">${phone}</a></p>
                        <p><strong>Lead Score:</strong> ${lead_score}/100</p>
                        <p><strong>Urgency:</strong> ${urgency}</p>
                        <p><strong>Budget Range:</strong> $${budget_min} - $${budget_max}</p>
                    </div>

                    <p><strong>Why this lead is HOT:</strong></p>
                    <ul>
                        ${hot_reasons}
                    </ul>

                    <p style="text-align: center;">
                        <a href="tel:${phone}" style="background: #ef4444; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 18px; font-weight: bold;">
                            📞 CALL NOW
                        </a>
                    </p>
                </div>
                """,
                "plain": """
                HOT LEAD ALERT - IMMEDIATE ACTION REQUIRED!

                Respond within 2 minutes for best conversion rate!

                Name: ${first_name} ${last_name}
                Phone: ${phone}
                Lead Score: ${lead_score}/100
                Urgency: ${urgency}
                Budget: $${budget_min} - $${budget_max}

                Call immediately: ${phone}
                """,
            },
            "lead_assigned": {
                "subject": "Lead Assigned: ${first_name} ${last_name}",
                "html": """
                <h2>New Lead Assignment</h2>
                <p>You have been assigned a new lead:</p>

                <div style="background: #f3f4f6; padding: 15px; border-radius: 5px;">
                    <p><strong>Name:</strong> ${first_name} ${last_name}</p>
                    <p><strong>Phone:</strong> ${phone}</p>
                    <p><strong>Email:</strong> ${email}</p>
                    <p><strong>Lead Score:</strong> ${lead_score} (${temperature})</p>
                    <p><strong>Assignment Note:</strong> ${assignment_note}</p>
                </div>

                <p><strong>Next Steps:</strong></p>
                <ol>
                    <li>Call within ${response_time} minutes</li>
                    <li>Schedule an appointment</li>
                    <li>Update lead status in CRM</li>
                </ol>

                <p><a href="${lead_url}" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Lead Details</a></p>
                """,
                "plain": """
                New Lead Assignment

                Name: ${first_name} ${last_name}
                Phone: ${phone}
                Email: ${email}
                Lead Score: ${lead_score} (${temperature})

                Assignment Note: ${assignment_note}

                Call within ${response_time} minutes!
                View Lead: ${lead_url}
                """,
            },
            # Customer notifications
            "customer_welcome": {
                "subject": "Welcome to the iSwitch Roofs Family, ${first_name}!",
                "html": """
                <h1>Welcome to iSwitch Roofs!</h1>

                <p>Dear ${first_name},</p>

                <p>Thank you for choosing iSwitch Roofs for your roofing needs. We're honored to have you as our customer and look forward to exceeding your expectations.</p>

                <h3>What's Next?</h3>
                <ul>
                    <li>Your project manager will contact you within 24 hours</li>
                    <li>We'll schedule a detailed project consultation</li>
                    <li>You'll receive a comprehensive project timeline</li>
                </ul>

                <h3>Your Account Manager</h3>
                <p><strong>${account_manager_name}</strong><br>
                Phone: ${account_manager_phone}<br>
                Email: ${account_manager_email}</p>

                <p>If you have any questions, don't hesitate to reach out!</p>

                <p>Best regards,<br>
                The iSwitch Roofs Team</p>
                """,
                "plain": """
                Welcome to iSwitch Roofs!

                Dear ${first_name},

                Thank you for choosing iSwitch Roofs. We're honored to have you as our customer.

                What's Next:
                - Your project manager will contact you within 24 hours
                - We'll schedule a detailed project consultation
                - You'll receive a comprehensive project timeline

                Your Account Manager:
                ${account_manager_name}
                Phone: ${account_manager_phone}
                Email: ${account_manager_email}

                Best regards,
                The iSwitch Roofs Team
                """,
            },
            # Appointment notifications
            "appointment_confirmation": {
                "subject": "Appointment Confirmed: ${appointment_date} at ${appointment_time}",
                "html": """
                <h2>Appointment Confirmation</h2>

                <p>Hi ${first_name},</p>

                <p>Your appointment has been confirmed!</p>

                <div style="background: #f0fdf4; border: 1px solid #86efac; padding: 15px; border-radius: 5px;">
                    <p><strong>Date:</strong> ${appointment_date}</p>
                    <p><strong>Time:</strong> ${appointment_time}</p>
                    <p><strong>Type:</strong> ${appointment_type}</p>
                    <p><strong>Location:</strong> ${appointment_location}</p>
                    <p><strong>With:</strong> ${team_member_name}</p>
                </div>

                <h3>Prepare for Your Appointment:</h3>
                <ul>
                    <li>Have any relevant documents ready</li>
                    <li>Prepare your questions</li>
                    <li>Ensure safe access to roof area</li>
                </ul>

                <p>Need to reschedule? <a href="${reschedule_url}">Click here</a> or call us at ${company_phone}.</p>

                <p><a href="${calendar_url}" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Add to Calendar</a></p>
                """,
                "plain": """
                Appointment Confirmation

                Hi ${first_name},

                Your appointment is confirmed!

                Date: ${appointment_date}
                Time: ${appointment_time}
                Type: ${appointment_type}
                Location: ${appointment_location}
                With: ${team_member_name}

                Need to reschedule? Call ${company_phone}

                Add to calendar: ${calendar_url}
                """,
            },
            "appointment_reminder": {
                "subject": "Reminder: Appointment Tomorrow at ${appointment_time}",
                "html": """
                <h2>Appointment Reminder</h2>

                <p>Hi ${first_name},</p>

                <p>This is a friendly reminder about your appointment tomorrow:</p>

                <div style="background: #fef3c7; border: 1px solid #fbbf24; padding: 15px; border-radius: 5px;">
                    <p><strong>📅 Date:</strong> ${appointment_date}</p>
                    <p><strong>⏰ Time:</strong> ${appointment_time}</p>
                    <p><strong>📍 Location:</strong> ${appointment_location}</p>
                    <p><strong>👤 With:</strong> ${team_member_name}</p>
                </div>

                <p>We look forward to seeing you!</p>

                <p>Need to reschedule? Please call us at ${company_phone} as soon as possible.</p>
                """,
                "plain": """
                Appointment Reminder

                Hi ${first_name},

                Reminder: You have an appointment tomorrow!

                Date: ${appointment_date}
                Time: ${appointment_time}
                Location: ${appointment_location}
                With: ${team_member_name}

                Need to reschedule? Call ${company_phone}
                """,
            },
            # Project notifications
            "project_started": {
                "subject": "Great News! Your Roofing Project Has Started",
                "html": """
                <h1>Your Project Has Started!</h1>

                <p>Hi ${first_name},</p>

                <p>We're excited to inform you that your roofing project has officially begun!</p>

                <h3>Project Details:</h3>
                <ul>
                    <li><strong>Project Type:</strong> ${project_type}</li>
                    <li><strong>Start Date:</strong> ${start_date}</li>
                    <li><strong>Estimated Completion:</strong> ${estimated_completion}</li>
                    <li><strong>Project Manager:</strong> ${project_manager_name} (${project_manager_phone})</li>
                </ul>

                <h3>What to Expect:</h3>
                <ol>
                    <li>Daily updates on progress</li>
                    <li>Quality checks at each milestone</li>
                    <li>Final walkthrough upon completion</li>
                </ol>

                <p>Track your project progress: <a href="${project_tracking_url}">View Project Status</a></p>

                <p>Questions? Contact your project manager at ${project_manager_phone}.</p>
                """,
                "plain": """
                Your Project Has Started!

                Hi ${first_name},

                Your roofing project has officially begun!

                Project Type: ${project_type}
                Start Date: ${start_date}
                Estimated Completion: ${estimated_completion}
                Project Manager: ${project_manager_name} (${project_manager_phone})

                Track progress: ${project_tracking_url}
                """,
            },
            "project_completed": {
                "subject": "🎉 Your Roofing Project is Complete!",
                "html": """
                <h1 style="color: #10b981;">🎉 Project Complete!</h1>

                <p>Dear ${first_name},</p>

                <p>We're thrilled to announce that your roofing project has been successfully completed!</p>

                <h3>Project Summary:</h3>
                <div style="background: #f0fdf4; padding: 15px; border-radius: 5px;">
                    <p><strong>Project Type:</strong> ${project_type}</p>
                    <p><strong>Completion Date:</strong> ${completion_date}</p>
                    <p><strong>Warranty:</strong> ${warranty_years} Years</p>
                </div>

                <h3>Important Documents:</h3>
                <ul>
                    <li><a href="${warranty_url}">Download Warranty Certificate</a></li>
                    <li><a href="${invoice_url}">View Final Invoice</a></li>
                    <li><a href="${photos_url}">View Project Photos</a></li>
                </ul>

                <h3>We Need Your Feedback!</h3>
                <p>Your opinion matters to us. Please take a moment to:</p>
                <p><a href="${review_url}" style="background: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Leave a Review</a></p>

                <p>Thank you for choosing iSwitch Roofs!</p>
                """,
                "plain": """
                Project Complete!

                Dear ${first_name},

                Your roofing project has been successfully completed!

                Project Type: ${project_type}
                Completion Date: ${completion_date}
                Warranty: ${warranty_years} Years

                Download warranty: ${warranty_url}
                View invoice: ${invoice_url}
                View photos: ${photos_url}

                Please leave a review: ${review_url}

                Thank you for choosing iSwitch Roofs!
                """,
            },
            # Review request
            "review_request": {
                "subject": "${first_name}, How Was Your Experience with iSwitch Roofs?",
                "html": """
                <h2>We Value Your Feedback!</h2>

                <p>Hi ${first_name},</p>

                <p>It's been a week since we completed your roofing project. We hope you're enjoying your new roof!</p>

                <p>Your feedback helps us improve and helps other homeowners make informed decisions.</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="${google_review_url}" style="background: #4285f4; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 16px; margin: 0 10px;">
                        Leave a Google Review
                    </a>
                </p>

                <p>It only takes 2 minutes, and we truly appreciate it!</p>

                <p>Had an issue? Please let us know directly at ${company_email} so we can make it right.</p>

                <p>Thank you for being a valued customer!</p>
                """,
                "plain": """
                We Value Your Feedback!

                Hi ${first_name},

                How was your experience with iSwitch Roofs?

                Please leave a review: ${google_review_url}

                Had an issue? Contact us at ${company_email}

                Thank you!
                """,
            },
        }

    def _load_sms_templates(self) -> dict[str, str]:
        """Load SMS templates."""
        return {
            # Lead notifications
            "lead_hot_alert": "HOT LEAD! ${first_name} ${last_name} - Score: ${lead_score}. Call NOW: ${phone}. Urgency: ${urgency}",
            "lead_assigned": "New lead assigned: ${first_name} ${last_name}, ${phone}. Call within ${response_time} mins. View: ${lead_url}",
            # Appointment reminders
            "appointment_reminder_1day": "Hi ${first_name}, reminder: You have an appointment tomorrow at ${appointment_time}. Location: ${appointment_location}. Need to reschedule? Call ${company_phone}",
            "appointment_reminder_1hour": "Hi ${first_name}, your appointment is in 1 hour at ${appointment_time}. We'll see you at ${appointment_location}!",
            "appointment_confirmation": "Hi ${first_name}, your appointment is confirmed for ${appointment_date} at ${appointment_time}. We look forward to seeing you!",
            # Customer updates
            "project_started": "Hi ${first_name}, great news! Your roofing project has started today. Your project manager ${project_manager_name} will keep you updated. Questions? Call ${project_manager_phone}",
            "project_completed": "Hi ${first_name}, your roofing project is complete! Thank you for choosing iSwitch Roofs. Please leave a review: ${review_url}",
            "project_delay": "Hi ${first_name}, due to ${delay_reason}, your project is delayed by ${delay_days} days. New completion date: ${new_date}. We apologize for the inconvenience.",
            # Review requests
            "review_request": "Hi ${first_name}, thank you for choosing iSwitch Roofs! We'd love your feedback. Please leave a review: ${review_url}",
            # Follow-ups
            "follow_up_3months": "Hi ${first_name}, it's been 3 months since your roof installation. How's everything? Any questions? Reply or call ${company_phone}",
            "maintenance_reminder": "Hi ${first_name}, it's time for your annual roof inspection! Schedule now: ${scheduling_url} or call ${company_phone}",
            # Marketing (requires opt-in)
            "promotion": "Hi ${first_name}, special offer! ${offer_description}. Valid until ${expiry_date}. Call ${company_phone} or visit ${website_url}",
            # System
            "opt_out_confirmation": "You've been unsubscribed from iSwitch Roofs SMS. Reply START to re-subscribe.",
            "opt_in_confirmation": "Welcome! You're now subscribed to iSwitch Roofs SMS updates. Reply STOP to unsubscribe anytime.",
        }

    def render_template(
        self,
        template_type: str,
        template_name: str,
        variables: dict[str, Any],
        format: str = "html",
    ) -> str | None:
        """
        Render a notification template with variables.

        Args:
            template_type: Type of template ('email' or 'sms')
            template_name: Name of the template
            variables: Variable values to substitute
            format: Format for email templates ('html' or 'plain')

        Returns:
            Rendered template or None
        """
        try:
            if template_type == "email":
                templates = self.email_templates.get(template_name)
                if not templates:
                    return None

                template_str = templates.get(format, templates.get("html"))
            elif template_type == "sms":
                template_str = self.sms_templates.get(template_name)
            else:
                return None

            if not template_str:
                return None

            # Create safe template with HTML escaping for variables
            safe_vars = {}
            for key, value in variables.items():
                if value is None:
                    safe_vars[key] = ""
                elif isinstance(value, str) and format == "html" and template_type == "email":
                    # Only escape HTML for HTML email templates
                    # Don't escape if it looks like it contains HTML (for hot_reasons list)
                    if not ("<" in str(value) and ">" in str(value)):
                        safe_vars[key] = html.escape(str(value))
                    else:
                        safe_vars[key] = str(value)
                else:
                    safe_vars[key] = str(value)

            # Use Template for safe substitution
            template = Template(template_str)
            return template.safe_substitute(**safe_vars)

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            return None

    def get_email_subject(self, template_name: str, variables: dict[str, Any]) -> str | None:
        """
        Get rendered email subject.

        Args:
            template_name: Email template name
            variables: Variable values

        Returns:
            Rendered subject or None
        """
        template = self.email_templates.get(template_name)
        if not template or "subject" not in template:
            return None

        try:
            subject_template = Template(template["subject"])
            return subject_template.safe_substitute(**variables)
        except Exception:
            return None

    def get_template_variables(self, template_type: str, template_name: str) -> list[str]:
        """
        Get list of variables used in a template.

        Args:
            template_type: Type of template
            template_name: Template name

        Returns:
            List of variable names
        """
        import re

        if template_type == "email":
            templates = self.email_templates.get(template_name, {})
            # Check all parts of email template
            template_str = " ".join(
                [
                    templates.get("subject", ""),
                    templates.get("html", ""),
                    templates.get("plain", ""),
                ]
            )
        elif template_type == "sms":
            template_str = self.sms_templates.get(template_name, "")
        else:
            return []

        # Find all ${variable} patterns
        pattern = r"\$\{([^}]+)\}"
        matches = re.findall(pattern, template_str)

        return list(set(matches))


# Singleton instance
notification_templates = NotificationTemplates()
