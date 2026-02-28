# Adaptive IDS/IPS — Anomaly Detection in University Networks

## 1. Overview
This project is an anomaly-based Intrusion Detection and Prevention System (IDS/IPS) for university networks. It uses Isolation Forest to detect unknown attacks without signatures, adapts thresholds based on network load, and applies multi-level responses (Log / Monitor / Rate Limit / Block).

## 2. Team
- Mirkomil Mirzohidov — AI/ML Engineer (anomaly detection, feature extraction, model training)
- Muhammad Saidahmetov — Network & Security Engineer (IPS logic, stability, risk engine, database)
- Asilbek Tashpulatov — Web & Backend Lead (FastAPI, React dashboard)

## 3. Project Structure
```
project/
├── data/
│   ├── raw/CIC-IDS-2017/     # original dataset CSV files
│   └── processed/            # cleaned features and scored samples
├── ml_engine/
│   ├── feature_extraction.py # load and clean CIC-IDS-2017 data
│   ├── anomaly_detection.py  # Isolation Forest training and scoring
│   ├── stability_module.py   # Temporal Stability Module
│   ├── threshold_controller.py # Adaptive Threshold Controller
│   ├── risk_engine.py        # Risk score computation
│   ├── decision_engine.py    # Multi-Level Decision Engine
│   └── train.py              # training entry point
├── models/
│   └── isolation_forest.pkl  # saved trained model
├── ips/                      # IPS actions (block, rate limit, escalation)
├── api/                      # FastAPI backend
├── web/                      # React frontend dashboard
├── database/                 # DB models and queries
├── logs/                     # system logs
└── config.py                 # all system parameters
```

## 4. Setup & Installation
Commands:
```
git clone <YOUR_REPO_URL>
cd project
pip install -r requirements.txt
```

Required packages:
scikit-learn, pandas, numpy, joblib, fastapi, uvicorn, pyarrow

## 5. Training the Model
Commands:
```
# From the project root:
python -m ml_engine.train
```

This loads CIC-IDS-2017 CSVs, cleans them, trains the Isolation Forest model, saves it to `models/isolation_forest.pkl`, and outputs a scored sample to `data/processed/sample_scored.csv`.

## 6. How the ML Pipeline Works
1. Feature Extraction — load and clean CSV data (29 selected features from CIC-IDS-2017)
2. Isolation Forest — assign anomaly score [0,1] per flow (n_estimators=200, max_samples=512, contamination=0.15)
3. Adaptive Threshold — threshold adjusts based on network load (Low load: 0.80, Medium: 0.75, High: 0.68)
4. Temporal Stability Module — sliding 30-second window computes Count, Frequency, Duration → StabilityScore
5. Risk Engine — Risk = 0.5 × A_norm + 0.3 × StabilityScore + 0.2 × (1 − Load)
6. Decision Engine — maps Risk to: LOG / MONITOR / RATE_LIMIT / TEMP_BLOCK

## 7. Risk Levels & Actions
| Risk Score | Level    | Action         |
|------------|----------|----------------|
| < 0.30     | LOW      | Log            |
| 0.30–0.50  | MEDIUM   | Monitor        |
| 0.50–0.75  | HIGH     | Rate Limit (60s) |
| ≥ 0.75     | CRITICAL | Block (120s)   |

## 8. Configuration
All parameters are defined in `config.py`. Key settings include:

| Parameter | Value | Description |
|-----------|-------|-------------|
| IF_N_ESTIMATORS | 200 | Number of trees in Isolation Forest |
| IF_MAX_SAMPLES | 512 | Sub-sample size per tree |
| IF_CONTAMINATION | 0.15 | Expected proportion of anomalies |
| T_BASE | 0.75 | Base anomaly threshold |
| T_LOW_LOAD | 0.80 | Strict threshold (low network load) |
| T_MEDIUM_LOAD | 0.75 | Normal threshold |
| T_HIGH_LOAD | 0.68 | Relaxed threshold (high network load) |
| WINDOW_SIZE | 30 | Stability window (seconds) |
| RATE_LIMIT_DURATION | 60 | Rate-limit duration (seconds) |
| BLOCK_DURATION | 120 | Block duration (seconds) |
| BLOCK_ESCALATION_2X | 300 | 2nd CRITICAL block (seconds) |
| BLOCK_ESCALATION_3X | 600 | 3rd CRITICAL block (seconds) |

## 9. Evaluation Results
Model evaluated on the full CIC-IDS-2017 dataset:

| Metric | Value |
|--------|-------|
| Total Flows | 1,976,336 |
| Real Attacks | 326,164 |
| Real Benign | 1,650,172 |
| True Positives (TP) | 247,562 |
| True Negatives (TN) | 1,420,824 |
| False Positives (FP) | 229,348 |
| False Negatives (FN) | 78,602 |
| **Accuracy** | **84.42%** |
| Precision | 51.91% |
| Recall | 75.90% |
| F1 Score | 0.6165 |
| False Positive Rate | 13.90% |

## 10. Features Used
The model is trained on 29 flow-level features extracted from CIC-IDS-2017:

`Flow Duration`, `Total Fwd Packets`, `Total Backward Packets`, `Total Length of Fwd Packets`, `Total Length of Bwd Packets`, `Flow Bytes/s`, `Flow Packets/s`, `Flow IAT Mean`, `Fwd IAT Mean`, `Bwd IAT Mean`, `Fwd PSH Flags`, `Bwd PSH Flags`, `Fwd URG Flags`, `Bwd URG Flags`, `FIN Flag Count`, `SYN Flag Count`, `RST Flag Count`, `PSH Flag Count`, `ACK Flag Count`, `URG Flag Count`, `Fwd Packet Length Max`, `Bwd Packet Length Max`, `Fwd Packet Length Mean`, `Bwd Packet Length Mean`, `Packet Length Mean`, `Packet Length Std`, `Average Packet Size`, `Avg Fwd Segment Size`, `Avg Bwd Segment Size`

## 11. Dataset
Name: CIC-IDS-2017 (Canadian Institute for Cybersecurity)
Place CSV files in: `data/raw/CIC-IDS-2017/`
Link: https://www.unb.ca/cic/datasets/ids-2017.html
