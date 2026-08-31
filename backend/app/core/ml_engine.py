import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from datetime import datetime, timedelta

class MLEngine:
    def __init__(self, db: Session):
        self.db = db
        # contamination depends on how strict we want to be
        self.model = IsolationForest(contamination=0.05, random_state=42)
        
    def _get_windowed_features(self, identity_name: str, start_time: datetime, end_time: datetime) -> dict:
        logs = self.db.query(AuditLog).filter(
            AuditLog.identity_name == identity_name,
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp < end_time
        ).order_by(AuditLog.timestamp.asc()).all()
        
        if not logs:
            return None
            
        df = pd.DataFrame([{
            "tool": log.tool,
            "action": log.action,
            "resource": log.resource,
            "decision": log.decision,
            "timestamp": log.timestamp
        } for log in logs])
        
        request_count = len(df)
        denied_count = len(df[df["decision"] == "DENY"])
        
        # Calculate inter-request seconds
        if request_count > 1:
            diffs = df["timestamp"].diff().dt.total_seconds().dropna()
            mean_inter_request = diffs.mean()
            # Burst: number of requests that happened within 1 second of previous
            burst_count = len(diffs[diffs < 1.0])
        else:
            mean_inter_request = 300.0 # max window size
            burst_count = 0
            
        # Sensitive actions (arbitrary definition for baseline: delete/drop or payment tool)
        sensitive_count = len(df[
            df["action"].str.lower().isin(["delete", "drop", "truncate"]) | 
            (df["tool"] == "payment")
        ])
        
        # After hours: assuming 9 to 5 UTC is normal
        after_hours_count = len(df[~df["timestamp"].dt.hour.between(9, 17)])
        
        return {
            "request_count": request_count,
            "requests_per_minute": request_count / 5.0, # 5 min window
            "unique_tools": df["tool"].nunique(),
            "unique_resources": df["resource"].nunique(),
            "denied_rate": denied_count / request_count if request_count > 0 else 0,
            "sensitive_action_rate": sensitive_count / request_count if request_count > 0 else 0,
            "burst_count": burst_count,
            "after_hours_rate": after_hours_count / request_count if request_count > 0 else 0,
            "mean_inter_request_seconds": mean_inter_request
        }

    def _build_training_data(self) -> pd.DataFrame:
        """Build historical dataset using 5-minute windows across all identities."""
        # For a real implementation we would cache this or have a background job
        all_logs = self.db.query(AuditLog).order_by(AuditLog.timestamp.asc()).all()
        if not all_logs:
            return pd.DataFrame()
            
        identities = list(set(log.identity_name for log in all_logs if log.identity_name))
        
        first_time = all_logs[0].timestamp
        last_time = datetime.utcnow()
        
        windows_data = []
        for identity in identities:
            curr_start = first_time
            while curr_start < last_time:
                curr_end = curr_start + timedelta(minutes=5)
                feat = self._get_windowed_features(identity, curr_start, curr_end)
                if feat:
                    windows_data.append(feat)
                curr_start = curr_end
                
        return pd.DataFrame(windows_data)

    def detect_anomaly(self, identity_name: str) -> dict:
        """Returns stable user-facing anomaly score 0-100 (higher is more anomalous)."""
        train_df = self._build_training_data()
        
        if len(train_df) < 10:
            return {"is_anomaly": False, "score": 0.0, "reason": "Not enough historical data to establish baseline"}
            
        self.model.fit(train_df)
        
        # Evaluate current window (last 5 minutes)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        current_feat_dict = self._get_windowed_features(identity_name, start_time, end_time)
        if not current_feat_dict:
            return {"is_anomaly": False, "score": 0.0, "reason": "No activity in current window"}
            
        current_feat = pd.DataFrame([current_feat_dict])
        
        # Raw Isolation Forest score: Negative is anomalous, positive is normal.
        # Scikit-learn decision_function returns roughly [-0.5, 0.5]
        raw_score = self.model.decision_function(current_feat)[0]
        
        # Transform [-0.5, 0.5] to [100, 0] (Invert so higher is worse)
        # We clip raw_score to [-0.5, 0.5] then map.
        clamped_score = max(-0.5, min(0.5, raw_score))
        # mapped = (clamped - (-0.5)) / 1.0 -> [0, 1]
        # invert = 1.0 - mapped -> [1, 0]
        # scale = invert * 100
        transformed_score = (1.0 - ((clamped_score + 0.5) / 1.0)) * 100.0
        
        is_anomaly = transformed_score > 75.0
        
        return {
            "is_anomaly": is_anomaly,
            "score": round(transformed_score, 2),
            "reason": "Anomalous multi-factor request patterns detected" if is_anomaly else "Normal baseline behavior"
        }
