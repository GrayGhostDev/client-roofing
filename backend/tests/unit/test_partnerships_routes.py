from flask import Flask


def test_partnerships_routes_exist():
    # Import module and its blueprint alias
    from app.routes import partnerships

    app = Flask(__name__)
    # Register without extra url_prefix (module already sets it)
    app.register_blueprint(partnerships.bp)

    routes = {rule.rule for rule in app.url_map.iter_rules()}

    # Core CRUD
    assert "/api/partnerships/" in routes
    assert "/api/partnerships/<partner_id>" in routes

    # Referrals convenience
    assert "/api/partnerships/<partner_id>/referrals" in routes
    assert "/api/partnerships/<partner_id>/referral" in routes

    # Commission convenience
    assert "/api/partnerships/<partner_id>/commission" in routes
