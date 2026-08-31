from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.models.workload import WorkloadIdentity

class PolicyDecision:
    def __init__(self, effect: str, reason: str, policy_name: str = None):
        self.effect = effect
        self.reason = reason
        self.policy_name = policy_name

class PolicyEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate(self, identity: WorkloadIdentity, tool: str, action: str, resource: str, parameters: dict) -> PolicyDecision:
        if identity.status != "ACTIVE":
            return PolicyDecision("DENY", "Identity is suspended")
            
        policies = self.db.query(Policy).filter(Policy.is_enabled == True).order_by(Policy.priority.desc()).all()
        
        # Default decision
        decision = PolicyDecision("DENY", "No matching policy found", "default-deny")
        
        for policy in policies:
            if self._matches(policy, identity, tool, action, resource, parameters):
                return PolicyDecision(policy.effect, f"Matched policy {policy.name}", policy.name)
                
        return decision
        
    def _matches(self, policy: Policy, identity: WorkloadIdentity, tool: str, action: str, resource: str, parameters: dict) -> bool:
        conds = policy.conditions
        if not conds:
            return False
            
        if "tool" in conds and conds["tool"] != tool and conds["tool"] != "*":
            return False
        if "action" in conds and conds["action"] != action and conds["action"] != "*":
            return False
        if "identity" in conds and conds["identity"] != identity.name:
            return False
            
        # Amount checks (e.g. for payments)
        if "max_amount" in conds and "amount" in parameters:
            try:
                if float(parameters["amount"]) > float(conds["max_amount"]):
                    return False
            except ValueError:
                return False
                
        if "environment" in conds and conds["environment"] != identity.environment:
            return False
            
        if "min_trust_level" in conds:
            levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            req_lvl = levels.get(conds["min_trust_level"].upper(), 0)
            id_lvl = levels.get(identity.trust_level.upper(), 0)
            if id_lvl < req_lvl:
                return False
                
        return True
