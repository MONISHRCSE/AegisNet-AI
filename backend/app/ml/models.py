import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
import json


# ── MITRE ATT&CK Mapping ────────────────────────────────────────────────────

MITRE_MAPPING = {
    "Reconnaissance": {
        "tactic": "Discovery",
        "technique": "T1046",
        "name": "Network Service Scanning",
    },
    "DoS": {
        "tactic": "Impact",
        "technique": "T1498",
        "name": "Network Denial of Service",
    },
   "BruteForce": {
    "tactic": "Initial Access",
    "technique": "T1110",
    "technique_name": "Brute Force"
},
    "WebAttack": {
        "tactic": "Initial Access",
        "technique": "T1190",
        "name": "Exploit Public-Facing Application",
    },
    "LateralMovement": {
        "tactic": "Lateral Movement",
        "technique": "T1021",
        "name": "Remote Services",
    },
    "Exfiltration": {
        "tactic": "Exfiltration",
        "technique": "T1041",
        "name": "Exfiltration Over C2 Channel",
    },
    "Malware": {
        "tactic": "Execution",
        "technique": "T1059",
        "name": "Command and Scripting Interpreter",
    },
    "Benign": None,
}


# ── XAI Heuristic Reason Templates ──────────────────────────────────────────

def generate_xai_reasons(features: dict, category: str, anomaly_score: float) -> List[str]:
    reasons = []

    orig_bytes = float(features.get("orig_bytes", 0))
    duration = float(features.get("duration", 0))
    dest_port = int(features.get("dest_port", 0))
    conn_state = features.get("conn_state", "")
    orig_pkts = int(features.get("orig_pkts", 0))

    if orig_bytes > 500_000:
        reasons.append(f"Outbound byte volume ({orig_bytes:,.0f} bytes) is abnormally high")

    if duration < 0.01 and orig_pkts > 20:
        reasons.append("High packet rate over extremely short duration — scan-like pattern")

    if dest_port in (22, 23, 3389, 5900):
        reasons.append(f"Destination port {dest_port} is a high-value remote access target")

    if conn_state in ("REJ", "RSTO", "RSTOS0"):
        reasons.append(f"Connection state '{conn_state}' indicates repeated rejections or resets")

    if anomaly_score < -0.3:
        reasons.append("Isolation Forest anomaly score exceeds deviation threshold from baseline")

    if category == "Reconnaissance":
        reasons.append("Port access pattern matches sequential service enumeration behaviour")

    if category == "BruteForce":
        reasons.append("High connection frequency to authentication port with repeated failures")

    if not reasons:
        reasons.append("Flow characteristics deviate from established behavioural baseline")

    return reasons


# ── Security Alert Model ─────────────────────────────────────────────────────

@dataclass
class SecurityAlert:
    flow_id: str
    attacker_ip: str
    target_ip: str
    anomaly_score: float
    ml_category: str
    confidence: float
    severity_score: float
    xai_explanation: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "new"
    mitre_attack: Optional[dict] = field(default=None)

    def __post_init__(self):
        self.mitre_attack = MITRE_MAPPING.get(self.ml_category)

    def to_mongo_doc(self) -> dict:
        return {
            "_alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "flow_id": self.flow_id,
            "attacker_ip": self.attacker_ip,
            "target_ip": self.target_ip,
            "ml_classification": {
                "model": "IsolationForest+RandomForest_v1",
                "category": self.ml_category,
                "confidence": round(self.confidence, 4),
            },
            "anomaly_score": round(self.anomaly_score, 4),
            "severity_score": round(self.severity_score, 2),
            "mitre_attack": self.mitre_attack,
            "xai_explanation": self.xai_explanation,
            "status": self.status,
        }

    def to_redis_record(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "flow_id": self.flow_id,
            "attacker_ip": self.attacker_ip,
            "target_ip": self.target_ip,
            "category": self.ml_category,
            "severity_score": str(round(self.severity_score, 2)),
            "confidence": str(round(self.confidence, 4)),
            "anomaly_score": str(round(self.anomaly_score, 4)),
            "status": self.status,
            "ts": self.timestamp.isoformat(),
            "mitre_attack": json.dumps(self.mitre_attack) if self.mitre_attack else ""
        }
