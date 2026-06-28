import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from app.correlation.models import Incident, MitreProgression
from app.correlation.scoring import calculate_incident_severity

logger = logging.getLogger("aegisnet.correlation.correlator")

INCIDENT_TIMEOUT_MINUTES = 15

class Correlator:
    def __init__(self):
        # Maps attacker_ip to active Incident
        self.active_incidents: Dict[str, Incident] = {}
        # Stores running sum of ml_confidence for scoring
        self.ml_confidence_sums: Dict[str, float] = {}

    def process_alert(self, alert: dict) -> Incident:
        attacker_ip = alert.get("attacker_ip")
        if not attacker_ip:
            return None

        now = datetime.now(timezone.utc)
        alert_id = alert.get("alert_id") or alert.get("_alert_id")
        target_ip = alert.get("target_ip")
        confidence = float(alert.get("confidence", 0) or alert.get("ml_classification", {}).get("confidence", 0))
        
        mitre_data_raw = alert.get("mitre_attack")
        mitre_data = None
        if mitre_data_raw:
            import json
            mitre_data = json.loads(mitre_data_raw) if isinstance(mitre_data_raw, str) else mitre_data_raw

        progression = None
        if mitre_data:
            progression = MitreProgression(
                tactic=mitre_data.get("tactic", ""),
                technique=mitre_data.get("technique", ""),
                timestamp=now
            )

        # Check for existing incident
        incident = self.active_incidents.get(attacker_ip)

        # If incident exists but is stale, close it and start a new one
        if incident and (now - incident.last_updated) > timedelta(minutes=INCIDENT_TIMEOUT_MINUTES):
            incident.status = "closed"
            # In a real app we'd emit an event to save the closed incident, but here we just replace it
            incident = None

        if not incident:
            incident = Incident(attacker_ip=attacker_ip)
            self.active_incidents[attacker_ip] = incident
            self.ml_confidence_sums[attacker_ip] = 0.0

        # Update Incident
        incident.last_updated = now
        
        if alert_id and alert_id not in incident.alert_ids:
            incident.alert_ids.append(alert_id)
            
        if target_ip and target_ip not in incident.target_ips:
            incident.target_ips.append(target_ip)

        if progression:
            incident.mitre_tactics.append(progression)
            tactic_name = mitre_data.get("name", progression.tactic)
            if tactic_name not in incident.attack_chain:
                incident.attack_chain.append(tactic_name)

        # Assuming honeypot interactions have a specific marker in target_ip or category
        # Here we just increment if the category implies a honeypot hit
        category = alert.get("category") or alert.get("ml_classification", {}).get("category", "")
        if "Honeypot" in category or "Decoy" in category:
            incident.honeypot_interactions += 1

        self.ml_confidence_sums[attacker_ip] += confidence
        incident.severity = calculate_incident_severity(incident, self.ml_confidence_sums[attacker_ip])

        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        for inc in self.active_incidents.values():
            if inc.incident_id == incident_id:
                return inc
        return None
