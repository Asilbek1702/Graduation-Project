"""Single source of truth for all system parameters used by the adaptive IDS/IPS system."""

# === PATHS ===
DATA_RAW_DIR = "data/raw/CIC-IDS-2017"
DATA_PROCESSED_DIR = "data/processed"
MODEL_PATH = "models/isolation_forest.pkl"

# === ISOLATION FOREST PARAMS ===
IF_N_ESTIMATORS = 200
IF_MAX_SAMPLES = 512
IF_CONTAMINATION = 0.15
IF_RANDOM_STATE = 42
RF_N_ESTIMATORS = 200
RF_MAX_DEPTH = 20
RF_PROBA_THRESHOLD = 0.50
RF_MODEL_PATH = "models/random_forest.pkl"

# === ANOMALY THRESHOLD (base) ===
T_BASE = 0.75
T_LOW_LOAD = 0.80     # strict mode (low network load)
T_MEDIUM_LOAD = 0.75  # normal mode
T_HIGH_LOAD = 0.68    # relaxed mode (high network load, avoid false positives)

# === EVALUATION THRESHOLDS ===
EVAL_THRESHOLDS = [0.70, 0.72, 0.75, 0.78, 0.80]

# === NETWORK LOAD LEVELS ===
LOAD_LOW_MAX = 0.30
LOAD_HIGH_MIN = 0.70

# === TEMPORAL STABILITY MODULE ===
WINDOW_SIZE = 30       # seconds
DELTA_T = 1            # seconds
COUNT_CEILING = 8      # max anomalies before capping C at 1.0
FREQ_CEILING = 0.25    # high frequency threshold
DURATION_CEILING = 6   # max consecutive anomalies before capping D at 1.0

# Stability score weights
W_COUNT = 0.4
W_FREQ = 0.3
W_DURATION = 0.3

# Stability score zones
STABILITY_LOW = 0.30
STABILITY_MEDIUM = 0.55
STABILITY_HIGH = 0.75

# === RISK ENGINE ===
W_ANOMALY = 0.5
W_STABILITY = 0.3
W_LOAD = 0.2

# Risk zones → action
RISK_LOW = 0.30
RISK_MEDIUM = 0.50
RISK_HIGH = 0.75

# === IPS ACTIONS ===
RATE_LIMIT_DURATION = 60       # seconds
BLOCK_DURATION = 120           # seconds
BLOCK_ESCALATION_2X = 300      # seconds, after 2nd CRITICAL in 5 min
BLOCK_ESCALATION_3X = 600      # seconds, after 3rd CRITICAL

# === FEATURES USED FOR TRAINING ===
FEATURE_COLUMNS = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Fwd IAT Mean",
    "Bwd IAT Mean",
    "Fwd PSH Flags",
    "Bwd PSH Flags",
    "Fwd URG Flags",
    "Bwd URG Flags",
    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "Fwd Packet Length Max",
    "Bwd Packet Length Max",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Packet Length Mean",
    "Packet Length Std",
    "Average Packet Size",
    "Avg Fwd Segment Size",
    "Avg Bwd Segment Size",
]
