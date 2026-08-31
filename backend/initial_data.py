import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.policy import Policy
from app.models.workload import WorkloadIdentity
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # 1. Create admin user
    user = db.query(User).filter(User.email == "admin@aegis.local").first()
    if not user:
        user = User(
            email="admin@aegis.local",
            hashed_password=get_password_hash("admin"),
            is_active=True,
        )
        db.add(user)
        db.commit()
        logger.info("Admin user created")

    # 2. Seed Default Policies
    policies = [
        {"name": "finance-refund-auto", "effect": "ALLOW", "priority": 100, "conditions": {"identity": "finance-service", "tool": "payment", "action": "refund", "max_amount": 500}},
        {"name": "finance-refund-large", "effect": "REQUIRE_APPROVAL", "priority": 200, "conditions": {"identity": "finance-service", "tool": "payment", "action": "refund"}},
        {"name": "support-read-customer", "effect": "ALLOW", "priority": 100, "conditions": {"identity": "support-service", "tool": "customer", "action": "read"}},
        {"name": "support-no-db-export", "effect": "DENY", "priority": 900, "conditions": {"identity": "support-service", "tool": "database", "action": "export"}},
    ]

    for p in policies:
        existing = db.query(Policy).filter(Policy.name == p["name"]).first()
        if not existing:
            pol = Policy(**p)
            db.add(pol)
    db.commit()
    logger.info("Default policies seeded")

def main() -> None:
    logger.info("Creating initial data")
    db = SessionLocal()
    init_db(db)
    logger.info("Initial data created")

if __name__ == "__main__":
    main()
