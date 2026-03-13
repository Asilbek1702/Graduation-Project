# Adaptive IDS/IPS — Anomaly Detection in University Networks

## 1. Overview
This project is an anomaly-based Intrusion Detection and Prevention System (IDS/IPS)
for university networks. It uses a two-level semi-supervised pipeline:
Level 1 is Isolation Forest for unsupervised anomaly detection,
and Level 2 is Random Forest to confirm detected anomalies.
The system adapts thresholds based on network load and applies
multi-level responses (Log / Monitor / Rate Limit / Block).

## 2. Team
- Mirkomil Mirzohidov — AI/ML Engineer (anomaly detection, feature extraction, model training)
- Muhammad Saidahmetov — Network & Security Engineer (IPS logic, stability, risk engine, database)
- Asilbek Tashpulatov — Web & Backend Lead (FastAPI, React dashboard)

## 3. Project Structure
```
project/
├── data/
│   ├── raw/CIC-IDS-2017/          # original dataset CSV files
│   └── processed/                 # cleaned features and scored samples
├── ml_engine/
│   ├── feature_extraction.py      # load and clean CIC-IDS-2017 data
│   ├── anomaly_detection.py       # Isolation Forest training and scoring
│   ├── semi_supervised.py         # Random Forest second-level classifier
│   ├── stability_module.py        # Temporal Stability Module
│   ├── threshold_controller.py    # Adaptive Threshold Controller
│   ├── risk_engine.py             # Risk score computation
│   ├── decision_engine.py         # Multi-Level Decision Engine
│   ├── train.py                   # training entry point (both models)
│   └── evaluate.py                # evaluation and threshold sweep
├── models/
│   ├── isolation_forest.pkl       # Level 1 — unsupervised anomaly detector
│   └── random_forest.pkl          # Level 2 — semi-supervised attack confirmer
├── ips/                           # IPS actions (block, rate limit, escalation)
├── api/                           # FastAPI backend
├── web/                           # React frontend dashboard
├── database/                      # DB models and queries
├── logs/                          # system logs
└── config.py                      # all system parameters
```

## 4. Setup & Installation
```
git clone <YOUR_REPO_URL>
cd project
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate          # Linux / Mac
pip install -r requirements.txt
```

Required packages:
scikit-learn, pandas, numpy, joblib, fastapi, uvicorn, pyarrow

## 5. Training the Models
```
# From the project root:
python -m ml_engine.train
```

This will:
1. Load and clean all CIC-IDS-2017 CSV files (29 features, ~1.97M flows)
2. Train Isolation Forest with balanced 10:1 benign:attack ratio
3. Save Isolation Forest to models/isolation_forest.pkl
4. Train Random Forest on full labeled dataset with class_weight="balanced"
5. Save Random Forest to models/random_forest.pkl
6. Output scored sample to data/processed/sample_scored.csv

## 6. Evaluation
```
# From the project root:
python -m ml_engine.evaluate
```

Evaluation results on CIC-IDS-2017 (1,976,336 flows):

Isolation Forest only (T=0.75):
  Precision:   51.9%
  Recall:      75.9%
  F1 Score:    0.6165
  FPR:         13.9%
  Accuracy:    84.4%

Combined IF + Random Forest (T=0.75, RF_proba >= 0.50):
  Precision:   99.9%
  Recall:      75.9%
  F1 Score:    0.8626
  FPR:         0.02%
  Accuracy:    96.0%

The Random Forest second-level classifier reduced false positives
from 229,348 to just 259 — a 99.9% reduction in false alarms.

### Random Forest Overfitting Check
  Train F1:  0.9943
  Test F1:   0.9927
  Gap:       0.0016 (threshold: 0.05)
  Status:    PASSED — no overfitting detected

## 7. How the ML Pipeline Works
The pipeline has two levels:

Level 1 — Isolation Forest (unsupervised):
- Analyzes each network flow and assigns an anomaly score between 0 and 1
- Score close to 0 = anomalous, score close to 1 = normal
- Flags flow as suspicious if score < T_BASE (0.75)
- Threshold adapts based on current network load

Level 2 — Random Forest (semi-supervised):
- Receives all flows flagged by Level 1
- Predicts probability of attack using labeled training data
- Confirms attack only if RF probability >= 0.50
- Final flag = Level 1 flagged AND Level 2 confirmed

Full pipeline steps:
1. Feature Extraction — load and clean CSV data (29 features)
2. Isolation Forest — assign anomaly score per flow
3. Adaptive Threshold — adjusts based on network load:
     Low load:    T = 0.80 (strict)
     Medium load: T = 0.75 (normal)
     High load:   T = 0.68 (relaxed, fewer false positives)
4. Random Forest — confirms anomalies flagged by Isolation Forest
5. Temporal Stability Module — sliding 30-second window computes
   Count, Frequency, Duration → StabilityScore
6. Risk Engine — Risk = 0.5 * A_norm + 0.3 * StabilityScore + 0.2 * (1 - Load)
7. Decision Engine — maps Risk to action: LOG / MONITOR / RATE_LIMIT / TEMP_BLOCK

## 8. Risk Levels & Actions
| Risk Score  | Level    | Action          | Duration |
|-------------|----------|-----------------|----------|
| < 0.30      | LOW      | Log             | —        |
| 0.30–0.50   | MEDIUM   | Monitor         | —        |
| 0.50–0.75   | HIGH     | Rate Limit      | 60 sec   |
| >= 0.75     | CRITICAL | Temporary Block | 120 sec  |

Escalation: if the same IP receives CRITICAL twice within 5 minutes,
block duration increases to 300 seconds. Three times → 600 seconds.

## 9. Configuration
All parameters are defined in config.py. Key settings:

-  T_BASE = 0.75                 # anomaly threshold (optimized by evaluation)
-  T_LOW_LOAD = 0.80             # strict mode
-  T_MEDIUM_LOAD = 0.75          # normal mode
-  T_HIGH_LOAD = 0.68            # relaxed mode
-  WINDOW_SIZE = 30              # seconds for stability module
-  IF_CONTAMINATION = 0.15       # Isolation Forest contamination
-  IF_N_ESTIMATORS = 200         # Isolation Forest trees
-  RF_N_ESTIMATORS = 200         # Random Forest trees
-  RF_PROBA_THRESHOLD = 0.50     # RF confirmation threshold
-  BLOCK_DURATION = 120          # seconds

## 10. Dataset
Name:   CIC-IDS-2017 (Canadian Institute for Cybersecurity)
Size:   ~1.97 million network flows
Place CSV files in: data/raw/CIC-IDS-2017/
Link:   https://www.unb.ca/cic/datasets/ids-2017.html

Attack types in dataset:
- DoS Hulk (166,086 flows)
- DDoS (127,619 flows)
- DoS GoldenEye (10,281 flows)
- DoS Slowhttptest (5,162 flows)
- DoS slowloris (4,870 flows)
- FTP-Patator, SSH-Patator, PortScan, Web Attack, Bot, and others

## 11. Why Are the Metrics So High?

The combined pipeline achieves Precision 99.9%, Recall 75.9%,
F1 0.8626, and Accuracy 96.0%. These numbers are high for the
following reasons:

1. Nature of the dataset
   CIC-IDS-2017 is a lab-generated dataset created under controlled
   conditions. Attack traffic was generated using specific tools
   (LOIC, GoldenEye, Slowloris) with consistent and repeatable
   patterns. This makes attacks easier to detect compared to
   real-world traffic where attack behavior is more varied and mixed
   with legitimate traffic.

2. Two-level architecture
   The pipeline combines two complementary models:
   - Isolation Forest catches anomalies without any labels
   - Random Forest confirms only real attacks using labeled data
   Together they eliminate almost all false positives while
   maintaining strong recall.

3. Overfitting check passed
   The gap between train F1 (0.9943) and test F1 (0.9927) is only
   0.0016, well below the 0.05 threshold. This confirms the model
   generalizes well within this dataset and has not memorized
   training data.

4. Expected real-world performance
   In a real university network, metrics will be lower due to:
   - Unknown and evolving attack patterns not seen in training
   - Higher traffic variability and noise
   - Mixed legitimate and malicious behavior harder to separate

   Realistic estimates for production deployment:
     Precision: 70-80%
     Recall:    60-70%
     F1:        0.65-0.75

   The Isolation Forest component remains useful in production
   because it detects unknown attacks without requiring labeled data.
   The Random Forest component can be retrained periodically as
   new labeled data becomes available.
