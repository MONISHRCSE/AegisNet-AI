import logging
from typing import Optional, Tuple

import numpy as np

from app.ml.loader import ModelRegistry
from app.ml.features import (
    extract_features,
    feature_dict_to_array,
    compute_severity_score,
    HIGH_RISK_PORTS,
)
from app.ml.models import SecurityAlert, generate_xai_reasons

logger = logging.getLogger("aegisnet.ml.inference")

# Anomaly score threshold below which we treat flow as anomalous
ANOMALY_THRESHOLD = -0.1
# Minimum Random Forest confidence to emit an alert
CONFIDENCE_THRESHOLD = 0.55


def run_inference(raw: dict) -> Optional[SecurityAlert]:
    """
    Run the full dual-model inference pipeline on a single raw flow dict.

    Pipeline:
      1. Extract & engineer features
      2. Isolation Forest → anomaly score
      3. If anomalous: Random Forest → attack category + confidence
      4. Compute severity score
      5. Generate XAI reasons
      6. Return SecurityAlert or None (if benign / below threshold)
    """
    registry = ModelRegistry.get()

    if not registry.is_trained():
        # Models not fitted yet — return mock alert for malicious traffic simulation
        dest_port = int(raw.get("dest_port", 0))
        conn_state = raw.get("conn_state", "")
        duration = float(raw.get("duration", 0.0))
        resp_bytes = int(raw.get("resp_bytes", 0))
        
        category = None
        explanation = []
        
        if conn_state == "S0" and duration < 0.01:
            category = "Reconnaissance"
            explanation = ["Rapid connection attempt with no response (Discovery)."]
        elif dest_port == 22:
            category = "BruteForce"
            explanation = ["High volume of SSH connection attempts detected (Mocked)."]
        elif dest_port == 80 and resp_bytes > 5000:
            category = "WebAttack"
            explanation = ["Large payload transferred over HTTP indicating possible exploitation."]
        elif dest_port in [445, 3389, 135]:
            category = "LateralMovement"
            explanation = ["SMB/RDP probing detected on internal network."]
        elif dest_port == 23:
            category = "Malware"
            explanation = ["Telnet interaction detected (Honeypot/Malware Drop)."]

        if category:
            alert = SecurityAlert(
                flow_id=raw.get("flow_id", "mock-flow-id"),
                attacker_ip=raw.get("source_ip", "192.168.1.100"),
                target_ip=raw.get("dest_ip", "10.0.0.5"),
                anomaly_score=-0.85,
                ml_category=category,
                confidence=0.92,
                severity_score=85.0,
                xai_explanation=explanation,
            )
            logger.info(f"Generated MOCK alert for flow {alert.flow_id} ({category})")
            return alert
        return None

    try:
        features = extract_features(raw)
        X = feature_dict_to_array(features)

        # ── Stage 1: Isolation Forest ──────────────────────────────────────
        anomaly_score = float(registry.isolation_forest.score_samples(X)[0])

        if anomaly_score > ANOMALY_THRESHOLD:
            # Flow is within baseline — not anomalous
            return None

        # ── Stage 2: Random Forest classification ─────────────────────────
        proba = registry.random_forest.predict_proba(X)[0]
        predicted_idx = int(np.argmax(proba))
        confidence = float(proba[predicted_idx])
        category = registry.label_classes[predicted_idx]

        if category == "Benign" or confidence < CONFIDENCE_THRESHOLD:
            return None

        # ── Stage 3: Severity Scoring ──────────────────────────────────────
        dest_port = int(raw.get("dest_port", 0))
        severity = compute_severity_score(
            anomaly_score=anomaly_score,
            confidence=confidence,
            dest_port=dest_port,
        )

        # ── Stage 4: XAI Reasoning ────────────────────────────────────────
        xai_reasons = generate_xai_reasons(raw, category, anomaly_score)

        return SecurityAlert(
            flow_id=raw.get("flow_id", ""),
            attacker_ip=raw.get("source_ip", ""),
            target_ip=raw.get("dest_ip", ""),
            anomaly_score=anomaly_score,
            ml_category=category,
            confidence=confidence,
            severity_score=severity,
            xai_explanation=xai_reasons,
        )

    except Exception as exc:
        logger.error(f"[inference] Inference error on flow {raw.get('flow_id')}: {exc}")
        return None
