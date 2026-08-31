# Aegis

Aegis is an AI-powered runtime security and authorization control plane designed to sit between automated workloads (or AI agents) and the critical tools/APIs they need to access. 

## Why It Exists

As automated agents and software services increasingly act on behalf of users, standard static credentials are no longer sufficient. Aegis exists to enforce dynamic, granular, and intelligent authorization policies. It evaluates every request not just on static credentials, but on context, risk, behavioral anomalies, and human-in-the-loop approvals before passing the request to a tool registry.

## Architecture

Aegis is divided into distinct, cleanly separated layers:
* **API Layer**: FastAPI endpoints handling validation and RESTful routing.
* **Service Layer**: Business logic for entity management.
* **Authorization Pipeline**: The core engine enforcing RBAC, ABAC, rate limiting, and ML anomaly checks.
* **Tool Registry**: A controlled execution abstraction preventing direct access to underlying capabilities.
* **Persistence Layer**: PostgreSQL database using SQLAlchemy.
* **Audit Layer**: Complete provenance of every security decision.
* **Frontend**: A React/Vite dashboard using TailwindCSS and Recharts for observability.

## Authorization Flow

Every request through the Aegis Gateway evaluates the following pipeline:
1. **Authentication**: Validates time-zone aware workload credentials, expiration, and active status.
2. **Identity Status**: Ensures the workload identity is not globally suspended.
3. **Tool Validation**: Confirms the requested tool and action exist in the registry and parameters match expected schemas.
4. **RBAC**: Evaluates role-based `tool.action` permissions.
5. **ABAC**: Evaluates deterministic attribute-based policies (e.g. amount thresholds, environments). Precedence: `HARD DENY` → `REQUIRE_APPROVAL` → `ALLOW` → `DEFAULT DENY`.
6. **Rate Limiting**: Checks Redis-backed token buckets.
7. **Risk Engine**: Deterministically scores context (e.g., sensitive resources).
8. **ML Signal**: Adds an IsolationForest unsupervised anomaly score.
9. **Approval Check**: If the policy or anomaly threshold mandates it, the request is halted and locked as `PENDING` for human review.
10. **Execution**: If `ALLOW`, the Tool Registry executes the action.
11. **Audit**: The entire decision, reason, and sanitized metadata are committed to the Audit log.

## RBAC & ABAC

* **RBAC**: Centralized role-based access control leveraging granular `tool.action` strings (e.g., `payment.refund`, `database.export`).
* **ABAC**: A deterministic JSON-condition policy engine. Conflicting policies default safely. A `DENY` always overrides an `ALLOW`.

## Risk Engine & ML Anomaly Detection

* **Risk Engine**: A deterministic scoring system evaluating the inherent sensitivity of a request (e.g. large financial transfers).
* **ML Anomaly Detection**: An offline-trained Isolation Forest model acts as an intelligence signal evaluating the request against historical baselines. It produces an anomaly score (0-100). *Note: The ML layer is an intelligence signal only. It cannot bypass RBAC/ABAC or override a DENY.*

## Approval Workflow

High-risk or anomalous requests are suspended in a `PENDING` state. The Approval system guarantees immutability. An administrator review re-checks the identity constraints before executing exactly what was originally requested, preventing TOCTOU (time-of-check to time-of-use) vulnerabilities.

## Tool Registry

Aegis abstracts capabilities into a localized registry. Currently, it implements six safe simulators: `payment`, `database`, `customer`, `ticket`, `email`, and `deployment`. 

## Database & Redis

* **Database**: PostgreSQL is the authoritative production database, managed exclusively via Alembic migrations. SQLite is supported strictly as a local/test fallback. 
* **Redis**: Used for concurrent, atomic rate limiting. Fails open gracefully to an in-memory mock during development if unavailable.

## Credential Lifecycle

* **Creation**: Credentials receive an `issued_at` and `expires_at` (default 90 days). Plaintext secrets are returned exactly once.
* **Rotation/Revocation**: Explicitly deactivates old credentials and sets a `revoked_at` timestamp.

## Local Development & Testing

1. Provide an `.env` file referencing your SQLite/Postgres database.
2. Run backend: `alembic upgrade head && uvicorn app.main:app --reload`
3. Run frontend: `npm ci && npm run dev`
4. **Testing**: `pytest` uses an isolated `test.db` fixture, ensuring zero test interdependence. 

## Docker & Deployment Architecture

The provided `docker-compose.yml` models a production-style deployment:
- `backend`: Non-root FastAPI ASGI container.
- `frontend`: Nginx serving static Vite assets.
- `db`: PostgreSQL 15 with persistent volumes.
- `redis`: Redis 7.

## Limitations

* **Not Enterprise Production Ready**: Aegis is a production-style security engineering prototype. It is NOT military-grade and does not guarantee zero vulnerabilities.
* **ML Retraining**: The ML Isolation Forest requires manual or scheduled retraining. It lacks a real-time event streaming pipeline (e.g. Kafka/RabbitMQ) for enterprise scale.
* **Tool Bindings**: The Tool Registry contains simulators. Binding them to live APIs (e.g., AWS, Stripe) requires careful parameter sanitation.
