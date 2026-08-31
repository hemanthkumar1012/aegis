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
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.request_id == request_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
        
    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Approval request is already {approval.status}")
        
    if action_in.action not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Prevent self-approval if we assume the approver shouldn't be the owner of the workload
    # For now, let's just assume we check the user role. Only ADMIN or SECURITY_ADMIN can approve.
    if current_user.role and current_user.role.name not in ["ADMIN", "SECURITY_ADMIN"]:
        raise HTTPException(status_code=403, detail="Unauthorized to approve requests")
        
    if action_in.action == "APPROVE":
        from app.api.endpoints.gateway import ToolRegistry
        execution_result = ToolRegistry.execute(
            approval.tool, approval.action, approval.resource, approval.parameters
        )
        if execution_result.get("status") == "SUCCESS":
            approval.status = "EXECUTED"
        else:
            approval.status = "FAILED"
    elif action_in.action == "REJECT":
        approval.status = "REJECTED"
        
    approval.approver_id = current_user.id
    db.commit()
    db.refresh(approval)
    
    return {"message": f"Request {approval.status}", "request_id": request_id}
