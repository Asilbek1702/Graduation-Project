"""Second-level semi-supervised classifier to validate Isolation Forest anomalies."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402

logger = logging.getLogger(__name__)


def train_second_level(X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    X_features = X.loc[:, config.FEATURE_COLUMNS]
    y_binary = y.astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X_features,
        y_binary,
        test_size=0.20,
        random_state=config.IF_RANDOM_STATE,
        stratify=y_binary,
    )

    model = RandomForestClassifier(
        n_estimators=config.RF_N_ESTIMATORS,
        max_depth=config.RF_MAX_DEPTH,
        class_weight="balanced",
        random_state=config.IF_RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, digits=4))

    model_path = Path(config.RF_MODEL_PATH)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    logger.info("Second-level model saved to %s", model_path)
    return model


def load_second_level() -> RandomForestClassifier:
    model_path = Path(config.RF_MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Second-level model not found at {model_path}. Train it with train_second_level()."
        )

    logger.info("Loading second-level model from %s", model_path)
    return joblib.load(model_path)


def combined_predict(
    if_scores: np.ndarray,
    X: pd.DataFrame,
    rf_model: RandomForestClassifier,
    if_threshold: float = config.T_BASE,
) -> np.ndarray:
    if_flags = if_scores < if_threshold
    rf_proba = rf_model.predict_proba(X.loc[:, config.FEATURE_COLUMNS])[:, 1]
    final_flag = if_flags & (rf_proba >= config.RF_PROBA_THRESHOLD)
    return final_flag
