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
1. Feature Extraction — load and clean CSV data
2. Isolation Forest — assign anomaly score [0,1] per flow
3. Adaptive Threshold — threshold adjusts based on network load (Low: 0.35, Medium: 0.30, High: 0.25)
4. Temporal Stability Module — sliding 30-second window computes Count, Frequency, Duration → StabilityScore
5. Risk Engine — Risk = 0.5 * A_norm + 0.3 * StabilityScore + 0.2 * (1 - Load)
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
- T_BASE = 0.30 (base anomaly threshold)
- WINDOW_SIZE = 30 (seconds)
- IF_CONTAMINATION = 0.05
- BLOCK_DURATION = 120 (seconds)

## 9. Dataset
Name: CIC-IDS-2017 (Canadian Institute for Cybersecurity)
Place CSV files in: `data/raw/CIC-IDS-2017/`
Link: https://www.unb.ca/cic/datasets/ids-2017.html
