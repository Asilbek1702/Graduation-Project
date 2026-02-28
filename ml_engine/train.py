"""Train the Isolation Forest model for the IDS/IPS system."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402
from ml_engine import anomaly_detection, feature_extraction  # noqa: E402

logger = logging.getLogger(__name__)


def _save_sample_with_scores(
    df: pd.DataFrame, scores: pd.Series, sample_size: int = 1000
) -> None:
    processed_dir = Path(config.DATA_PROCESSED_DIR)
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "sample_scored.csv"

    sample = df.copy()
    sample["anomaly_score"] = scores
    sample = sample.sample(n=min(sample_size, len(sample)), random_state=42)
    sample.to_csv(output_path, index=False)
    logger.info("Saved scored sample to %s", output_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    logger.info("Loading and cleaning data")
    df = feature_extraction.load_and_clean_data()

    logger.info("Selecting feature columns")
    X = df.loc[:, config.FEATURE_COLUMNS]

    logger.info("Training Isolation Forest model")
    model = anomaly_detection.train_model(X)

    logger.info("Scoring training data")
    scores = anomaly_detection.get_anomaly_score(model, X)

    mean_score = float(scores.mean())
    min_score = float(scores.min())
    max_score = float(scores.max())
    pct_anomalies = float((scores < config.T_BASE).mean() * 100.0)

    print(f"Mean score: {mean_score:.4f}")
    print(f"Min score: {min_score:.4f}")
    print(f"Max score: {max_score:.4f}")
    print(f"Percent flagged (< {config.T_BASE:.2f}): {pct_anomalies:.2f}%")

    _save_sample_with_scores(X, pd.Series(scores, index=X.index))


if __name__ == "__main__":
    main()
