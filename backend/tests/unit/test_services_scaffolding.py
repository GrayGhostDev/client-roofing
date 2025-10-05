import pytest
from datetime import datetime


@pytest.mark.xfail(reason="Automation service not implemented yet", strict=False)
def test_automation_service_schedule_follow_up_stub():
    from app.services.automation_service import automation_service

    with pytest.raises(NotImplementedError):
        automation_service.schedule_follow_up(
            "lead_1", datetime.utcnow(), "sms", "tmpl_1", "user_1"
        )


@pytest.mark.xfail(reason="Integration service not implemented yet", strict=False)
def test_integration_service_enqueue_sync_stub():
    from app.services.integration_service import integration_service

    with pytest.raises(NotImplementedError):
        integration_service.enqueue_sync("twilio", "messages", {"to": "+10000000000"})


@pytest.mark.xfail(reason="Report service not implemented yet", strict=False)
def test_report_service_generate_leads_report_stub():
    from app.services.report_service import report_service

    with pytest.raises(NotImplementedError):
        report_service.generate_leads_report(
            filters={}, group_by=["source"], timeframe={"from": "2025-01-01", "to": "2025-01-31"}
        )


@pytest.mark.xfail(reason="Invoice service not implemented yet", strict=False)
def test_invoice_service_create_invoice_stub():
    from app.services.invoice_service import invoice_service

    with pytest.raises(NotImplementedError):
        invoice_service.create_invoice("cust_1", line_items=[{"name": "Deposit", "amount_cents": 10000}])
