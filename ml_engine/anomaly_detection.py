"""Isolation Forest training and inference for IDS/IPS anomaly detection."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402

logger = logging.getLogger(__name__)


def train_model(X: pd.DataFrame) -> IsolationForest:
    model = IsolationForest(
        n_estimators=config.IF_N_ESTIMATORS,
        max_samples=config.IF_MAX_SAMPLES,
        contamination=config.IF_CONTAMINATION,
        random_state=config.IF_RANDOM_STATE,
    )
    model.fit(X)

    model_path = Path(config.MODEL_PATH)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    logger.info("Model training complete. Saved to %s", model_path)
    return model


def load_model() -> IsolationForest:
    model_path = Path(config.MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")

    logger.info("Loading model from %s", model_path)
    return joblib.load(model_path)


def get_anomaly_score(model: IsolationForest, X: pd.DataFrame) -> np.ndarray:
    scores = model.score_samples(X)
    min_score = scores.min()
    max_score = scores.max()
    if max_score == min_score:
        logger.warning("All anomaly scores identical; returning zeros for normalized scores.")
        return np.zeros_like(scores, dtype=float)

    normalized = (scores - min_score) / (max_score - min_score)
    return normalized


def flag_anomalies(scores: np.ndarray, threshold: float | None = None) -> np.ndarray:
    if threshold is None:
        threshold = config.T_BASE
    return scores < threshold
