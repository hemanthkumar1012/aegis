# Aegis
**AI-Powered Runtime Security & Authorization Control Plane**

Aegis is a modern security control plane that sits between automated workloads/software services and protected tools/resources. It provides a comprehensive suite of deterministic security controls combined with AI/ML behavioral anomaly detection to secure workload identities.

## Core Features
- **Workload Identity Management**: Create, suspend, and rotate credentials for machine identities.
- **Role-Based & Attribute-Based Access Control (RBAC/ABAC)**: Fine-grained permissions and contextual evaluation.
- **Deterministic Policy Engine**: Enforces ALLOW, DENY, and REQUIRE_APPROVAL decisions with a default-deny posture.
- **Gateway / API Security Pipeline**: Validates identity, executes policies, enforces rate limits, and assesses risk.
- **Risk Assessment Engine**: Deterministic risk scoring based on resource sensitivity, destructive actions, and anomalies.
- **AI/ML Anomaly Detection**: Uses `scikit-learn` (Isolation Forest) trained on historical audit events to detect anomalous behaviors.
- **Human Approval Workflow**: High-risk or high-value operations can be flagged for human review before execution.
- **Audit Logging**: Comprehensive structured logging for security events and authorization decisions.
- **React Dashboard**: Modern, responsive control plane UI using Vite, React, TailwindCSS, and Recharts.

## Architecture
A request follows this pipeline:
`Client -> Gateway -> Authentication -> Identity Validation -> Policy Engine -> Rate Limiter -> Risk Engine -> Approval Check -> Tool Execution -> Audit Logging`

**Note on AI:** AI/ML in Aegis provides an intelligence signal (a risk anomaly score) but does NOT possess ultimate authorization authority. Deterministic policies (e.g. "DENY database export") always override ML signals.

## Technologies
- **Backend**: Python 3, FastAPI, SQLAlchemy, Alembic, PostgreSQL (fallback to SQLite), Pydantic
- **Frontend**: React 18, Vite, TailwindCSS, Recharts, Lucide React
- **ML/Security**: Scikit-Learn (Isolation Forest), Redis (Rate Limiting), JWT Auth, Bcrypt
- **Infrastructure**: Docker, Docker Compose, GitHub Actions (CI)

## Local Setup

### 1. Requirements
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional for full stack)

### 2. Environment Setup
Rename `.env.example` to `.env` and adjust the variables.

### 3. Backend (Without Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../requirements.txt
pip install email-validator "bcrypt<4.0.0"

# Run migrations and seed data
alembic upgrade head
python initial_data.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Running with Docker (Recommended)
```bash
docker-compose up --build
```
This starts PostgreSQL, Redis, Backend, and Frontend.

## Testing
Run the backend pytest suite:
```bash
cd backend
pytest
```

## Threat Model
See `docs/threat-model.md` for a complete threat landscape analysis including mitigations for credential theft, privilege escalation, request flooding, and policy bypass.

## Known Limitations
- Currently uses SQLite when run locally without Docker (fallback configured in `config.py`).
- Redis rate limiting falls back to an in-memory mock if the Redis server is unavailable.
- This is a production-style prototype and requires an independent security audit before real-world deployment.
