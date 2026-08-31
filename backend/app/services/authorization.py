from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.workload import WorkloadIdentity
from app.core.policy_engine import PolicyEngine
from app.core.rate_limit import get_rate_limiter
from app.core.risk_engine import RiskEngine
from app.core.ml_engine import MLEngine
import uuid
import time

class AuthorizationPipeline:
    def __init__(self, db: Session):
        self.db = db
        self.policy_engine = PolicyEngine(db)
        self.rate_limiter = get_rate_limiter()
        self.risk_engine = RiskEngine()
        self.ml_engine = MLEngine(db)
        
    def check_rbac(self, identity: WorkloadIdentity, tool: str, action: str) -> bool:
        """
        Check if the identity's role has the required permission: tool.action
        """
        if not identity.role:
            print("RBAC FAIL: No role")
            return False
        required_perm = f"{tool}.{action}"
        perms = [p.name for p in identity.role.permissions]
        print(f"RBAC CHECK: required={required_perm}, has={perms}")
        return required_perm in perms

    def evaluate(self, identity: WorkloadIdentity, tool: str, action: str, resource: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full authorization pipeline in the correct order.
        Returns a dict with execution decisions and metadata to be logged.
        """
        # 1. & 2. & 3. Authentication & Identity Status are done in deps.
        
        # 4. RBAC Permission Check
        if not self.check_rbac(identity, tool, action):
            return {
                "decision": "DENY",
                "reason": "Missing RBAC permission",
                "policy_name": "RBAC_CHECK",
                "risk_score": 0.0,
                "anomaly_score": 0.0
            }
            
        # 5. ABAC Policy Check
        policy_decision = self.policy_engine.evaluate(identity, tool, action, resource, parameters)
        
        if policy_decision.effect == "DENY":
            return {
                "decision": "DENY",
                "reason": policy_decision.reason,
                "policy_name": policy_decision.policy_name,
                "risk_score": 0.0,
                "anomaly_score": 0.0
            }
            
        # 6. Rate Limit
        allowed, remaining = self.rate_limiter.check_limit(identity.name, limit=60, window=60)
        if not allowed:
            return {
                "decision": "DENY",
                "reason": "Rate limit exceeded",
                "policy_name": "RATE_LIMIT",
                "risk_score": 0.0,
                "anomaly_score": 0.0
            }
            
        # 7. Deterministic Risk
        risk_eval = self.risk_engine.evaluate(identity, tool, action, resource, parameters)
        risk_score = risk_eval["score"]
        
        # 8. ML Anomaly Signal (0 - 100)
        ml_eval = self.ml_engine.detect_anomaly(identity.name)
        anomaly_score = ml_eval.get("score", 0.0)
        
        # Determine final effect
        final_effect = policy_decision.effect
        final_reason = policy_decision.reason
        
        # Elevate to REQUIRE_APPROVAL if risk is high or anomaly detected
        if final_effect == "ALLOW":
            if risk_score > 75:
                final_effect = "REQUIRE_APPROVAL"
                final_reason = f"Elevated deterministic risk ({risk_score})"
            elif anomaly_score > 75:
                final_effect = "REQUIRE_APPROVAL"
                final_reason = "Anomalous behavior detected"
                
        return {
            "decision": final_effect,
            "reason": final_reason,
            "policy_name": policy_decision.policy_name,
            "risk_score": risk_score,
            "anomaly_score": anomaly_score,
        }
