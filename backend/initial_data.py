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
    from app.models.user import Role, Permission

    # 1. Create Roles and Permissions
    admin_role = db.query(Role).filter_by(name="ADMIN").first()
    if not admin_role:
        admin_role = Role(name="ADMIN", description="System Administrator")
        db.add(admin_role)
    
    finance_role = db.query(Role).filter_by(name="FINANCE_SERVICE_ROLE").first()
    if not finance_role:
        finance_role = Role(name="FINANCE_SERVICE_ROLE", description="Finance Workloads")
        db.add(finance_role)
        
    support_role = db.query(Role).filter_by(name="SUPPORT_SERVICE_ROLE").first()
    if not support_role:
        support_role = Role(name="SUPPORT_SERVICE_ROLE", description="Support Workloads")
        db.add(support_role)
        
    db.commit()

    # Permissions
    perms = ["payment.refund", "payment.read", "customer.read", "database.export", "customer.delete"]
    for perm_name in perms:
        p = db.query(Permission).filter_by(name=perm_name).first()
        if not p:
            p = Permission(name=perm_name)
            db.add(p)
            db.commit()
            if perm_name.startswith("payment"):
                finance_role.permissions.append(p)
            elif perm_name == "customer.read":
                support_role.permissions.append(p)
    db.commit()

    # 2. Create admin user
    user = db.query(User).filter(User.email == "admin@aegis.local").first()
    if not user:
        from app.core.config import settings
        
        pwd = settings.ADMIN_PASSWORD
        if settings.ENVIRONMENT.lower() == "production":
            if pwd in ["", "admin", "changeme", "password"]:
                raise ValueError("ADMIN_PASSWORD must be configured to a secure value in production")
                
        user = User(
            email="admin@aegis.local",
            hashed_password=get_password_hash(pwd),
            is_active=True,
            role_id=admin_role.id
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
