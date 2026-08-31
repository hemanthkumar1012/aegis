from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.models.workload import WorkloadIdentity

class PolicyDecision:
    def __init__(self, effect: str, reason: str, policy_name: str = None, conditions: dict = None):
        self.effect = effect
        self.reason = reason
        self.policy_name = policy_name
        self.conditions = conditions or {}

class PolicyEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate(self, identity: WorkloadIdentity, tool: str, action: str, resource: str, parameters: dict) -> PolicyDecision:
        if identity.status != "ACTIVE":
            return PolicyDecision("DENY", "Identity is suspended")
            
        policies = self.db.query(Policy).filter(Policy.is_enabled == True).all()
        
        matching_policies = []
        for policy in policies:
            if self._matches(policy, identity, tool, action, resource, parameters):
                matching_policies.append(policy)
                
        if not matching_policies:
            return PolicyDecision("DENY", "No matching policy found", "default-deny")
            
        # Precedence 1: Explicit hard DENY
        for p in matching_policies:
            if p.effect == "DENY":
                return PolicyDecision("DENY", f"Explicit DENY matched policy {p.name}", p.name, p.conditions)
                
        # Precedence 2: Explicit REQUIRE_APPROVAL
        # If there are multiple, we pick the one with highest priority to log, but the effect is the same.
        require_approval_policies = [p for p in matching_policies if p.effect == "REQUIRE_APPROVAL"]
        if require_approval_policies:
            p = sorted(require_approval_policies, key=lambda x: x.priority, reverse=True)[0]
            return PolicyDecision("REQUIRE_APPROVAL", f"REQUIRE_APPROVAL matched policy {p.name}", p.name, p.conditions)
            
        # Precedence 3: Specific ALLOW
        allow_policies = [p for p in matching_policies if p.effect == "ALLOW"]
        if allow_policies:
            p = sorted(allow_policies, key=lambda x: x.priority, reverse=True)[0]
            return PolicyDecision("ALLOW", f"ALLOW matched policy {p.name}", p.name, p.conditions)
            
        # Precedence 4: Fallback
        return PolicyDecision("DENY", "Fallback to default deny", "default-deny")
        
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
                
        if "min_amount" in conds and "amount" in parameters:
            try:
                if float(parameters["amount"]) < float(conds["min_amount"]):
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
