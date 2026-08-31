import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from datetime import datetime, timedelta

class MLEngine:
    def __init__(self, db: Session):
        self.db = db
        self.model = IsolationForest(contamination=0.05, random_state=42)
        
    def _extract_features(self, identity_name: str) -> pd.DataFrame:
        # Extract features for a specific identity over the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        logs = self.db.query(AuditLog).filter(
            AuditLog.identity_name == identity_name,
            AuditLog.timestamp >= one_hour_ago
        ).all()
        
        if not logs:
            return pd.DataFrame()
            
        df = pd.DataFrame([{
            "tool": log.tool,
            "action": log.action,
            "decision": log.decision
        } for log in logs])
        
        # Aggregate features
        features = {
            "request_count": len(df),
            "tool_diversity": df["tool"].nunique(),
            "denied_rate": len(df[df["decision"] == "DENY"]) / len(df) if len(df) > 0 else 0,
        }
        
        return pd.DataFrame([features])

    def detect_anomaly(self, identity_name: str) -> dict:
        """Returns anomaly signal and score"""
        # In a real system, we'd train on historical data across all identities or a specific baseline.
        # For this prototype, we'll fetch all data, train, and then evaluate the specific identity.
        
        all_logs = self.db.query(AuditLog).all()
        if len(all_logs) < 10:
            return {"is_anomaly": False, "score": 0.0, "reason": "Not enough data"}
            
        # Group by identity to form a training set
        identities = list(set(log.identity_name for log in all_logs if log.identity_name))
        
        train_data = []
        for identity in identities:
            feat = self._extract_features(identity)
            if not feat.empty:
                train_data.append(feat.iloc[0])
                
        if len(train_data) < 2:
            return {"is_anomaly": False, "score": 0.0, "reason": "Not enough diverse data"}
            
        train_df = pd.DataFrame(train_data)
        self.model.fit(train_df)
        
        # Evaluate current identity
        current_feat = self._extract_features(identity_name)
        if current_feat.empty:
            return {"is_anomaly": False, "score": 0.0, "reason": "No recent activity"}
            
        prediction = self.model.predict(current_feat)[0]
        # prediction is -1 for outlier, 1 for inlier
        
        score_val = self.model.decision_function(current_feat)[0]
        
        is_anomaly = prediction == -1
        
        return {
            "is_anomaly": is_anomaly,
            "score": float(score_val), # Lower score is more anomalous
            "reason": "Unusual request patterns detected by ML" if is_anomaly else "Normal behavior"
        }
