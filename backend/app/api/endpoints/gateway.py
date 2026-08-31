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

from app.services.authorization import AuthorizationPipeline
import json

class ToolRegistry:
    @staticmethod
    def execute(tool_name: str, action: str, resource: str, parameters: dict) -> dict:
        supported_tools = ["payment", "database", "customer", "ticket", "email", "deployment"]
        if tool_name not in supported_tools:
            return {"status": "FAILED", "result": f"Unknown tool: {tool_name}"}
        
        return {
            "tool": tool_name,
            "action": action,
            "status": "SUCCESS",
            "result": {"message": f"Simulated execution of {action} on {tool_name}"}
        }

@router.post("/execute")
def execute_tool(
    request: GatewayRequest,
    identity: WorkloadIdentity = Depends(get_current_workload),
    db: Session = Depends(get_db)
) -> Any:
    # 1, 2 & 3 Authentication and Status Check done in Depends
    
    if identity.name != request.identity:
        raise HTTPException(status_code=403, detail="Identity mismatch")

    req_id = str(uuid.uuid4())
    
    auth_pipeline = AuthorizationPipeline(db)
    result = auth_pipeline.evaluate(
        identity=identity,
        tool=request.tool,
        action=request.action,
        resource=request.resource,
        parameters=request.parameters
    )
    
    # Audit Logging
    audit_entry = AuditLog(
        request_id=req_id,
        identity_name=identity.name,
        tool=request.tool,
        action=request.action,
        resource=request.resource,
        decision=result["decision"],
        policy_applied=result["policy_name"],
        risk_score=result["risk_score"],
        request_metadata=request.parameters
    )
    db.add(audit_entry)
    db.commit()
    
    if result["decision"] == "DENY":
        status_code = 429 if result["policy_name"] == "RATE_LIMIT" else 403
        raise HTTPException(status_code=status_code, detail={"decision": "DENY", "reason": result["reason"], "policy": result["policy_name"]})
        
    elif result["decision"] == "REQUIRE_APPROVAL":
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
        return {"decision": "REQUIRE_APPROVAL", "reason": result["reason"], "request_id": req_id}
        
    elif result["decision"] == "ALLOW":
        execution_result = ToolRegistry.execute(request.tool, request.action, request.resource, request.parameters)
        
        # We should also log the execution outcome securely
        # For simplicity, we just return it to the caller
        return {
            "decision": "ALLOW",
            "request_id": req_id,
            "execution": execution_result
        }
        
    raise HTTPException(status_code=500, detail="Unknown policy effect")
