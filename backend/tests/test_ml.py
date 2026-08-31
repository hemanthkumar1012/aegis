from app.core.ml_engine import MLEngine
from app.db.session import SessionLocal

def test_ml_engine_insufficient_data():
    db = SessionLocal()
    engine = MLEngine(db)
    
    result = engine.detect_anomaly("nonexistent")
    
    assert "is_anomaly" in result
    assert result["is_anomaly"] == False
    assert "Not enough historical data to establish baseline" in result["reason"] or "No activity in current window" in result["reason"]
    
    db.close()
