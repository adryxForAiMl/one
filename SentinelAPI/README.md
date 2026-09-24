# SENTINELAPI: Zero-Trust API Security Intelligence

> **"Discover. Verify. Explain. Remediate."**  
> AI Hackathon — Problem Statement 3: Zero-Trust API Vulnerability Scanner

---

## Executive Summary

**SentinelAPI** is an AI-assisted Zero-Trust API Security Operations platform. Rather than naively guessing status codes or running noisy fuzzers, SentinelAPI answers the fundamental zero-trust question:

> *"Can this API be trusted to correctly enforce security boundaries across authenticated identities?"*

SentinelAPI combines **Target Preflight Validation**, **OpenAPI 3.x/Swagger Specification Ingestion**, **Multi-Identity Mapping**, **Deterministic BOLA (Broken Object Level Authorization) Testing**, **Behavioral Response Verification & Fingerprinting**, and **Local scikit-learn Machine Learning Anomaly Scoring** to reconstruct verified attack paths and generate actionable developer remediation.

---

## Key Differentiators

1. **Target Preflight System**: Validates network connectivity, HTTP response latency, OpenAPI auto-discovery across candidate paths, and evaluates scan readiness *before* sending tests.
2. **Deterministic BOLA Engine**: Exercises authenticated cross-identity access (User A accessing User B's objects, and vice versa in reverse direction) to prove authorization violations beyond doubt.
3. **Behavioral Response Verification**: Analyzes HTTP status, response structures, identity vs resource owner mismatches, and SHA-256 normalized response fingerprints.
4. **Local ML Anomaly Intelligence**: Integrates an on-device Random Forest classifier (scikit-learn) trained on synthetic API vulnerability scenarios to evaluate anomaly probability without external telemetry leak.
5. **Transparent, Explainable Risk Engine**: Provides clear, human-readable explanations of why an API received its risk score, accompanied by a 6-category **Security Posture Scorecard**.
6. **Security Investigation Workspace**: 3-column flagship investigation cockpit combining **Attack Paths list**, interactive **9-Node React Flow Graph**, and an **Evidence Inspector** with live **Security Event Timeline**.
7. **Developer Remediation with Code Diffs**: Provides root-cause diagnosis, safe remediation code snippets in Python/FastAPI, and automated fix verification requirements.
8. **Audit-Ready Reporting**: One-click printable executive security reports with JSON and CSV exports.

---

## System Architecture

```
                          ┌─────────────────────────────────────┐
                          │     SentinelAPI Web Console        │
                          │   React 19 · Vite · TypeScript      │
                          │   Tailwind CSS · React Flow         │
                          │      http://localhost:5173          │
                          └──────────────────┬──────────────────┘
                                             │ REST / JSON
                                             ▼
                          ┌─────────────────────────────────────┐
                          │       SentinelAPI Core Backend       │
                          │      FastAPI Engine (Port 8001)     │
                          └──────┬───────────┬───────────┬──────┘
                                 │           │           │
           ┌─────────────────────┴───┐       │       ┌───┴─────────────────────┐
           ▼                         ▼       │       ▼                         ▼
┌──────────────────────┐ ┌───────────────┐   │ ┌───────────────┐ ┌──────────────────────┐
│   Target Preflight   │ │OpenAPI Parser │   │ │  BOLA Engine  │ │  Local ML Risk Engine│
│   Network & Spec     │ │  Swagger 2.0  │   │ │ Bidirectional │ │    Random Forest     │
│   Probe Candidates   │ │  OpenAPI 3.x  │   │ │ Cross-Testing │ │    scikit-learn      │
└──────────────────────┘ └───────────────┘   │ └───────────────┘ └──────────────────────┘
                                             │ Target Probes
                                             ▼
                          ┌─────────────────────────────────────┐
                          │    Authorized Test Sandbox API      │
                          │  FastAPI Demonstrator (Port 8000)   │
                          │   User A (ID 1) · User B (ID 2)     │
                          └─────────────────────────────────────┘
```

---

## Professional 13-Stage Scan Pipeline

SentinelAPI executes an auditable 13-stage security assessment pipeline:

1. **`01 TARGET PREFLIGHT`**: URL normalization, TCP connectivity check, and latency benchmark.
2. **`02 API DISCOVERY`**: Automated probing of `/openapi.json`, `/swagger.json`, `/api/openapi.json`, etc.
3. **`03 OPENAPI ANALYSIS`**: Extraction of paths, parameters, schemas, and security requirements.
4. **`04 AUTHENTICATION`**: Resolution and safe masking of Bearer tokens and API keys.
5. **`05 IDENTITY MAPPING`**: Attribution of resource ownership (Identity A vs Identity B).
6. **`06 AUTHORIZATION TESTING`**: Baseline retrieval of authorized object collections.
7. **`07 OBJECT ACCESS TESTING`**: Cross-identity parameter injection against object routes.
8. **`08 RESPONSE ANALYSIS`**: Comparison of status codes, payload structures, and sensitive fields.
9. **`09 VULNERABILITY VERIFICATION`**: Behavioral response verification and deterministic evidence capture.
10. **`10 RISK INTELLIGENCE`**: Weighted calculation combining exploitability, severity, and identity scope.
11. **`11 ATTACK PATH RECONSTRUCTION`**: Node and edge graph synthesis for visual threat modeling.
12. **`12 REMEDIATION`**: Generation of code fix recommendations and verification steps.
13. **`13 REPORT GENERATION`**: Compilation of executive scorecards and downloadable artifacts.

---

## Local Sandbox Demonstration

The repository includes an authorized test sandbox (`sandbox/main.py`) running on `http://localhost:8000`:
- **Identity User A** (`token-user-a`): Owns Order `#101` (MacBook Air)
- **Identity User B** (`token-user-b`): Owns Order `#102` (iPhone)
- **Vulnerability**: Endpoint `GET /orders/{order_id}` authenticates callers but omits object ownership validation.
- **Proof**: User A requests `/orders/102` with `token-user-a` $\rightarrow$ API responds with `HTTP 200 OK` exposing User B's order.

---

## Quick Start & Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Python Environment Setup
```bash
cd SentinelAPI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

### 2. Run the Services

**Terminal 1 — Authorized Test Sandbox (Port 8000):**
```bash
cd SentinelAPI
source .venv/bin/activate
uvicorn sandbox.main:app --port 8000 --reload
```

**Terminal 2 — SentinelAPI Core Backend (Port 8001):**
```bash
cd SentinelAPI
source .venv/bin/activate
uvicorn app.main:app --port 8001 --reload
```

**Terminal 3 — Frontend Web Application (Port 5173):**
```bash
cd SentinelAPI/frontend
npm run dev
```

### 3. Run Automated Tests
```bash
cd SentinelAPI
source .venv/bin/activate
pytest tests/ -v
```

---

## Live Demo Guide (2–3 Minute Judge Flow)

1. Open `http://localhost:5173` in any browser.
2. Note the hero header: **SENTINELAPI: Zero-Trust API Security Intelligence** — *"Discover. Verify. Explain. Remediate."*
3. Click **"TRY LOCAL SECURITY DEMO"** or navigate to the **API Scanner** tab.
4. Click **"VALIDATE TARGET"**: Observe the live **Target Preflight** checklist verifying URL format, host latency, OpenAPI parsing, and scan readiness.
5. Click **"START SECURITY SCAN"**: Watch the live **13-stage scan pipeline** execute.
6. Review the completed scan card showing **2 Verified BOLA Findings** and a **100/100 Risk Score**.
7. Click **"VIEW EXECUTIVE DASHBOARD"**:
   - Inspect the **Radial Risk Posture Gauge** (100 / CRITICAL).
   - Review the **Zero-Trust Security Posture Scorecard** (Authorization Grade F, Object Access Grade F, Authentication Grade A).
   - Read the **AI Security Intelligence** section explaining transparently *why* the score was given.
8. Click any finding to inspect the **Investigation Drawer**:
   - Compare request vs response headers and JSON payloads with masked credentials.
   - Review the **Developer Remediation Guidance** showing side-by-side vulnerable vs remediated code diffs.
9. Navigate to the **Attack Graph** tab:
   - Interact with the **Attack Path Reconstruction** (Attacker $\rightarrow$ Token $\rightarrow$ Gateway $\rightarrow$ Object ID $\rightarrow$ Victim $\rightarrow$ HTTP 200 Breach).
   - Toggle to **API Attack Surface Topology** mode to view global endpoint hierarchy.
10. Navigate to **Reports**: Preview the print-ready executive audit report, or export **JSON** and **CSV** files.

---

## Security Model & Ethical Boundary

SentinelAPI adheres strictly to defensive, authorized API security auditing:
- Only tests APIs for which authorized credentials and explicit user scope have been defined.
- Performs non-destructive `GET` verification checks.
- Masks all sensitive authentication tokens and headers before logging or display.
- Never performs brute-force attacks, denial-of-service, or remote code execution.
