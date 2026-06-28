# AegisNet AI — Complete Database Architecture

## Overview
AegisNet AI employs a polyglot persistence strategy to balance relational integrity, high-throughput event logging, and real-time state management.
*   **PostgreSQL:** Relational state, RBAC, Asset Inventory, Configuration, Threat Intelligence Feeds.
*   **MongoDB:** High-volume time-series telemetry (Zeek logs), ML alerts, Honeypot interaction logs, and Forensic Correlation.
*   **Redis:** Real-time event bus (Pub/Sub & Streams), caching, rate limiting, and fast O(1) lookups for Threat Intel filtering.

---

## 1. PostgreSQL Schema (State, RBAC & Config)

PostgreSQL handles structured data where ACID compliance and complex relationships are required.

### 1.1 RBAC Schema
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- 'Admin', 'Analyst', 'Viewer'
    permissions JSONB NOT NULL
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 1.2 Asset Inventory Schema
```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address INET UNIQUE NOT NULL,
    mac_address MACADDR,
    hostname VARCHAR(255),
    os_fingerprint VARCHAR(100),
    criticality_score DECIMAL(3,2) DEFAULT 1.00, -- Multiplier for threat scoring
    is_honeypot BOOLEAN DEFAULT false,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_assets_ip ON assets(ip_address);
```

### 1.3 Honeypot Templates & Active Decoys
```sql
CREATE TABLE honeypot_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- e.g., 'ssh-cowrie', 'mysql-fake'
    docker_image VARCHAR(255) NOT NULL,
    target_ports INT[] NOT NULL,
    interaction_level VARCHAR(50), -- 'low', 'medium', 'high'
    env_vars JSONB
);

CREATE TABLE active_decoys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id INTEGER REFERENCES honeypot_templates(id),
    assigned_ip INET NOT NULL,
    target_attacker_ip INET NOT NULL,
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'stopped', 'archived'
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    terminated_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX idx_active_decoys_attacker ON active_decoys(target_attacker_ip);
```

### 1.4 Threat Intelligence Schema (Relational Cache)
```sql
CREATE TABLE threat_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    indicator VARCHAR(255) UNIQUE NOT NULL, -- IP, Domain, or Hash
    indicator_type VARCHAR(50) NOT NULL, -- 'ip', 'domain', 'hash'
    source VARCHAR(100) NOT NULL, -- e.g., 'AbuseIPDB', 'AlienVault'
    confidence_score INTEGER CHECK (confidence_score BETWEEN 0 AND 100),
    tags TEXT[],
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_threat_intel_indicator ON threat_intelligence(indicator);
```

---

## 2. MongoDB Collection Design (Logs & Forensics)

MongoDB handles the immense volume of network telemetry and unstructured honeypot interactions.

### 2.1 Network Flows (Zeek `conn.log`)
**Time-Series Optimization Strategy:** This collection is explicitly created as a MongoDB Time Series collection, partitioned by `source_ip` with a granularity of `seconds`.

```javascript
// Collection: network_flows
{
  "_id": ObjectId("..."),
  "timestamp": ISODate("2026-05-15T10:00:00.000Z"),
  "meta": {
    "source_ip": "192.168.1.55",
    "dest_ip": "10.0.0.8",
    "dest_port": 3306
  },
  "flow_id": "CHhAvVGS1DHFzaPt9", // Zeek UID
  "proto": "tcp",
  "service": "mysql",
  "duration": 0.05,
  "orig_bytes": 1200,
  "resp_bytes": 843,
  "conn_state": "SF",
  "history": "ShADadFf",
  "orig_pkts": 10,
  "resp_pkts": 8,
  "log_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" // Forensic Integrity
}
// Indexing: { "meta.source_ip": 1, "timestamp": -1 }, { "flow_id": 1 }
```

### 2.2 Security Alerts & ML Inferences
```javascript
// Collection: security_alerts
{
  "_id": ObjectId("..."),
  "timestamp": ISODate("2026-05-15T10:00:01.000Z"),
  "flow_id": "CHhAvVGS1DHFzaPt9",
  "attacker_ip": "192.168.1.55",
  "target_ip": "10.0.0.8",
  "ml_classification": {
    "model": "RandomForest_v2",
    "category": "Reconnaissance",
    "confidence": 0.94
  },
  "anomaly_score": -0.85, // From Isolation Forest
  "severity_score": 8.5, // Computed (ML Confidence * Asset Criticality)
  "mitre_attack": {
    "tactic": "TA0043",
    "technique": "T1046",
    "name": "Network Service Scanning"
  },
  "xai_explanation": [
    "Connection rate (500/sec) exceeds baseline by 800%",
    "Destination port variance is abnormally high"
  ],
  "status": "new" // 'new', 'investigating', 'resolved'
}
// Indexing: { "attacker_ip": 1, "timestamp": -1 }, { "status": 1, "severity_score": -1 }
```

### 2.3 Honeypot Interaction Schema
```javascript
// Collection: honeypot_logs
{
  "_id": ObjectId("..."),
  "timestamp": ISODate("2026-05-15T10:05:00.000Z"),
  "decoy_id": "uuid-from-postgres-active-decoys",
  "attacker_ip": "192.168.1.55",
  "honeypot_type": "ssh-cowrie",
  "interaction_type": "login_attempt",
  "payload": {
    "username": "root",
    "password": "password123",
    "success": false
  },
  "session_id": "cowrie_session_994",
  "log_hash": "ab82...f92a"
}
// Indexing: { "attacker_ip": 1, "timestamp": -1 }, { "decoy_id": 1 }
```

### 2.4 Alert Correlation Schema
Used for aggregating timelines to prevent SOC alert fatigue.
```javascript
// Collection: alert_correlations
{
  "_id": ObjectId("..."),
  "incident_id": "INC-2026-05-15-001",
  "primary_attacker_ip": "192.168.1.55",
  "first_seen": ISODate("2026-05-15T10:00:00.000Z"),
  "last_updated": ISODate("2026-05-15T10:05:00.000Z"),
  "severity": "CRITICAL",
  "progression": [
    { "timestamp": "...", "event_type": "Reconnaissance", "ref_id": ObjectId("...") }, // Points to security_alerts
    { "timestamp": "...", "event_type": "Honeypot_Interaction", "ref_id": ObjectId("...") } // Points to honeypot_logs
  ],
  "mitigation_taken": "Traffic diverted to Cowrie Decoy"
}
// Indexing: { "primary_attacker_ip": 1, "last_updated": -1 }
```

---

## 3. Redis Caching & Message Bus Structure

Redis bridges the gap between high-velocity network packet ingestion, ML inference queues, and real-time dashboard updates.

### 3.1 Streams (Message Broker via Redis Streams)
*   **Key:** `stream:telemetry:raw_flows`
    *   *Producer:* `aegis-telemetry` (Zeek).
    *   *Consumer Group:* `ml-workers` (Isolation Forest/Random Forest inference).
*   **Key:** `stream:ml:alerts`
    *   *Producer:* `aegis-ml`.
    *   *Consumer Group:* `api-gateway` (WebSocket broadcast), `deception-orchestrator` (Honeypot logic).

### 3.2 Key-Value & Sets (State & Lookups)
*   **Rate Limiting:** `SET ratelimit:api:{jwt_id}` (TTL: 60s)
*   **Active Decoy Routing Cache:** 
    *   *Key:* `hash:routing:{attacker_ip}`
    *   *Value:* `{"decoy_ip": "172.18.0.5", "target_port": 3306, "expires_at": "..."}`
    *   *Purpose:* O(1) lookup for the network packet redirector (if not purely using iptables).
*   **Threat Intel Fast-Lookup Set:**
    *   *Key:* `set:ti:malicious_ips`
    *   *Value:* Members: `['1.2.3.4', '5.6.7.8']`
    *   *Purpose:* The telemetry engine can check `SISMEMBER set:ti:malicious_ips {source_ip}` in microseconds before passing flows to ML.

---

## 4. Indexing Strategies & Query Optimization

### PostgreSQL
*   **B-Tree Indexes:** Applied to `ip_address` (INET types are highly optimized in Postgres), `indicator` (Threat Intel), and `username`.
*   **JSONB GIN Indexes:** Applied to `permissions` in `roles` for fast capability lookups (`CREATE INDEX idx_roles_perms ON roles USING GIN (permissions);`).

### MongoDB
*   **Compound Indexes:** Most queries from the SOC dashboard filter by IP and order by time. Therefore, `{ "attacker_ip": 1, "timestamp": -1 }` is applied across alerts and honeypot logs.
*   **Time-Series Clustered Index:** `network_flows` inherently clusters data by `timestamp` and `meta.source_ip`, eliminating the need for manual compound indexing on those fields while maximizing I/O performance.

---

## 5. Data Retention Strategy

To manage storage costs while maintaining compliance and forensic viability:
1.  **Redis:** Transient. Streams are capped via `XADD MAXLEN ~ 100000`. Caches use strict TTLs (e.g., 5-15 minutes).
2.  **MongoDB `network_flows`:** Massive volume. Automatically drops data older than 14 days using MongoDB TTL Indexes (`expireAfterSeconds: 1209600`).
3.  **MongoDB `security_alerts` & `honeypot_logs`:** Medium volume. Retained for 90 days in hot storage.
4.  **PostgreSQL `active_decoys` / Assets:** Low volume. Retained indefinitely as historical records. Terminated decoys change status rather than being deleted.
5.  **Cold Storage (Optional):** A cron job dumps MongoDB alerts older than 90 days to compressed JSON/Parquet files in an S3-compatible blob store.

---

## 6. Forensic Integrity & Security

*   **Immutable Logging:** As Zeek generates a `flow_id`, the API immediately generates a SHA-256 hash `hash(flow_id + timestamp + source_ip + protocol + duration)` and writes it to MongoDB as `log_hash`. Any subsequent tampering with the database record will invalidate the hash when verified by an auditor.
*   **Least Privilege:** The `aegis-api` service connects to PostgreSQL with a dedicated database user that has `INSERT/SELECT/UPDATE` privileges but lacks `DELETE` or `DROP` capabilities.
*   **Network Isolation:** PostgreSQL and MongoDB must run on a private Docker network (`aegis-data-tier`), completely inaccessible from the host machine interfaces and honeypot networks. Only the FastAPI and ML containers can connect to them.
