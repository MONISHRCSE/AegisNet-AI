import numpy as np
import pandas as pd
from typing import Dict, List

# ── Feature columns expected by trained models ───────────────────────────────
FEATURE_COLUMNS = [
    "duration",
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "resp_pkts",
    "dest_port",
    "bytes_per_pkt_orig",
    "bytes_per_pkt_resp",
    "pkt_ratio",
    "byte_ratio",
    "proto_tcp",
    "proto_udp",
    "proto_icmp",
    "conn_state_SF",
    "conn_state_REJ",
    "conn_state_RSTO",
    "conn_state_RSTOS0",
    "conn_state_S0",
    "conn_state_OTH",
]

# High-risk ports that elevate severity
HIGH_RISK_PORTS = {22, 23, 25, 53, 80, 443, 445, 3306, 3389, 5432, 5900, 6379, 8080, 27017}


def extract_features(raw: Dict) -> Dict:
    """
    Convert a raw Redis stream record into a feature dict.
    raw keys: flow_id, source_ip, dest_ip, dest_port, proto,
              service, duration, orig_bytes, resp_bytes,
              conn_state, orig_pkts, resp_pkts, log_hash, ts
    """
    duration   = float(raw.get("duration", 0)) or 1e-6  # avoid div-by-zero
    orig_bytes = float(raw.get("orig_bytes", 0))
    resp_bytes = float(raw.get("resp_bytes", 0))
    orig_pkts  = max(int(raw.get("orig_pkts", 1)), 1)
    resp_pkts  = max(int(raw.get("resp_pkts", 1)), 1)
    dest_port  = int(raw.get("dest_port", 0))
    proto      = raw.get("proto", "").lower()
    conn_state = raw.get("conn_state", "OTH")

    features = {
        "duration":          duration,
        "orig_bytes":        orig_bytes,
        "resp_bytes":        resp_bytes,
        "orig_pkts":         orig_pkts,
        "resp_pkts":         resp_pkts,
        "dest_port":         dest_port,
        "bytes_per_pkt_orig": orig_bytes / orig_pkts,
        "bytes_per_pkt_resp": resp_bytes / resp_pkts,
        "pkt_ratio":         orig_pkts / resp_pkts,
        "byte_ratio":        orig_bytes / (resp_bytes + 1),
        # Protocol one-hot
        "proto_tcp":  int(proto == "tcp"),
        "proto_udp":  int(proto == "udp"),
        "proto_icmp": int(proto == "icmp"),
        # Connection state one-hot
        "conn_state_SF":     int(conn_state == "SF"),
        "conn_state_REJ":    int(conn_state == "REJ"),
        "conn_state_RSTO":   int(conn_state == "RSTO"),
        "conn_state_RSTOS0": int(conn_state == "RSTOS0"),
        "conn_state_S0":     int(conn_state == "S0"),
        "conn_state_OTH":    int(conn_state not in ("SF", "REJ", "RSTO", "RSTOS0", "S0")),
    }
    return features


def feature_dict_to_array(features: Dict) -> np.ndarray:
    """Return features as a row array in the correct column order."""
    return np.array([features[col] for col in FEATURE_COLUMNS], dtype=np.float32).reshape(1, -1)


def compute_severity_score(
    anomaly_score: float,
    confidence: float,
    dest_port: int,
    asset_criticality: float = 1.0,
) -> float:
    """
    Severity = base_score * port_risk_multiplier * asset_criticality, capped at 10.0

    anomaly_score: Isolation Forest output scaled to [0, 1] (higher = more anomalous)
    confidence:    Random Forest class probability for the detected category
    """
    base_score = (abs(anomaly_score) * 0.4 + confidence * 0.6) * 10.0
    port_multiplier = 1.3 if dest_port in HIGH_RISK_PORTS else 1.0
    severity = base_score * port_multiplier * asset_criticality
    return min(round(severity, 2), 10.0)
