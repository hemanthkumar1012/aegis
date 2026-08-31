from fastapi import APIRouter
from app.api.endpoints import auth, workload, gateway, policy, approval, audit

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(workload.router, prefix="/workloads", tags=["workloads"])
api_router.include_router(gateway.router, prefix="/gateway", tags=["gateway"])
api_router.include_router(policy.router, prefix="/policies", tags=["policies"])
api_router.include_router(approval.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
