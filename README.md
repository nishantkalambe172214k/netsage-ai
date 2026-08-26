# NetSage AI

NetSage AI is an AI-assisted Cisco Packet Tracer troubleshooting and remediation platform with deterministic Python rule checking and mandatory human review.

---

## Architecture Overview

```
NetSage AI System
 ├── 1. Packet Tracer / Cisco Config Ingestion (Topology & CLI logs)
 ├── 2. Deterministic Rule Engine (VLANs, Subnets, Routing Protocols, ACLs, Interfaces)
 ├── 3. AI Root Cause & Remediation Generator (Confidence scoring & Suggested CLI commands)
 ├── 4. Mandatory Human Review (HITL approval/modification gate before application)
 └── 5. Verification Engine (Simulated re-checks and validation logs)
```

---

## Database Models (`SQLite`: `netsage.db`)

1. **`cases`**: Network troubleshooting case records containing topologies, raw configs, and workflow status (`OPEN`, `IN_REVIEW`, `APPROVED`, `REJECTED`, `RESOLVED`, `CLOSED`).
2. **`rule_findings`**: Python deterministic rule inspection findings (severity: `INFO`/`WARNING`/`CRITICAL`, status: `PASS`/`FAIL`, affected devices/interfaces).
3. **`diagnoses`**: AI-generated root-cause diagnostic reports with confidence scores and suggested CLI remediation scripts.
4. **`reviews`**: Mandatory human reviewer decisions (`APPROVED`, `REJECTED`, `MODIFIED`), reviewer identity, notes, and adjusted commands.
5. **`verification_results`**: Post-remediation verification test results (`PASSED`, `FAILED`, `PARTIAL`) and simulated ping / rule validation outputs.

---

## Quick Start

### 1. Backend Setup & Run

```bash
# Navigate to backend and activate virtualenv
cd backend
source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start backend server on port 8000
uvicorn app.main:app --reload --port 8000
```
- API Health Check: `http://localhost:8000/api/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 2. Frontend Setup & Run

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Web Application: `http://localhost:5173`

### 3. Run Backend Tests

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests -v
```
