import random
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

# Basic realistic IP ranges for simulation
EXTERNAL_IPS = [f"185.15.55.{i}" for i in range(1, 20)] + [f"194.22.44.{i}" for i in range(1, 10)]
INTERNAL_IPS = [f"10.0.0.{i}" for i in range(10, 250)]

class ZeekFlowGenerator:
    """Generates Zeek conn.log compatible telemetry flows."""
    
    @staticmethod
    def generate_flow(
        source_ip: str, 
        dest_ip: str, 
        dest_port: int, 
        proto: str = "tcp",
        service: str = "-",
        duration: float = 0.0,
        orig_bytes: int = 0,
        resp_bytes: int = 0,
        conn_state: str = "SF",
        history: str = "SAD",
        is_malicious: bool = False
    ) -> Dict[str, Any]:
        
        timestamp = time.time()
        
        return {
            "flow_id": f"C{uuid.uuid4().hex[:17]}",
            "source_ip": source_ip,
            "dest_ip": dest_ip,
            "dest_port": str(dest_port),
            "proto": proto,
            "service": service,
            "duration": str(duration),
            "orig_bytes": str(orig_bytes),
            "resp_bytes": str(resp_bytes),
            "conn_state": conn_state,
            "orig_pkts": str(random.randint(1, 10) if orig_bytes > 0 else 0),
            "resp_pkts": str(random.randint(1, 10) if resp_bytes > 0 else 0),
            "log_hash": "simulated",
            "ts": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
            "_simulated_malicious": is_malicious  # Used for metrics, won't be seen by ML
        }
