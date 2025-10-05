import pytest


@pytest.mark.xfail(reason="Workflows not implemented yet", strict=False)
def test_touch_16_campaign_run_for_lead_stub():
    from app.workflows import touch_16_campaign as t16

    with pytest.raises(NotImplementedError):
        t16.run_for_lead("lead_1", context={})


@pytest.mark.xfail(reason="Workflows not implemented yet", strict=False)
def test_touch_16_campaign_enqueue_for_segment_stub():
    from app.workflows import touch_16_campaign as t16

    with pytest.raises(NotImplementedError):
        t16.enqueue_for_segment({"temperature": "hot"})


@pytest.mark.xfail(reason="Workflows not implemented yet", strict=False)
def test_review_automation_run_for_lead_stub():
    from app.workflows import review_automation

    with pytest.raises(NotImplementedError):
        review_automation.run_for_lead("lead_1", context={})


@pytest.mark.xfail(reason="Workflows not implemented yet", strict=False)
def test_referral_automation_run_for_lead_stub():
    from app.workflows import referral_automation

    with pytest.raises(NotImplementedError):
        referral_automation.run_for_lead("lead_1", context={})
