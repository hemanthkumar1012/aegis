import pytest
from app.core.policy_engine import PolicyEngine
from app.models.workload import WorkloadIdentity
from app.models.policy import Policy

@pytest.fixture
def engine(db_session):
    db = db_session
    yield PolicyEngine(db)
    
def test_default_deny(engine):
    identity = WorkloadIdentity(name="unknown", status="ACTIVE")
    decision = engine.evaluate(identity, "unknown_tool_test", "read", "res", {})
    assert decision.effect == "DENY"

def test_suspended_identity(engine):
    identity = WorkloadIdentity(name="test-identity", status="SUSPENDED")
    decision = engine.evaluate(identity, "database", "read", "res", {})
    assert decision.effect == "DENY"
    assert "suspended" in decision.reason.lower()

def test_abac_amount_threshold(db_session):
    db = db_session
    engine = PolicyEngine(db)
    
    # Add a temporary policy
    pol = db.query(Policy).filter_by(name="test-amount-unique").first()
    if not pol:
        pol = Policy(name="test-amount-unique", effect="ALLOW", priority=500, conditions={"max_amount": 500, "tool": "payment_test"})
        db.add(pol)
        db.commit()
    
    identity = WorkloadIdentity(name="test-identity", status="ACTIVE")
    
    # Below threshold
    decision = engine.evaluate(identity, "payment_test", "refund", "res", {"amount": 400})
    assert decision.effect == "ALLOW"
    
    # Above threshold -> should fall through to default DENY since no other policy matches
    decision2 = engine.evaluate(identity, "payment_test", "refund", "res", {"amount": 600})
    assert decision2.effect == "DENY"
    
    db.delete(pol)
    db.commit()
    