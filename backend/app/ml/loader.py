import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier

logger = logging.getLogger("aegisnet.ml.loader")

MODEL_DIR = Path(os.getenv("MODEL_DIR", "/app/ml_models"))

ISOLATION_FOREST_PATH = MODEL_DIR / "isolation_forest.joblib"
RANDOM_FOREST_PATH    = MODEL_DIR / "random_forest.joblib"
LABEL_ENCODER_PATH    = MODEL_DIR / "label_encoder.joblib"

# Attack categories matching training labels
ATTACK_LABELS = ["Benign", "BruteForce", "DoS", "Exfiltration", "LateralMovement", "Reconnaissance", "WebAttack"]


class ModelRegistry:
    """
    Singleton model registry — loads models once at worker startup,
    exposes them for synchronous inference.
    """

    _instance: Optional["ModelRegistry"] = None

    def __init__(self):
        self.isolation_forest: Optional[IsolationForest] = None
        self.random_forest: Optional[RandomForestClassifier] = None
        self.label_classes: list = ATTACK_LABELS

    @classmethod
    def get(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)

        if ISOLATION_FOREST_PATH.exists():
            logger.info(f"[registry] Loading IsolationForest from {ISOLATION_FOREST_PATH}")
            self.isolation_forest = joblib.load(ISOLATION_FOREST_PATH)
        else:
            logger.warning("[registry] IsolationForest model not found — initialising with defaults for development.")
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                contamination=0.05,
                random_state=42,
            )

        if RANDOM_FOREST_PATH.exists():
            logger.info(f"[registry] Loading RandomForest from {RANDOM_FOREST_PATH}")
            self.random_forest = joblib.load(RANDOM_FOREST_PATH)
            if LABEL_ENCODER_PATH.exists():
                encoder = joblib.load(LABEL_ENCODER_PATH)
                self.label_classes = list(encoder.classes_)
        else:
            logger.warning("[registry] RandomForest model not found — initialising with defaults for development.")
            self.random_forest = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
            )

    def save(self) -> None:
        joblib.dump(self.isolation_forest, ISOLATION_FOREST_PATH)
        joblib.dump(self.random_forest, RANDOM_FOREST_PATH)
        logger.info("[registry] Models saved to disk.")

    def is_trained(self) -> bool:
        try:
            return (
                hasattr(self.isolation_forest, "estimators_")
                and hasattr(self.random_forest, "estimators_")
            )
        except Exception:
            return False
