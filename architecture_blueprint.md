# AegisNet AI — Technical Architecture & R&D Blueprint

## PHASE 1 — ARCHITECTURE VALIDATION

### Refined Architecture & Microservice Boundaries
To ensure scalability and modularity, the system is divided into bounded contexts communicating via an event-driven message bus.

1.  **Network Telemetry Service (`aegis-telemetry`):** Runs Zeek/Scapy. Captures flows and publishes raw connection records.
2.  **ML Inference Engine (`aegis-ml`):** Consumes telemetry, performs real-time preprocessing, and executes inference. Publishes threat scores.
3.  **API Gateway (`aegis-api`):** FastAPI orchestrator. Handles REST requests, WebSocket telemetry streams, and RBAC enforcement.
4.  **Honeypot Orchestrator (`aegis-deception`):** Listens for "Deception Trigger" events. Interfaces with the Docker daemon to manage decoy lifecycles and manipulates `iptables` for routing.
5.  **Data Lake & State:** 
    *   **Redis:** Message broker (Pub/Sub) and state cache.
    *   **PostgreSQL:** Relational state (Users, RBAC, Honeypot Templates).
    *   **MongoDB:** Immutable event logs, Zeek logs, and forensic timelines.

### Event-Driven Workflow
1. `aegis-telemetry` generates a Zeek `conn.log` entry.
2. Entry is published to Redis stream `topic:network_flows`.
3. `aegis-ml` consumes the flow, runs Isolation Forest & Random Forest.
4. If anomalous/malicious, `aegis-ml` publishes to `topic:threat_alerts`.
5. `aegis-api` consumes the alert, pushes to the frontend via WebSockets, and evaluates response policies.
6. If deception policy matches, `aegis-api` publishes to `topic:deception_triggers`.
7. `aegis-deception` spins up the decoy and updates NAT rules.

---

## PHASE 2 — AI/ML PIPELINE IMPROVEMENT

### Dataset & Preprocessing
*   **Dataset Selection:** **CICIDS2017** and **UNSW-NB15** (focusing on flow-based features, omitting payload data to align with the agent-less DPI constraints).
*   **Input Features:** Flow Duration, Total Fwd/Bwd Packets, Fwd/Bwd Packet Length Max/Min/Mean, Destination Port, Protocol, TCP Flag Counts.
*   **Preprocessing:** Min-Max Scaling (normalizing byte counts), One-Hot Encoding for categorical features (Protocol, State).

### Model Selection & Inference Pipeline
1.  **Isolation Forest (Unsupervised):** 
    *   *Purpose:* Behavioral baseline deviation (Zero-day detection).
    *   *Output:* Anomaly Score (-1 for anomaly, 1 for normal).
2.  **Random Forest (Supervised):**
    *   *Purpose:* Multi-class attack classification.
    *   *Labels:* Benign, Reconnaissance, DoS, Brute Force, Web Attack.
3.  **LSTM (Sequential - Optional Advanced Stage):**
    *   *Purpose:* Modeling time-series port access to predict scan progression or lateral movement.

### Evaluation Metrics
*   **Primary:** F1-Score (balances Precision and Recall), minimizing False Positives to prevent operational fatigue.
*   **Validation:** K-Fold Cross-Validation, evaluating inference latency (< 50ms per batch).

---

## PHASE 3 — ADAPTIVE HONEYPOT ENGINE REFINEMENT

### Orchestration & Routing Logic
1.  **Attack Trigger:** Random Forest classifies an IP as performing `Reconnaissance` targeting Port 3306 (MySQL).
2.  **Orchestration Workflow:** `aegis-deception` receives the trigger. It queries PostgreSQL for the `mysql-decoy` template.
3.  **Docker Isolation:** It uses the Docker API to spawn a container from the `mysql-decoy` image on an isolated Docker bridge network (`aegis-honeynet`), which has strict `DROP` rules for outbound traffic to the internal LAN.
4.  **Routing Logic (The Deception):** The orchestrator executes an `iptables` DNAT rule on the host:
    `iptables -t nat -A PREROUTING -s <Attacker_IP> -p tcp --dport 3306 -j DNAT --to-destination <Decoy_IP>:3306`
5.  **Interaction:** The attacker transparently interacts with the decoy. Decoy logs are forwarded via Fluentd/Docker-logs to MongoDB.

---

## PHASE 4 — THREAT DETECTION ENGINE REFINEMENT

### Threat Classification & Scoring
*   **Base Score:** Derived from ML model confidence probabilities (0.0 to 1.0).
*   **Asset Criticality Multiplier:** Target assets defined in DB have weights (e.g., Domain Controller = 1.5, Guest WiFi = 0.5).
*   **Explainable Scoring (XAI):** Utilizing SHAP (SHapley Additive exPlanations) summary plots offline to define hardcoded heuristic explanations. E.g., if Random Forest flags "DoS", the XAI module checks the highest weighted features and outputs: *"Flagged due to high Total Fwd Packets and extreme Flow Duration."*

### MITRE ATT&CK Correlation
*   *Reconnaissance (TA0043):* Mapped when ML classifies "Probe" and multiple sequential destination ports are hit.
*   *Credential Access (TA0006):* Mapped when honeypot logs indicate failed SSH logins.
*   *Lateral Movement (TA0008):* Mapped when anomalous flows originate from internal IP subnets to other internal subnets.

---

## PHASE 5 — DASHBOARD & SOC DESIGN

### UI Module Structure (React/Tailwind)
1.  **Global View:** Network topology map (D3.js) showing live node communication and red lines for anomalous flows.
2.  **Live Telemetry Feed:** Real-time WebSocket stream of Zeek flows and ML classifications.
3.  **Alert Triage Panel:** Grouped incidents, MITRE ATT&CK tags, XAI reasoning, and Threat Severity Scores.
4.  **Honeypot Activity Terminal:** A live scrolling terminal simulating `tail -f` of attacker interactions inside decoys.
5.  **Forensic Investigation:** Query builder to filter MongoDB records by IP, Timeframe, or Attack Class.

### SOC Workflow
1. Alert arrives -> Analyst expands alert to view XAI reasoning and MITRE mapping.
2. Analyst reviews the automated response recommendation (e.g., "Deploy SSH Honeypot").
3. Analyst clicks "Approve Mitigation".

---

## PHASE 6 — LOGGING & FORENSICS IMPROVEMENT

### Centralized Logging Strategy
*   **Event Correlation:** Every Zeek flow gets a unique `flow_id`. ML alerts and Honeypot interactions reference this `flow_id` and the `source_ip` to chain events.
*   **Immutable Logs:** As raw logs enter the API, a SHA-256 hash of the JSON payload is calculated and stored. This ensures forensic evidence has not been tampered with.
*   **Attack Timeline Generation:** Aggregation pipeline in MongoDB grouping events by `source_ip` sorted by timestamp, yielding an array: `[Port Scan -> Anomaly Detected -> Honeypot Deployed -> Brute Force Attempted]`.

---

## PHASE 7 — SECURITY HARDENING

### Hardening Checklist
*   **Honeypot Segmentation:** Decoy containers run without `--privileged` flags, using read-only root filesystems where possible, on a dedicated bridged interface with no physical external routing capability except back through the proxy.
*   **API Protection:** FastAPI endpoints secured with JWT bearer tokens. Short-lived access tokens (15m) and secure HttpOnly refresh tokens.
*   **RBAC Enforcement:** Middleware in FastAPI decodes JWT roles (`Admin`, `Analyst`). `POST /api/v1/response/*` strictly requires `Admin`.
*   **Rate Limiting:** FastAPI-Limiter backed by Redis to prevent API abuse.

---

## PHASE 8 — PERFORMANCE & SCALABILITY

### Optimization Strategy
*   **Zeek Throughput:** Offload packet capture to PF_RING if running on bare metal.
*   **Async Bottlenecks:** ML inference in Python is CPU-bound and blocks the AsyncIO event loop. Moving inference to a separate process pool (Celery workers) prevents API latency.
*   **Database Scaling:** MongoDB time-series collections should be utilized for flow logs, indexing on `{ "timestamp": -1, "source_ip": 1 }`.

---

## PHASE 9 — RESEARCH & EVALUATION DESIGN

### Experimental Methodology
1.  **Testbed:** Isolated local network containing vulnerable VMs (Metasploitable) and AegisNet sensors.
2.  **Attack Simulation:** Execute automated attacks using `tcpreplay` with CICIDS2017 PCAPs, and active attacks using Metasploit/Nmap.
3.  **Benchmarking:** Compare AegisNet's ML classification accuracy and response latency against a vanilla Suricata IDS implementation.
4.  **Metrics:** True Positive Rate (TPR), False Positive Rate (FPR), Time-to-Detect (TTD), and Time-to-Deceive (TTDc - time from detection to honeypot traffic routing).

---

## PHASE 10 — IMPLEMENTATION ROADMAP

**Phase 1: MVP Setup & Infrastructure (Weeks 1-2)**
*   *Deliverables:* Docker Compose environment, FastAPI structure, React boilerplate, PostgreSQL/MongoDB schemas.
*   *Complexity:* Low.

**Phase 2: Network Telemetry Integration (Weeks 3-4)**
*   *Deliverables:* Zeek container configured to sniff traffic, parsing `conn.log`, pushing to Redis/MongoDB, WebSocket UI feed.
*   *Complexity:* Medium.

**Phase 3: AI/ML Pipeline Integration (Weeks 5-7)**
*   *Deliverables:* Train Isolation/Random Forest on CICIDS2017, wrap in Celery worker for inference, link to API for live scoring.
*   *Complexity:* High.

**Phase 4: Adaptive Honeypot Orchestration (Weeks 8-9)**
*   *Deliverables:* Python Docker SDK integration to spin up Cowrie. Basic `iptables` automation scripts for DNAT redirection.
*   *Complexity:* High (Networking logic is complex).

**Phase 5: SOC Dashboard & XAI Integration (Weeks 10-11)**
*   *Deliverables:* MITRE mapping logic, XAI heuristic generation, topology graphs, alert triage workflow UI.
*   *Complexity:* Medium.

**Phase 6: Forensic Logging, Hardening & Evaluation (Weeks 12-14)**
*   *Deliverables:* SHA-256 log integrity, RBAC testing, system benchmarking, final report generation.
*   *Complexity:* Medium.
