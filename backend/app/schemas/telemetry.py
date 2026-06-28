from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, List

class FlowMetadata(BaseModel):
    source_ip: str
    dest_ip: str
    dest_port: int

class NetworkFlow(BaseModel):
    timestamp: datetime
    meta: FlowMetadata
    flow_id: str
    proto: str
    service: str | None = None
    duration: float
    orig_bytes: int
    resp_bytes: int
    conn_state: str
    history: str | None = None
    orig_pkts: int
    resp_pkts: int
    log_hash: str

class MLClassification(BaseModel):
    model: str
    category: str
    confidence: float

class MitreAttack(BaseModel):
    tactic: str
    technique: str
    name: str

class SecurityAlert(BaseModel):
    timestamp: datetime
    flow_id: str
    attacker_ip: str
    target_ip: str
    ml_classification: MLClassification
    anomaly_score: float
    severity_score: float
    mitre_attack: MitreAttack | None = None
    xai_explanation: List[str] = []
    status: str = "new"

class HoneypotInteraction(BaseModel):
    timestamp: datetime
    decoy_id: str
    attacker_ip: str
    honeypot_type: str
    interaction_type: str
    payload: Dict[str, Any]
    session_id: str
    log_hash: str
