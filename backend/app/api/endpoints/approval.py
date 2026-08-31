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
        
    if action_in.action == "APPROVE":
        approval.status = "APPROVED"
        # In a real app we might trigger a webhook or message queue here to execute the delayed task.
    elif action_in.action == "REJECT":
        approval.status = "REJECTED"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    approval.approver_id = current_user.id
    db.commit()
    db.refresh(approval)
    
    return {"message": f"Request {approval.status}", "request_id": request_id}
