"""Train the Isolation Forest model for the IDS/IPS system."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

import pandas as pd

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402
from ml_engine import anomaly_detection, feature_extraction, semi_supervised  # noqa: E402

logger = logging.getLogger(__name__)


def _csv_files(data_dir: str | Path) -> List[Path]:
    data_path = Path(data_dir)
    return sorted(data_path.glob("*.csv"))


def _load_raw_with_labels() -> pd.DataFrame:
    csv_files = _csv_files(config.DATA_RAW_DIR)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {config.DATA_RAW_DIR}")

    logger.info("Loading %d raw CSV files from %s", len(csv_files), config.DATA_RAW_DIR)

    frames: List[pd.DataFrame] = []
    for csv_path in csv_files:
        logger.info("Reading %s", csv_path)
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        if "Label" not in df.columns:
            raise ValueError(f"Missing Label column in {csv_path}")
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)

    required_columns = list(config.FEATURE_COLUMNS) + ["Label"]
    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns in raw data: {missing}")

    data = data.loc[:, required_columns]
    data["Label"] = data["Label"].astype(str).str.strip()

    logger.info("Dropping rows with missing feature values")
    data = data.dropna(subset=config.FEATURE_COLUMNS)

    logger.info("Replacing infinite values and dropping NaNs")
    data = data.replace([float("inf"), float("-inf")], pd.NA)
    data = data.dropna(subset=config.FEATURE_COLUMNS)

    logger.info("Dropping duplicate rows based on feature columns")
    data = data.drop_duplicates(subset=config.FEATURE_COLUMNS)

    logger.info("Cleaned labeled data. Rows: %d, Columns: %d", data.shape[0], data.shape[1])
    return data


def _align_labels(features: pd.DataFrame, labeled: pd.DataFrame) -> pd.DataFrame:
    logger.info("Aligning labels to processed features")
    merged = features.merge(
        labeled,
        on=list(config.FEATURE_COLUMNS),
        how="left",
        validate="one_to_one",
    )

    missing_labels = merged["Label"].isna().sum()
    if missing_labels:
        raise ValueError(f"Failed to align {missing_labels} labels to processed features.")

    return merged


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
    features = feature_extraction.load_and_clean_data()

    logger.info("Loading raw data with labels")
    labeled_raw = _load_raw_with_labels()
    labeled = _align_labels(features, labeled_raw)

    logger.info("Selecting feature columns")
    X_full = features.loc[:, config.FEATURE_COLUMNS]

    logger.info("Balancing dataset by undersampling benign traffic (10:1 benign:attack)")
    true_anomaly = labeled["Label"] != "BENIGN"
    attacks = labeled.loc[true_anomaly]
    benign = labeled.loc[~true_anomaly]

    if attacks.empty:
        raise ValueError("No attack rows found; cannot balance training data.")

    target_benign = len(attacks) * 10
    if len(benign) >= target_benign:
        benign_sample = benign.sample(
            n=target_benign, random_state=config.IF_RANDOM_STATE
        )
    else:
        logger.warning(
            "Benign rows (%d) fewer than target (%d); using all benign rows.",
            len(benign),
            target_benign,
        )
        benign_sample = benign

    balanced = pd.concat([attacks, benign_sample], ignore_index=True)
    X_train = balanced.loc[:, config.FEATURE_COLUMNS]

    logger.info("Training Isolation Forest model")
    model = anomaly_detection.train_model(X_train)

    logger.info("Training second-level Random Forest")
    X_rf = labeled.loc[:, config.FEATURE_COLUMNS]
    y_rf = (labeled["Label"] != "BENIGN").astype(int)
    semi_supervised.train_second_level(X_rf, y_rf)
    logger.info("Second-level Random Forest trained and saved.")

    logger.info("Scoring full dataset")
    scores = anomaly_detection.get_anomaly_score(model, X_full)

    mean_score = float(scores.mean())
    min_score = float(scores.min())
    max_score = float(scores.max())
    pct_anomalies = float((scores < config.T_BASE).mean() * 100.0)

    print(f"Mean score: {mean_score:.4f}")
    print(f"Min score: {min_score:.4f}")
    print(f"Max score: {max_score:.4f}")
    print(f"Percent flagged (< {config.T_BASE:.2f}): {pct_anomalies:.2f}%")

    _save_sample_with_scores(X_full, pd.Series(scores, index=X_full.index))


if __name__ == "__main__":
    main()
