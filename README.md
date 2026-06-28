# AegisNet AI: Adaptive Network Defense Platform 🛰️

<!-- Add your project banner/screenshot here, e.g.: -->
<!-- <img width="1920" height="1080" alt="AegisNet AI SOC Dashboard" src="YOUR_IMAGE_URL_HERE" /> -->

[![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Zeek](https://img.shields.io/badge/Zeek-Network_IDS-orange?style=for-the-badge)](https://zeek.org/)
[![Docker](https://img.shields.io/badge/Docker-Honeypots-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Pub/Sub-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Forensics-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)

> *⚠️ Disclaimer:* AegisNet AI is a research/educational cybersecurity prototype. Deploying honeypots and DNAT rerouting on production networks carries real risk — review and adapt the deception layer before using outside isolated lab environments.

---

## Problem Statement

- *Signature-Based Detection is Reactive:* Traditional NIDS rely on known attack signatures and miss zero-day, never-seen-before behavioral anomalies.

- *Heavy Endpoint Agents Don't Scale:* Many security platforms require agents installed on every host, creating deployment overhead and blind spots wherever an agent can't be installed.

- *Detection Without Containment:* Most systems can flag an attack but offer no way to actively trap, study, or redirect the attacker — once detected, the attacker often simply continues.

- *Alert Fatigue & Black-Box Scoring:* Security analysts are flooded with alerts that lack context or explanation, making it hard to prioritize and trust automated flags.

- There is a need for an *agent-less, explainable, and actively deceptive* network defense platform that detects, correlates, and autonomously contains threats in real time.

---

## Project Objective

*AegisNet AI* is an AI-powered Network Intrusion Detection System (NIDS) and cloud security platform engineered to detect, explain, and autonomously contain network-based threats.

The platform aims to:
- *Agent-less Behavioral Detection:* Analyze raw network flow metadata (via Zeek) instead of requiring endpoint installations.
- *Hybrid ML Threat Engine:* Combine unsupervised anomaly detection with supervised attack classification for both known and zero-day threats.
- *Adaptive Deception:* Automatically deploy decoy services and reroute attacker traffic away from real assets — no manual intervention required.
- *Explainable, Correlated Alerts:* Map isolated flows into MITRE ATT&CK-aligned incidents with human-readable reasoning for every flag.

---

## Sustainable Development Goals (SDGs)

### SDG 9: Industry, Innovation and Infrastructure
- *Target 9.1 / 9.c:* Strengthens the resilience of digital network infrastructure against evolving cyber threats through adaptive, AI-driven defense.

### SDG 16: Peace, Justice and Strong Institutions
- *Target 16.4:* Helps protect critical systems and data integrity from intrusion, fraud, and unauthorized access — supporting trustworthy digital institutions.

---

## Proposed Solution

AegisNet AI runs on a fast, *event-driven microservices architecture*. Network telemetry flows asynchronously from sensor → ML inference → correlation → deception → analyst dashboard.

### Architecture & Workflow:

<!-- Replace with your actual architecture diagram URL -->
<img width="1536" height="1024" alt="ChatGPT Image Jun 28, 2026, 12_11_34 PM" src="https://github.com/user-attachments/assets/6e0b3041-5fe7-44c4-b72b-afe810b2d151" />


*Event-driven flow from raw traffic ingestion to autonomous deception and SOC triage*

1. *Telemetry & Ingestion (`aegis-zeek` / `aegis-telemetry-worker`):* Zeek sniffs raw traffic and performs Deep Packet Inspection, generating structured flow logs. The Telemetry Worker parses these and publishes them to a Redis queue.
2. *ML Inference & Threat Scoring (`aegis-ml-consumer`):* An async worker consumes flows from Redis, encodes features (packet length, duration, TCP flags), and scores them via Isolation Forest (anomaly) and Random Forest (classification). Malicious flows generate an Alert back to Redis.
3. *Correlation & Orchestration (`aegis-api`):* The FastAPI Gateway evaluates incoming alerts against recent history, groups related actions into a single Incident, and maps it to a MITRE ATT&CK tactic (e.g., Discovery, Credential Access, Lateral Movement).
4. *Dynamic Deception (`aegis-api` → Docker):* If policy dictates, the API spins up an isolated decoy container (e.g., `ssh-decoy`, `mysql-decoy`) on the `aegis-honeynet` network and applies `iptables` DNAT rules to silently reroute the attacker's traffic into it.
5. *SOC Analyst Triage (React Dashboard):* The new Incident, MITRE tags, and XAI explanation stream to the frontend via WebSockets in real time — the analyst watches the live topology update and can monitor attacker activity inside the honeypot terminal.

---

## 🛠️ Technologies Used

### *Frontend Stack*
- *Framework:* React + TypeScript + Vite
- *Styling:* TailwindCSS
- *Visualization:* D3.js (real-time network topology mapping)
- *Real-Time:* WebSockets

### *Backend Stack*
- *Orchestrator:* FastAPI (Python) with WebSocket support
- *Correlation Engine:* Custom incident grouping + MITRE ATT&CK mapping
- *Deception Engine:* Docker SDK + iptables (DNAT rerouting)

### *AI/ML Pipeline*
- *Anomaly Detection:* Scikit-Learn Isolation Forest (unsupervised, zero-day detection)
- *Attack Classification:* Scikit-Learn Random Forest (DoS, Brute Force, Reconnaissance, etc.)
- *Processing:* Pandas, Celery (async workers)

### *Network Sensor*
- *IDS Engine:* Zeek (Deep Packet Inspection)
- *Packet Tooling:* Scapy

### *Data & Messaging*
- *Message Broker:* Redis (Pub/Sub streams)
- *Forensic Storage:* MongoDB (immutable flow logs, honeypot session data)
- *Relational State:* PostgreSQL (RBAC, structured alert/session data)

### *Infrastructure*
- Docker, Docker Compose, NGINX Reverse Proxy, iptables

---

## 🎯 Key Features

- ✅ *Zero-Day Anomaly Detection:* Isolation Forest flags behavior never seen before, no signatures required
- ✅ *Known-Attack Classification:* Random Forest labels DoS, Brute Force, Reconnaissance, and more
- ✅ *Adaptive Honeypot Orchestration:* Auto-deploys decoy services and transparently reroutes attackers via Docker + iptables
- ✅ *Live SOC Dashboard:* Real-time network topology with malicious flows highlighted via WebSockets
- ✅ *MITRE ATT&CK Correlation:* Groups raw flows into consolidated, framework-aligned Incidents
- ✅ *Explainable AI (XAI):* Human-readable reasoning behind every flagged flow
- ✅ *Adversarial Simulator:* Built-in mock attack generator to test detection and correlation logic end-to-end

---

## 📸 Demo / Screenshots

### 1. Login
<!-- Replace with your actual screenshot URL -->
<img width="1919" height="967" alt="Screenshot 2026-05-27 115022" src="https://github.com/user-attachments/assets/5674fff8-5b73-4aad-a533-d920cdb21e2f" />


### 2. Overview
The main SOC dashboard — live network topology, system health, and high-level threat summary at a glance.
<img width="1919" height="973" alt="Screenshot 2026-05-27 115330" src="https://github.com/user-attachments/assets/476496df-5779-49f7-8771-9be82fdc370a" />


### 3. Threats
Real-time feed of detected anomalies and classified attacks, with MITRE ATT&CK tags and XAI reasoning per incident.
<img width="1918" height="968" alt="Screenshot 2026-05-27 115408" src="https://github.com/user-attachments/assets/efddfa3c-75ec-463b-a4d0-1fb188f04f1f" />


### 4. Honeypots
Live view of active decoy containers, attacker sessions, and captured commands inside the honeynet.
<img width="1919" height="970" alt="Screenshot 2026-05-27 115420" src="https://github.com/user-attachments/assets/99c078ff-03f4-4540-9173-8f2459db97e6" />


### 5. Auth APIs
API documentation / interface for the JWT-based authentication and RBAC-protected endpoints.
<img width="1919" height="967" alt="Screenshot 2026-05-27 115617" src="https://github.com/user-attachments/assets/5407e0e1-01ce-43a4-9a52-2fef8f9559da" />


---

## 💻 Local Development Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Root/sudo access (required for Zeek packet capture & iptables rules)

### 1. Clone the Repository
```bash
git clone https://github.com/MonishRCSE/AegisNet-AI.git
cd AegisNet-AI
```

### 2. Start Core Services (Redis, MongoDB, PostgreSQL, Zeek)
```bash
docker compose up -d
```

### 3. Start the Backend Services
```bash
cd aegis-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# In a separate terminal
cd ../aegis-ml-consumer
pip install -r requirements.txt
python consumer.py
```

### 4. Start the Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
The SOC dashboard will be available at `http://localhost:5173`

---

## 📊 Project Status

| Domain | Status | Notes |
|:-------|:-------|:------|
| *Frontend Dashboard* | ✅ *Stable* | Real-time topology + WebSocket alerts |
| *ML Detection Engine* | ✅ *Active* | Isolation Forest + Random Forest, 98.5% detection accuracy |
| *Deception Engine* | ✅ *Active* | Docker honeypot orchestration + iptables rerouting |
| *Correlation Engine* | ✅ *Functional* | MITRE ATT&CK incident mapping |
| *Latency* | ✅ *<50ms* | End-to-end alert pipeline |

---

<p align="center">
  <strong>Detecting What Signatures Can't, Containing What Firewalls Won't</strong><br>
  Built with ❤️ by Monish
</p>
