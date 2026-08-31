import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.workload_deps import get_current_workload
from app.models.workload import WorkloadIdentity
from app.schemas.workload import GatewayRequest
from app.core.policy_engine import PolicyEngine
from app.models.audit import AuditLog
from app.models.approval import ApprovalRequest
# We will mock the risk engine and ML for now

router = APIRouter()

@router.post("/execute")
def execute_tool(
    request: GatewayRequest,
    identity: WorkloadIdentity = Depends(get_current_workload),
    db: Session = Depends(get_db)
) -> Any:
    # 1. & 2. Authentication and Identity validation happens in Depends
    
    # Check if identity requested matches authenticated identity
    if identity.name != request.identity:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    # 3. Identity status check (done in Depends)
    
    # 4 & 5. Policy evaluation
    engine = PolicyEngine(db)
    decision = engine.evaluate(
        identity=identity,
        tool=request.tool,
        action=request.action,
        resource=request.resource,
        parameters=request.parameters
    )

    req_id = str(uuid.uuid4())

    # 6. Rate Limit
    from app.core.rate_limit import RateLimiter
    from app.core.risk_engine import RiskEngine
    
    limiter = RateLimiter()
    # Simple limit: 60 per minute
    allowed, remaining = limiter.check_limit(identity.name, limit=60, window=60)
    
    if not allowed:
        # Log rate limit
        audit_entry = AuditLog(
            request_id=req_id, identity_name=identity.name, tool=request.tool, action=request.action, resource=request.resource,
            decision="DENY", policy_applied="RATE_LIMIT", risk_score=0.0, request_metadata=request.parameters
        )
        db.add(audit_entry)
        db.commit()
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # 7. Risk Engine
    r_engine = RiskEngine()
    risk_eval = r_engine.evaluate(identity, request.tool, request.action, request.resource, request.parameters)
    risk_score = risk_eval["score"]
    
    # If high risk, we can artificially override ALLOW to REQUIRE_APPROVAL (as a demo feature)
    if risk_score > 75 and decision.effect == "ALLOW":
        decision.effect = "REQUIRE_APPROVAL"
        decision.reason = f"Elevated risk score ({risk_score}): " + ", ".join(risk_eval["reasons"])

    audit_entry = AuditLog(
        request_id=req_id,
        identity_name=identity.name,
        tool=request.tool,
        action=request.action,
        resource=request.resource,
        decision=decision.effect,
        policy_applied=decision.policy_name,
        risk_score=risk_score,
        request_metadata=request.parameters
    )
    db.add(audit_entry)
    db.commit()

    if decision.effect == "DENY":
        raise HTTPException(status_code=403, detail={"decision": "DENY", "reason": decision.reason, "policy": decision.policy_name})
    
    elif decision.effect == "REQUIRE_APPROVAL":
        # Create approval request
        approval = ApprovalRequest(
            request_id=req_id,
            identity_name=identity.name,
            tool=request.tool,
            action=request.action,
            resource=request.resource,
            parameters=request.parameters,
            status="PENDING"
        )
        db.add(approval)
        db.commit()
        return {"decision": "REQUIRE_APPROVAL", "reason": decision.reason, "request_id": req_id}
        
    elif decision.effect == "ALLOW":
        # Simulate execution
        return {
            "decision": "ALLOW",
            "result": f"Executed {request.action} on {request.tool} successfully.",
            "request_id": req_id
        }

    raise HTTPException(status_code=500, detail="Unknown policy effect")
