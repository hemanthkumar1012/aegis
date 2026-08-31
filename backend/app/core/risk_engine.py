from app.models.workload import WorkloadIdentity

class RiskEngine:
    def evaluate(self, identity: WorkloadIdentity, tool: str, action: str, resource: str, parameters: dict) -> dict:
        score = 0
        reasons = []
        
        # New identity check (trust level)
        if identity.trust_level == "LOW":
            score += 20
            reasons.append("Low trust identity")
            
        # Destructive action
        destructive_actions = ["delete", "drop", "truncate", "remove"]
        if any(act in action.lower() for act in destructive_actions):
            score += 40
            reasons.append("Destructive action requested")
            
        # Sensitive resource
        sensitive_resources = ["database", "payment", "credentials", "users"]
        if any(res in tool.lower() or res in resource.lower() for res in sensitive_resources):
            score += 30
            reasons.append("Sensitive resource accessed")
            
        # Financial action
        if "amount" in parameters:
            try:
                amt = float(parameters["amount"])
                if amt > 1000:
                    score += 25
                    reasons.append("High value financial transaction")
            except ValueError:
                pass
                
        # Normalize score
        score = min(score, 100)
        
        level = "LOW"
        if score > 75:
            level = "CRITICAL"
        elif score > 50:
            level = "HIGH"
        elif score > 25:
            level = "MEDIUM"
            
        return {
            "score": score,
            "level": level,
            "reasons": reasons
        }
