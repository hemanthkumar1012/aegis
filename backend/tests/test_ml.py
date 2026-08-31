from app.core.ml_engine import MLEngine

def test_ml_engine_insufficient_data(db_session):
    db = db_session
    engine = MLEngine(db)
    
    result = engine.detect_anomaly("nonexistent")
    
    assert "is_anomaly" in result
    assert result["is_anomaly"] == False
    assert "Not enough historical data to establish baseline" in result["reason"] or "No activity in current window" in result["reason"]
    
    
def test_ml_return_format(db_session):
    db = db_session
    engine = MLEngine(db)
    
    result = engine.detect_anomaly("nonexistent")
    assert "is_anomaly" in result
    assert "score" in result
    assert "reason" in result
    assert 0.0 <= result["score"] <= 100.0
    
    