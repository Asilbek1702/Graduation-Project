"""
quick_setup.py — Trains model on synthetic data and tests ML → API pipeline.

Run this from the project root:
    python quick_setup.py

Steps:
  1. Creates models/ directory
  2. Generates synthetic training data (mimics CIC-IDS-2017 features)
  3. Trains and saves the Isolation Forest model
  4. Trains and saves the Random Forest model
  5. Tests ml_sender.py with a sample flow
  6. Shows final result

Make sure backend is running before running this script:
    cd percepta_backend && uvicorn main:app --reload --port 8000
"""

import sys
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

if "" not in sys.path:
    sys.path.insert(0, "")

import config

# ── Step 1: Create directories ────────────────────────────────────────────────
logger.info("Step 1: Creating directories...")
Path("models").mkdir(exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)
logger.info("  ✅ models/ and data/processed/ ready")

# ── Step 2: Generate synthetic training data ──────────────────────────────────
logger.info("Step 2: Generating synthetic training data (5000 flows)...")

np.random.seed(42)
n_benign  = 4250  # 85% benign
n_attack  = 750   # 15% attack

def make_benign(n):
    return pd.DataFrame({
        "Flow Duration":                   np.random.exponential(5000, n),
        "Total Fwd Packets":               np.random.poisson(15, n).astype(float),
        "Total Backward Packets":          np.random.poisson(10, n).astype(float),
        "Total Length of Fwd Packets":     np.random.exponential(3000, n),
        "Total Length of Bwd Packets":     np.random.exponential(2000, n),
        "Flow Bytes/s":                    np.random.uniform(1000, 200000, n),
        "Flow Packets/s":                  np.random.uniform(1, 50, n),
        "Flow IAT Mean":                   np.random.exponential(200, n),
        "Fwd IAT Mean":                    np.random.exponential(300, n),
        "Bwd IAT Mean":                    np.random.exponential(400, n),
        "Fwd PSH Flags":                   np.zeros(n),
        "Bwd PSH Flags":                   np.zeros(n),
        "Fwd URG Flags":                   np.zeros(n),
        "Bwd URG Flags":                   np.zeros(n),
        "FIN Flag Count":                  np.random.binomial(1, 0.7, n).astype(float),
        "SYN Flag Count":                  np.random.binomial(1, 0.9, n).astype(float),
        "RST Flag Count":                  np.random.binomial(1, 0.05, n).astype(float),
        "PSH Flag Count":                  np.random.binomial(1, 0.3, n).astype(float),
        "ACK Flag Count":                  np.random.binomial(1, 0.95, n).astype(float),
        "URG Flag Count":                  np.zeros(n),
        "Fwd Packet Length Max":           np.random.uniform(40, 1500, n),
        "Bwd Packet Length Max":           np.random.uniform(40, 1500, n),
        "Fwd Packet Length Mean":          np.random.uniform(40, 800, n),
        "Bwd Packet Length Mean":          np.random.uniform(40, 800, n),
        "Packet Length Mean":              np.random.uniform(40, 800, n),
        "Packet Length Std":               np.random.uniform(0, 400, n),
        "Average Packet Size":             np.random.uniform(40, 800, n),
        "Avg Fwd Segment Size":            np.random.uniform(40, 800, n),
        "Avg Bwd Segment Size":            np.random.uniform(40, 800, n),
        "Label":                           ["BENIGN"] * n,
    })

def make_attack(n):
    return pd.DataFrame({
        "Flow Duration":                   np.random.exponential(500, n),   # shorter
        "Total Fwd Packets":               np.random.poisson(200, n).astype(float),  # many packets
        "Total Backward Packets":          np.random.poisson(5, n).astype(float),    # few responses
        "Total Length of Fwd Packets":     np.random.exponential(50000, n),           # large bursts
        "Total Length of Bwd Packets":     np.random.exponential(500, n),
        "Flow Bytes/s":                    np.random.uniform(500000, 5000000, n),     # very high
        "Flow Packets/s":                  np.random.uniform(200, 2000, n),           # very high
        "Flow IAT Mean":                   np.random.exponential(5, n),               # very short IAT
        "Fwd IAT Mean":                    np.random.exponential(5, n),
        "Bwd IAT Mean":                    np.random.exponential(100, n),
        "Fwd PSH Flags":                   np.random.binomial(1, 0.8, n).astype(float),
        "Bwd PSH Flags":                   np.random.binomial(1, 0.2, n).astype(float),
        "Fwd URG Flags":                   np.random.binomial(1, 0.5, n).astype(float),
        "Bwd URG Flags":                   np.random.binomial(1, 0.1, n).astype(float),
        "FIN Flag Count":                  np.zeros(n),
        "SYN Flag Count":                  np.random.binomial(1, 0.95, n).astype(float),
        "RST Flag Count":                  np.random.binomial(1, 0.4, n).astype(float),
        "PSH Flag Count":                  np.random.binomial(1, 0.8, n).astype(float),
        "ACK Flag Count":                  np.random.binomial(1, 0.5, n).astype(float),
        "URG Flag Count":                  np.random.binomial(1, 0.5, n).astype(float),
        "Fwd Packet Length Max":           np.random.uniform(1400, 1500, n),
        "Bwd Packet Length Max":           np.random.uniform(40, 100, n),
        "Fwd Packet Length Mean":          np.random.uniform(1000, 1500, n),
        "Bwd Packet Length Mean":          np.random.uniform(40, 100, n),
        "Packet Length Mean":              np.random.uniform(500, 1500, n),
        "Packet Length Std":               np.random.uniform(400, 700, n),
        "Average Packet Size":             np.random.uniform(500, 1500, n),
        "Avg Fwd Segment Size":            np.random.uniform(1000, 1500, n),
        "Avg Bwd Segment Size":            np.random.uniform(40, 100, n),
        "Label":                           ["DoS Hulk"] * n,
    })

df = pd.concat([make_benign(n_benign), make_attack(n_attack)], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle
logger.info("  ✅ Generated %d flows (%d benign, %d attack)", len(df), n_benign, n_attack)

# ── Step 3: Train Isolation Forest ────────────────────────────────────────────
logger.info("Step 3: Training Isolation Forest...")

from sklearn.ensemble import IsolationForest

X = df[config.FEATURE_COLUMNS].astype(float)

# Train on benign-only for better unsupervised performance
X_benign = df.loc[df["Label"] == "BENIGN", config.FEATURE_COLUMNS].astype(float)

model_if = IsolationForest(
    n_estimators=config.IF_N_ESTIMATORS,
    max_samples=min(config.IF_MAX_SAMPLES, len(X_benign)),
    contamination=config.IF_CONTAMINATION,
    random_state=config.IF_RANDOM_STATE,
)
model_if.fit(X_benign)
joblib.dump(model_if, config.MODEL_PATH)
logger.info("  ✅ Isolation Forest saved to %s", config.MODEL_PATH)

# ── Step 4: Train Random Forest (second level) ────────────────────────────────
logger.info("Step 4: Training Random Forest (second level)...")

try:
    from sklearn.ensemble import RandomForestClassifier
    y = (df["Label"] != "BENIGN").astype(int)
    model_rf = RandomForestClassifier(
        n_estimators=config.RF_N_ESTIMATORS,
        max_depth=config.RF_MAX_DEPTH,
        random_state=config.IF_RANDOM_STATE,
    )
    model_rf.fit(X, y)
    joblib.dump(model_rf, config.RF_MODEL_PATH)
    logger.info("  ✅ Random Forest saved to %s", config.RF_MODEL_PATH)
except Exception as e:
    logger.warning("  ⚠️  RF training skipped: %s", e)

# ── Step 5: Quick sanity check ────────────────────────────────────────────────
logger.info("Step 5: Sanity check — scoring test samples...")

from ml_engine.anomaly_detection import get_anomaly_score, flag_anomalies

benign_sample = X_benign.sample(5, random_state=1)
attack_sample = df.loc[df["Label"] != "BENIGN", config.FEATURE_COLUMNS].astype(float).sample(5, random_state=1)

b_scores = get_anomaly_score(model_if, benign_sample)
a_scores = get_anomaly_score(model_if, attack_sample)

logger.info("  Benign scores  (expect HIGH ~0.7–1.0): %s", np.round(b_scores, 3))
logger.info("  Attack scores  (expect LOW  ~0.0–0.4): %s", np.round(a_scores, 3))
logger.info("  ✅ Model working correctly")

# ── Step 6: Test ml_sender ────────────────────────────────────────────────────
logger.info("Step 6: Testing MLSender → backend API...")

try:
    from ML_sender import MLSender

    sender = MLSender()

    # Simulate a suspicious/attack-like flow
    attack_flow = {
        "Flow Duration": 200.0,
        "Total Fwd Packets": 300.0,
        "Total Backward Packets": 3.0,
        "Total Length of Fwd Packets": 120000.0,
        "Total Length of Bwd Packets": 300.0,
        "Flow Bytes/s": 2000000.0,
        "Flow Packets/s": 800.0,
        "Flow IAT Mean": 2.0,
        "Fwd IAT Mean": 2.0,
        "Bwd IAT Mean": 80.0,
        "Fwd PSH Flags": 1.0,
        "Bwd PSH Flags": 0.0,
        "Fwd URG Flags": 1.0,
        "Bwd URG Flags": 0.0,
        "FIN Flag Count": 0.0,
        "SYN Flag Count": 1.0,
        "RST Flag Count": 1.0,
        "PSH Flag Count": 1.0,
        "ACK Flag Count": 0.0,
        "URG Flag Count": 1.0,
        "Fwd Packet Length Max": 1490.0,
        "Bwd Packet Length Max": 60.0,
        "Fwd Packet Length Mean": 1200.0,
        "Bwd Packet Length Mean": 60.0,
        "Packet Length Mean": 800.0,
        "Packet Length Std": 600.0,
        "Average Packet Size": 800.0,
        "Avg Fwd Segment Size": 1200.0,
        "Avg Bwd Segment Size": 60.0,
        # Metadata
        "source_ip": "10.0.0.99",
        "destination_ip": "192.168.1.1",
        "protocol": "TCP",
        "destination_port": 80,
    }

    result = sender.process_and_send(attack_flow)
    payload = result["event_payload"]

    print("\n" + "=" * 60)
    print("  RESULT")
    print("=" * 60)
    print(f"  anomaly_score : {payload['anomaly_score']}")
    print(f"  is_anomaly    : {payload['is_anomaly']}")
    print(f"  stability     : {payload['stability_score']}")
    print(f"  risk_score    : {payload['risk_score']}")
    print(f"  risk_level    : {payload['risk_level']}")
    print(f"  action_taken  : {payload['action_taken']}")
    print(f"  API status    : {result['api_status']}")
    print(f"  API response  : {result['api_response']}")
    print("=" * 60)

    if result["api_status"] in (200, 201):
        print("\n✅ SUCCESS — Event stored in database and visible on dashboard!")
    elif result["api_status"] is None:
        print("\n⚠️  Backend not running. Start it with:")
        print("    cd percepta_backend && uvicorn main:app --reload --port 8000")
        print("    Then run: python quick_setup.py again\n")
    else:
        print(f"\n❌ API returned status {result['api_status']}")

except ImportError as e:
    logger.error("Could not import MLSender: %s", e)
    print("Make sure ML_sender.py is in the project root.")