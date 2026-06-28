import time
import json
from typing import Dict, Any
from app.db.mongodb import db

class SimulationMetrics:
    def __init__(self):
        self.metrics = {
            "total_attacks_simulated": 0,
            "incidents_generated": 0,
            "detection_latency_ms": [],
            "correlation_latency_ms": []
        }

    def record_attack(self):
        self.metrics["total_attacks_simulated"] += 1

    async def calculate_end_of_run_metrics(self):
        """Calculates final metrics across the DB."""
        # Simple count for demonstration
        self.metrics["incidents_generated"] = await db.db.incidents.count_documents({})
        
        # Calculate latency averages
        avg_det = sum(self.metrics["detection_latency_ms"]) / max(1, len(self.metrics["detection_latency_ms"]))
        avg_cor = sum(self.metrics["correlation_latency_ms"]) / max(1, len(self.metrics["correlation_latency_ms"]))
        
        self.metrics["avg_detection_latency_ms"] = avg_det
        self.metrics["avg_correlation_latency_ms"] = avg_cor

    def export(self, filepath: str = "simulator_metrics.json"):
        with open(filepath, 'w') as f:
            json.dump(self.metrics, f, indent=4)
