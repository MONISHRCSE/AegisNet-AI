import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

@dataclass
class MitreProgression:
    tactic: str
    technique: str
    timestamp: datetime

@dataclass
class Incident:
    attacker_ip: str
    status: str = "open"
    severity: str = "LOW"
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    target_ips: List[str] = field(default_factory=list)
    alert_ids: List[str] = field(default_factory=list)
    mitre_tactics: List[MitreProgression] = field(default_factory=list)
    honeypot_interactions: int = 0
    attack_chain: List[str] = field(default_factory=list)
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_mongo_doc(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "attacker_ip": self.attacker_ip,
            "status": self.status,
            "severity": self.severity,
            "start_time": self.start_time,
            "last_updated": self.last_updated,
            "target_ips": list(set(self.target_ips)),
            "alert_ids": self.alert_ids,
            "mitre_tactics": [{"tactic": m.tactic, "technique": m.technique, "timestamp": m.timestamp} for m in self.mitre_tactics],
            "honeypot_interactions": self.honeypot_interactions,
            "attack_chain": self.attack_chain
        }

@dataclass
class TopologyNode:
    id: str
    type: str
    label: str
    severity: str = "low"

@dataclass
class TopologyEdge:
    source: str
    target: str
    type: str

@dataclass
class TopologyGraph:
    nodes: List[TopologyNode] = field(default_factory=list)
    edges: List[TopologyEdge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.__dict__ for n in self.nodes],
            "edges": [e.__dict__ for e in self.edges]
        }
