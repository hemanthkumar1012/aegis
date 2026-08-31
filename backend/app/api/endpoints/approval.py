from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.approval import ApprovalRequest
from app.schemas.approval import ApprovalRequestSchema, ApprovalAction
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[ApprovalRequestSchema])
def read_approvals(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return db.query(ApprovalRequest).all()

@router.post("/{request_id}/review")
def review_approval(
    *,
    db: Session = Depends(deps.get_db),
    request_id: str,
    action_in: ApprovalAction,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # 1. Lock the row to prevent concurrent execution
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.request_id == request_id).with_for_update().first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
        
    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval request is already {approval.status}")
        
    from datetime import datetime, UTC
    if approval.expires_at and approval.expires_at < datetime.now(UTC):
        approval.status = "EXPIRED"
        db.commit()
        raise HTTPException(status_code=400, detail="Approval request has expired")
        
    if action_in.action not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    if current_user.role and current_user.role.name not in ["ADMIN", "SECURITY_ADMIN"]:
        raise HTTPException(status_code=403, detail="Unauthorized to approve requests")
        
    approval.approver_id = current_user.id

    if action_in.action == "APPROVE":
        from app.models.workload import WorkloadIdentity
        from app.services.authorization import AuthorizationPipeline
        
        # 2. Re-verify identity existence and status
        identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.name == approval.identity_name).first()
        if not identity or identity.status != "ACTIVE":
            approval.status = "FAILED"
            db.commit()
            raise HTTPException(status_code=403, detail="Identity is missing or suspended")
            
        # 3. Re-evaluate ABAC/RBAC
        pipeline = AuthorizationPipeline(db)
        eval_result = pipeline.evaluate(identity, approval.tool, approval.action, approval.resource, approval.parameters)
        
        # If the result is DENY, it must be rejected (e.g. a new block policy was added)
        if eval_result["decision"] == "DENY":
            approval.status = "REJECTED"
            db.commit()
            raise HTTPException(status_code=403, detail=f"Request now violates a hard DENY policy: {eval_result}")
            
        # If it returns REQUIRE_APPROVAL again (e.g. still anomalous or high risk), 
        # we explicitly define that the existing human approval is sufficient for this exact immutable request.
        # Since the approval record is immutable and cannot be altered, the approver's authorization holds.
        elif eval_result["decision"] == "REQUIRE_APPROVAL":
            pass # Existing approval is sufficient

        # 4. Execute
        from app.core.tools import registry as tool_registry
        execution_result = tool_registry.execute(
            approval.tool, approval.action, approval.resource, approval.parameters
        )
        if execution_result.get("status") == "SUCCESS":
            approval.status = "EXECUTED"
        else:
            approval.status = "FAILED"
            
    elif action_in.action == "REJECT":
        approval.status = "REJECTED"
        
    # Generate Audit Log for approval action
    from app.models.audit import AuditLog
    import uuid
    audit_entry = AuditLog(
        request_id=str(uuid.uuid4()),
        identity_name=approval.identity_name,
        tool=approval.tool,
        action=approval.action,
        resource=approval.resource,
        decision=f"APPROVAL_{action_in.action}_{approval.status}",
        policy_applied="APPROVAL_WORKFLOW",
        risk_score=0.0,
        anomaly_score=0.0,
        request_metadata={"approver_id": current_user.id, "original_request": request_id}
    )
    db.add(audit_entry)
        
    db.commit()
    db.refresh(approval)
    
    return {"message": f"Request {approval.status}", "request_id": request_id}
