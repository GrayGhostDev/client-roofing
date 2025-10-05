def test_services_package_lazy_exports():
    # Ensure we can import from app.services and access lazy exports
    from app.services import LeadScoringEngine, lead_scoring_engine, partnerships_service, realtime_service

    # Types and basic properties
    assert isinstance(lead_scoring_engine, LeadScoringEngine)
    assert hasattr(partnerships_service, "create_partner")
    assert hasattr(realtime_service, "trigger_event")
