# AegisNet AI — An Adaptive Agent-less AI Cyber Defense & Autonomous Deception Platform

## 1. Executive Summary
AegisNet AI is a research-oriented, agent-less cybersecurity platform designed to provide real-time network visibility, AI-driven behavioral threat detection, and autonomous deception-oriented defense. Built for heterogeneous network environments, it operates by analyzing network traffic metadata and flows to identify anomalies. Upon detecting malicious behavior, the system orchestrates adaptive honeypot environments to redirect attackers, collect threat intelligence, and safely isolate threats. It serves as a comprehensive proof-of-concept for intelligent cyber defense orchestration without the overhead of endpoint agents.

## 2. Problem Statement
Traditional cybersecurity architectures often rely on signature-based detection and resource-heavy endpoint agents, leaving them vulnerable to zero-day exploits, insider threats, and environments where agents cannot be installed (e.g., IoT, legacy systems). Furthermore, static honeypots are easily fingerprinted and bypassed by sophisticated attackers. There is a need for a lightweight, agent-less monitoring system that couples behavioral anomaly detection with dynamic, adaptive deception to proactively manage and study threat actors.

## 3. Project Objectives
*   Develop an agent-less network monitoring system capable of protocol behavior and flow analysis.
*   Implement AI-driven behavioral threat detection to identify anomalous activities and potential attack progressions.
*   Design a dynamic deception engine that orchestrates context-specific honeypots based on incoming attack vectors.
*   Build a semi-autonomous response workflow that prioritizes safe isolation and administrator approval for critical actions.
*   Provide a centralized security dashboard integrating MITRE ATT&CK mapping, Explainable AI (XAI) insights, and threat severity scoring.

## 4. System Philosophy
**“Adaptive autonomous cyber deception with behavioral intelligence.”**
The platform assumes compromise is inevitable. Instead of purely blocking, it observes, classifies, and deceives attackers, turning their reconnaissance and exploitation attempts into actionable intelligence while minimizing actual network risk.

## 5. Research Novelty
AegisNet AI bridges the gap between passive network monitoring and active deception. The novelty lies in its closed-loop system: traffic anomalies trigger specific ML classification models, which in turn dynamically provision context-aware honeypot services (e.g., deploying a fake database in response to SQL injection probes), creating a tailored deception environment on the fly.

## 6. Core Innovations
*   **Context-Aware Adaptive Deception:** Honeypots are not static; they are deployed or reconfigured in real-time based on the specific protocol or port being targeted.
*   **Agent-less Behavioral Baselining:** Utilizing flow data and packet metadata to establish normal network behavior patterns without endpoint installation.
*   **Explainable Threat Scoring:** Combining anomaly scores with SHAP/LIME-inspired heuristics to provide analysts with human-readable reasons for alerts.

## 7. Complete System Architecture
The architecture is highly modular and designed for containerized deployment:
*   **Frontend Layer:** React-based dashboard for real-time visualization and management.
*   **API Gateway:** FastAPI backend coordinating all inter-module communication.
*   **Packet Monitoring Engine:** Captures and processes network flows and packet headers.
*   **AI/ML Engine:** Hosts trained models for anomaly detection and classification.
*   **Honeypot Orchestration Layer:** Manages the lifecycle of Docker-based decoy services.
*   **Response Engine:** Executes semi-autonomous mitigation policies.
*   **Database Layer:** PostgreSQL (config/RBAC), MongoDB (event logs), Redis (state/cache).

## 8. Detailed Module Explanations
*   **Packet Monitoring Engine:** Uses Scapy and Zeek to extract flow records, connection states, and protocol metadata (not full payload DPI).
*   **Threat Detection Engine:** Rules-based heuristics combined with ML predictions to flag suspicious flows.
*   **Honeypot Orchestration:** Uses Docker API to spin up specific Cowrie (SSH) or custom Flask (Web/DB) decoys when directed by the Response Engine.
*   **Logging & Forensics:** Aggregates alerts, honeypot interactions, and network flows into MongoDB for timeline reconstruction.

## 9. AI/ML Workflow
AI/ML is explicitly scoped to specific tasks:
*   **Isolation Forest:** *Purpose:* Anomaly detection. *Input:* Network flow features (bytes transferred, duration, port variance). *Output:* Anomaly score (1 or -1).
*   **Random Forest:** *Purpose:* Attack classification. *Input:* Flow metadata. *Output:* Attack category (e.g., DoS, Probe, Web Attack).
*   **LSTM:** *Purpose:* Sequential behavioral modeling. *Input:* Time-series sequence of port accesses. *Output:* Probability of lateral movement or scan progression.

## 10. Honeypot Adaptation Workflow
The adaptive honeypot system is trigger-based:
1.  **Trigger:** Threat Detection Engine identifies an IP scanning Port 22 (SSH) and Port 3306 (MySQL).
2.  **Logic:** Orchestrator queries available decoy templates.
3.  **Adaptation:** A Docker container running Cowrie (SSH decoy) and a fake MySQL listener are dynamically spun up on a safe virtual IP.
4.  **Routing:** Traffic from the malicious IP is transparently routed (via iptables/SDN rules) to the decoy IP.

## 11. Threat Detection Workflow
1.  **Ingestion:** Zeek captures connection logs (`conn.log`).
2.  **Preprocessing:** Pandas pipeline normalizes numerical features and encodes categorical data.
3.  **Inference:** Data is passed to the Isolation Forest model.
4.  **Enrichment:** If flagged anomalous, the data is passed to the Random Forest classifier for categorization.
5.  **Alerting:** The event is scored and sent to the API Gateway for dashboard rendering.

## 12. End-to-End Attack Scenario
1.  **Reconnaissance:** Attacker performs an aggressive Nmap scan.
2.  **Detection:** Isolation Forest flags the high connection rate; Random Forest classifies it as a 'Probe'.
3.  **Deception:** Honeypot Orchestrator provisions fake HTTP and SSH services. Response Engine updates routing to redirect the attacker's next connections to these decoys.
4.  **Interaction:** Attacker attempts brute-force on the fake SSH. Cowrie logs credentials.
5.  **Isolation:** Response Engine calculates a critical risk score and proposes an IP block to the Admin. Admin approves, and the IP is dropped at the edge.

## 13. MITRE ATT&CK Mapping
Alerts are contextually mapped to the MITRE framework:
*   *TA0043 (Reconnaissance):* Port scanning, active probing.
*   *TA0006 (Credential Access):* SSH brute-force attempts logged in honeypots.
*   *TA0008 (Lateral Movement):* Internal-to-internal anomalous flow detection.

## 14. Explainable AI Strategy (XAI)
To build trust, the dashboard provides explanations for ML decisions.
*   *Example Alert:* "High Risk Flow Detected."
*   *XAI Context:* "Flagged due to: 1) Outbound byte volume is 400% above baseline, 2) Destination IP is historically unknown, 3) Communication occurred at 03:00 AM local time."

## 15. Technology Stack
*   **Frontend:** React.js, Tailwind CSS, Chart.js, Socket.IO-client.
*   **Backend:** Python 3.10+, FastAPI, AsyncIO, Uvicorn.
*   **Databases:** PostgreSQL (Relational/State), MongoDB (Logs/NoSQL), Redis (Pub/Sub & Cache).
*   **Cybersecurity Tools:** Zeek (Network Monitoring), Scapy (Packet crafting/analysis), Cowrie (SSH Honeypot), iptables (Routing).
*   **AI/ML:** Scikit-learn, Pandas, NumPy.
*   **Deployment:** Docker, Docker Compose, Nginx.

## 16. Deployment Architecture
Deployed as a multi-container Docker Compose application.
*   `aegis-frontend` (React/Nginx)
*   `aegis-api` (FastAPI)
*   `aegis-worker` (Celery/ML Inference)
*   `aegis-zeek` (Network Monitor - requires host network binding)
*   `aegis-db-postgres`, `aegis-db-mongo`, `aegis-redis`

## 17. Database Design Overview
*   **PostgreSQL:** `Users` (RBAC), `Assets` (Discovered devices), `Policies` (Response rules).
*   **MongoDB:** `NetworkFlows` (Raw Zeek logs), `SecurityAlerts` (Processed ML events), `HoneypotLogs` (Attacker interactions).
*   **Redis:** Rate limiting, active session tracking, Celery task queues.

## 18. API Architecture
RESTful design with WebSockets for real-time telemetry.
*   `GET /api/v1/alerts`: Retrieve historical alerts with pagination.
*   `POST /api/v1/response/approve`: Admin endpoint to approve a pending mitigation action.
*   `WS /ws/telemetry`: Live stream of network flows and threat scores.

## 19. Security Considerations
*   **Deception Isolation:** Honeypots must run on isolated Docker bridge networks with strictly no egress to the internal corporate LAN.
*   **API Security:** JWT-based authentication for the FastAPI backend.
*   **Rate Limiting:** Implemented via Redis to prevent dashboard DoS.

## 20. Scalability Considerations
While designed as a proof-of-concept, scalability is considered:
*   Zeek can be clustered for higher throughput.
*   FastAPI workers can be scaled horizontally.
*   MongoDB enables sharding for massive log volumes.

## 21. Logging & Forensics Workflow
All raw flows and ML inferences are hashed (e.g., SHA-256) upon creation to ensure forensic integrity. Analysts can query the MongoDB instance via the dashboard to reconstruct a timeline of an IP's activity across the network and honeypots.

## 22. Role-Based Access Architecture (RBAC)
*   **Admin:** Full access to approve response actions, configure honeypots, and manage users.
*   **Analyst:** Can view alerts, access forensic logs, and tag events, but cannot authorize blocking.
*   **Viewer:** Read-only dashboard access.

## 23. Threat Intelligence Integration
Optional integration via background Celery tasks:
*   Extracting source IPs from alerts and querying **AbuseIPDB** API.
*   Tagging alerts with community confidence scores to aid Analyst triage.

## 24. Limitations
*   *No Deep Payload Inspection:* Cannot detect malware hidden in encrypted payloads without SSL termination.
*   *Simulated Responses:* Production-grade enterprise switch integration (e.g., Cisco ISE) is simulated via localized `iptables` modifications.
*   *Honeypot Depth:* Decoy services emulate basic interactivity but may be fingerprinted by advanced, manual penetration testers.

## 25. Future Enhancements
*   Implementation of eBPF for lower-latency network monitoring.
*   Integration with open-source SIEMs like Elastic Security or Wazuh.
*   Dynamic generation of decoy documents (honeytokens) seeded within the network.

## 26. Research Contribution
This project provides a tangible, modular framework demonstrating that agent-less network telemetry, when combined with lightweight machine learning and dynamic container orchestration, can proactively manage threat actors through deception, rather than relying solely on reactive, static blocking.

## 27. Final Conclusion
AegisNet AI successfully scopes down the monumental task of enterprise cybersecurity into a highly functional, research-grade implementation. By focusing on behavioral flow analysis, explainable ML, and practical Docker-based honeypot orchestration, it serves as a robust proof-of-concept for the future of adaptive, autonomous cyber defense.
