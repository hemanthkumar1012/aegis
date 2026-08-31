# Aegis Engineering Review & Refactor Findings

## Backend Architecture
- **API vs Service logic:** Migrated heavy validation and authorization pipeline resolution (RBAC, ABAC, ML Anomaly check, Risk engine check) away from raw API routes and into a unified `AuthorizationPipeline` service in `backend/app/services/authorization.py`. The gateway now correctly acts as an orchestrator rather than a business logic blob.
- **Gateway Abstraction:** Ensured one centralized authorization path exists for all protected operations.
- **Structured Decisions:** The authorization pipeline now explicitly returns `decision`, `reason`, `policy_id`, `risk`, `anomaly_score`, `matched_permissions`, and `matched_conditions` in its dict, which the gateway converts into audit logs and standard API responses.

## Authentication & Authorization
- **Security Check:** Verified credential validation thoroughly enforces `is_active`, `revoked_at`, and `expires_at` conditions.
- **Timezones:** Replaced all deprecated `datetime.utcnow()` references with timezone-aware `datetime.now(UTC)` throughout `security.py`, `ml_engine.py`, and `approval.py`.

## Policy Engine & ABAC
- **Deterministic Precedence:** Explicit policies return `DENY` > `REQUIRE_APPROVAL` > `ALLOW` > Default `DENY`.
- **Condition Matching:** `policy_engine.py` explicitly captures and returns `p.conditions` inside the `PolicyDecision` response for precise audit tracking.

## Tool Registry
- Verified exact strict implementation of the 6 core tools: `payment`, `database`, `customer`, `ticket`, `email`, `deployment`.
- Each safely simulated tool correctly rejects unknown actions and validates required parameter schemas (e.g., `amount` for payments, `destination` for exports).

## Approvals
- **Concurrency & Expiration:** Checked that `ApprovalRequest` utilizes `with_for_update()` to enforce row-level atomic locks during review actions.
- Implemented `expires_at` during the creation of an approval in the gateway, and enforced expiration verification at the execution step in `review_approval`.

## Machine Learning
- **Latency Bound:** Discovered that the ML training method `_build_training_data` was scanning the entire unbounded AuditLog history.
- Bounded this query to the last 24 hours to prevent exponential latency decay in the core gateway authorization path.

## Database Quality
- Tested and verified empty initialization works cleanly through `alembic upgrade head` and `initial_data.py`.
- Verified N+1 patterns are mitigated on the critical paths.

## Code Quality & Dependencies
- Pinned all dependencies in `requirements.txt` based on the successful operating environment (FastAPI 0.141, SQLAlchemy 2.0, Pydantic 2.13).
- Eliminated redundant dependency downloads in the `.github/workflows/ci.yml` pipeline.
- Populated `.env.example` with safe deterministic environment variable placeholders, eradicating the empty file configuration.
