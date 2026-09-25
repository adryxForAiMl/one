# KAVACH: Zero-Trust API Security Platform

> **"Discover. Verify. Explain. Protect."**  
> AI Hackathon — Problem Statement 3: Zero-Trust API Vulnerability Scanner

---

## Executive Summary

**KAVACH** is an enterprise Zero-Trust API Security Operations platform. Rather than naively guessing status codes or running noisy fuzzers, KAVACH enforces the foundational zero-trust paradigm:

> *"Authentication does not equal authorization. Can this API be trusted to enforce tenancy and object boundaries across authenticated identities?"*

KAVACH unifies **Target Preflight Validation**, **Netra API Discovery & OpenAPI Ingestion**, **Kavach-Auth Multi-Identity Mapping**, **Raksha Deterministic BOLA/IDOR Detection**, **Pramaan Behavioral Response Verification**, **Drishti Local scikit-learn ML Threat Intelligence**, **Trace Attack-Path Reconstruction**, and **Suraksha Automated Developer Remediation** into a single cohesive security intelligence platform.

---

## The KAVACH Modular Architecture

| Module | Meaning | Functional Purpose |
|---|---|---|
| **KAVACH Core** | *Core Engine* | Central security orchestration, scan coordination, risk calculation, and platform lifecycle. |
| **KAVACH Netra** | *Vision / Eye* | API discovery, OpenAPI 3.x/Swagger 2.0 ingestion, endpoint inventory, and attack-surface mapping. |
| **KAVACH Kavach-Auth (KAVACH Access)** | *Access* | Multi-identity authentication profiles, token scopes, and authorization boundary testing. |
| **KAVACH Raksha** | *Protection* | Deterministic Broken Object Level Authorization (BOLA/IDOR) defense and cross-identity verification. |
| **KAVACH Drishti** | *Insight* | Local scikit-learn Random Forest ML intelligence, anomaly scoring, and 6-category Posture Scorecard. |
| **KAVACH Trace** | *Pathways* | 9-stage attack path reconstruction, interactive React Flow graph workspace, and security event timeline. |
| **KAVACH Pramaan** | *Evidence* | Behavioral response verification, normalized SHA-256 fingerprints, and sensitive data exposure detection. |
| **KAVACH Suraksha** | *Remediation* | Context-aware developer remediation, secure code diffs, architectural guidance, and re-scan triggers. |
| **KAVACH Dastaavez** | *Documentation* | Executive summaries, technical audit logs, printable reports, and downloadable JSON/CSV exports. |
| **KAVACH Lab** | *Sandbox* | Controlled vulnerability test environment for live demonstration of authorization boundaries. |

---

## Key Differentiators

1. **Deterministic BOLA/IDOR Defense (Raksha)**: Exercises bidirectional authenticated cross-identity access (User A accessing User B's objects, and User B accessing User A's objects) to prove authorization violations with mathematical certainty.
2. **Behavioral Response Verification (Pramaan)**: Analyzes HTTP status, response payloads, caller-to-owner mismatches, sensitive field exposure (`password`, `token`, `secret`, `ssn`), and normalized SHA-256 structural fingerprints.
3. **Local Machine Learning Intelligence (Drishti)**: Embedded on-device Random Forest classifier (scikit-learn) trained on synthetic API vulnerability scenarios evaluates anomaly probabilities without external telemetry leaks.
4. **Transparent, Explainable Risk Engine**: Provides human-readable explanations of why an API received its score, supported by a 6-category **Security Posture Scorecard** (`Authentication`, `Authorization`, `Object Access`, `Data Exposure`, `API Configuration`, `Attack Surface`).
5. **Security Investigation Workspace (Trace)**: Stacked investigation workspace combining **Attack Paths**, an interactive **9-Node React Flow Graph**, inline node telemetry, an **Evidence Inspector**, and a live **Security Event Timeline**.
6. **Developer Remediation Center (Suraksha)**: Provides root-cause diagnosis, secure code diffs (Python/FastAPI), architectural policy controls, and verification checklists.
7. **Compliance & Audit Reporting (Dastaavez)**: One-click printable executive security reports with machine-readable JSON and CSV exports.

---

## System Architecture

```
                          ┌─────────────────────────────────────┐
                          │         KAVACH Web Console          │
                          │   React 19 · Vite · TypeScript      │
                          │   Tailwind CSS · React Flow         │
                          │      http://localhost:5173          │
                          └──────────────────┬──────────────────┘
                                             │ REST / JSON
                                             ▼
                          ┌─────────────────────────────────────┐
                          │         KAVACH Core Backend         │
                          │      FastAPI Engine (Port 8001)     │
                          └──────┬───────────┬───────────┬──────┘
                                 │           │           │
            ┌────────────────────┴───┐       │       ┌───┴─────────────────────┐
            ▼                        ▼       │       ▼                         ▼
┌──────────────────────┐ ┌───────────────┐   │ ┌───────────────┐ ┌──────────────────────┐
│   Target Preflight   │ │  KAVACH Netra │   │ │ KAVACH Raksha │ │    KAVACH Drishti    │
│   Network & Spec     │ │ OpenAPI 3.x   │   │ │ BOLA Defense  │ │  Local ML Random     │
│   Candidate Probing  │ │  Swagger 2.0  │   │ │ Cross-Testing │ │  Forest Classifier   │
└──────────────────────┘ └───────────────┘   │ └───────────────┘ └──────────────────────┘
                                             │ Target Probes
                                             ▼
                          ┌─────────────────────────────────────┐
                          │             KAVACH Lab              │
                          │   Controlled Test Sandbox (8000)    │
                          │   User A (ID 1) · User B (ID 2)     │
                          │   INTENTIONALLY VULNERABLE          │
                          └─────────────────────────────────────┘
```

---

## Verification Pipeline

KAVACH executes an auditable 7-stage zero-trust assessment pipeline:

1. **Target Validation**: Normalizes candidate target URI, pings network reachability, evaluates response latency, and validates HTTP connectivity.
2. **Netra API Discovery**: Discovers specifications across candidate routes (`/openapi.json`, `/swagger.json`, etc.), parses paths, extracts parameters, and categorizes endpoints into Collection and Object routes.
3. **Access Verification (Kavach-Auth)**: Configures multi-identity profiles, masks credentials (`tok***-a`, `tok***-b`), and establishes baseline tenant tokens.
4. **Raksha Authorization Tests**: Executes cross-identity authorization matrices, unauthenticated access probes, and out-of-bounds parameter variations.
5. **Drishti Risk Intelligence**: Evaluates behavioral response signals with local Random Forest ML inference and calculates the 6-category Security Posture Scorecard.
6. **Pramaan Evidence**: Extracts sensitive fields, compares baseline vs cross-tenant payloads, and computes SHA-256 structural response fingerprints.
7. **Security Verdict & Remediation (Suraksha)**: Generates actionable code diffs, root-cause guidance, attack-path graphs, and downloadable audit reports.

---

## Quickstart & Local Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ & npm
- macOS / Linux

### 1. Repository Setup
```bash
git clone <repo-url>
cd SentinelAPI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch Local Environment

**Terminal 1 — KAVACH Lab Sandbox API (Port 8000):**
> *Note: KAVACH Lab is an intentionally vulnerable test API designed specifically to demonstrate BOLA/IDOR detection.*
```bash
source .venv/bin/activate
uvicorn sandbox.main:app --port 8000 --reload
```

**Terminal 2 — KAVACH Core Backend (Port 8001):**
```bash
source .venv/bin/activate
uvicorn app.main:app --port 8001 --reload
```

**Terminal 3 — KAVACH Web Console (Port 5173):**
```bash
cd frontend
npm install
npm run dev
```

Open your browser to: **`http://localhost:5173`**

---

## Automated Verification & Test Suite

Run the automated test suite covering all security engines, ML inference, and API contracts:
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

Run frontend production compilation and linting:
```bash
cd frontend
npm run build
npx oxlint
```

---

## AI Hackathon Compliance & Ethics Notice

KAVACH is built strictly for **defensive, authorized API security auditing**:
- Non-destructive preflight evaluation prevents service degradation.
- Multi-identity testing requires explicit operator credential provisioning.
- Passwords, bearer tokens, and API keys are automatically masked across all logs, telemetry, and audit exports.
- All machine learning inference is performed locally without leaking sensitive API schemas to third-party providers.

---

*KAVACH — Zero-Trust API Security Platform · AI Hackathon Problem Statement 3*
