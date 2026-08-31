# Aegis - AI-Powered Runtime Security & Authorization Control Plane

Aegis is an experimental security control plane prototype that sits between automated workloads and protected tools. It provides identity, authorization, anomaly detection, and human-in-the-loop approval workflows.

> **Note:** This is a prototype and candidate build. It is not intended for production deployment or enterprise use.

## Features

* **Workload/Service Identity**: Authenticate automated systems with scoped credentials.
* **RBAC + ABAC**: Deterministic policy precedence combining role-based and attribute-based access control. (Hard DENY always wins).
* **Tool Gateway Registry**: Secure routing to six simulated tools (`payment`, `database`, `customer`, `ticket`, `email`, `deployment`).
* **Deterministic Risk Engine**: Assigns baseline risk scores to actions.
* **ML Anomaly Detection**: Unsupervised ML (Isolation Forest) generates an anomaly score (0-100) based on historical request patterns.
* **Approval Workflow**: High-risk or anomalous requests are suspended for explicit human approval via transactional state locks.
* **Audit Trail**: Detailed logging of all gateway decisions and human approvals, with automatic credential masking.
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
