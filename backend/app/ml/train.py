"""
AegisNet AI — Model Training Script
Trains IsolationForest + RandomForestClassifier on CICIDS2017 CSV.
Usage: python -m app.ml.train --dataset /data/cicids2017_flows.csv
"""
import argparse
import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

logger = logging.getLogger("aegisnet.ml.train")
logging.basicConfig(level=logging.INFO, format="%(levelname)-5.5s [%(name)s] %(message)s")

MODEL_DIR = Path(os.getenv("MODEL_DIR", "./ml_models"))

CICIDS_FEATURE_MAP = {
    "Flow Duration":               "duration",
    "Total Fwd Packets":           "orig_pkts",
    "Total Bwd Packets":           "resp_pkts",
    "Total Length of Fwd Packets": "orig_bytes",
    "Total Length of Bwd Packets": "resp_bytes",
    "Destination Port":            "dest_port",
}
LABEL_COL = "Label"


def train(csv_path: str) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()
    df = df.rename(columns=CICIDS_FEATURE_MAP)
    feature_cols = list(CICIDS_FEATURE_MAP.values())
    df = df.dropna(subset=feature_cols + [LABEL_COL])
    df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], 0).clip(lower=0)

    scaler = MinMaxScaler()
    X = scaler.fit_transform(df[feature_cols].astype(np.float32))

    le = LabelEncoder()
    y = le.fit_transform(df[LABEL_COL].str.strip())
    joblib.dump(le, MODEL_DIR / "label_encoder.joblib")
    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")

    benign_mask = (le.inverse_transform(y) == "BENIGN")
    iso = IsolationForest(n_estimators=150, contamination=0.05, random_state=42, n_jobs=-1)
    iso.fit(X[benign_mask])
    joblib.dump(iso, MODEL_DIR / "isolation_forest.joblib")
    logger.info("IsolationForest saved.")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    rf = RandomForestClassifier(n_estimators=200, max_depth=20, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    joblib.dump(rf, MODEL_DIR / "random_forest.joblib")
    logger.info("RandomForest saved.")

    y_pred = rf.predict(X_test)
    logger.info("\n" + classification_report(y_test, y_pred, target_names=le.classes_))
    logger.info(f"Macro F1: {f1_score(y_test, y_pred, average='macro'):.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    train(args.dataset)
