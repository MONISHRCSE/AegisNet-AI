from typing import List
from app.correlation.models import Incident

def calculate_incident_severity(incident: Incident, ml_confidence_sum: float) -> str:
    """
    Incident severity must combine:
    - ML confidence
    - attack frequency
    - asset criticality (omitted or fetched)
    - honeypot interaction
    - attack progression depth
    """
    score = 0.0

    # Base severity from alert frequency
    score += len(incident.alert_ids) * 5.0
    
    # ML confidence average factor
    if incident.alert_ids:
        score += (ml_confidence_sum / len(incident.alert_ids)) * 100

    # Honeypot interactions are highly indicative of malicious intent
    score += incident.honeypot_interactions * 50

    # MITRE Progression Depth
    tactics_seen = {m.tactic for m in incident.mitre_tactics}
    score += len(tactics_seen) * 20

    if score > 200:
        return "CRITICAL"
    elif score > 100:
        return "HIGH"
    elif score > 50:
        return "MEDIUM"
    return "LOW"
