"""Evaluate the trained Isolation Forest model against CIC-IDS-2017 labels."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402
from ml_engine import anomaly_detection, feature_extraction  # noqa: E402

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
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna(subset=config.FEATURE_COLUMNS)

    logger.info("Dropping duplicate rows based on feature columns")
    data = data.drop_duplicates(subset=config.FEATURE_COLUMNS)

    logger.info("Cleaned labeled data. Rows: %d, Columns: %d", data.shape[0], data.shape[1])
    return data


def _align_labels(
    features: pd.DataFrame, labeled: pd.DataFrame
) -> pd.DataFrame:
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


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _compute_metrics(
    predicted_anomaly: np.ndarray, true_anomaly: np.ndarray
) -> dict[str, float]:
    tp = int((predicted_anomaly & true_anomaly).sum())
    tn = int((~predicted_anomaly & ~true_anomaly).sum())
    fp = int((predicted_anomaly & ~true_anomaly).sum())
    fn = int((~predicted_anomaly & true_anomaly).sum())

    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1_score = _safe_div(2 * precision * recall, precision + recall)
    false_positive_rate = _safe_div(fp, fp + tn)
    accuracy = _safe_div(tp + tn, len(true_anomaly))

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "false_positive_rate": false_positive_rate,
        "accuracy": accuracy,
    }


def _save_evaluation_summary(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved evaluation summary to %s", path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    logger.info("Loading processed feature set")
    features = feature_extraction.load_processed_data()

    logger.info("Loading raw data with labels")
    labeled_raw = _load_raw_with_labels()

    labeled = _align_labels(features, labeled_raw)

    logger.info("Loading trained Isolation Forest model")
    model = anomaly_detection.load_model()

    logger.info("Scoring data")
    scores = anomaly_detection.get_anomaly_score(model, features)
    predicted_anomaly = scores < config.T_BASE

    true_anomaly = labeled["Label"] != "BENIGN"

    base_metrics = _compute_metrics(predicted_anomaly, true_anomaly.to_numpy())

    total_flows = int(len(labeled))
    total_attacks = int(true_anomaly.sum())
    total_benign = int((~true_anomaly).sum())

    print(f"Total flows: {total_flows}")
    print(f"Total real attacks: {total_attacks}")
    print(f"Total real benign: {total_benign}")
    print(f"TP: {base_metrics['tp']}")
    print(f"TN: {base_metrics['tn']}")
    print(f"FP: {base_metrics['fp']}")
    print(f"FN: {base_metrics['fn']}")
    print(f"Precision: {base_metrics['precision']:.4f}")
    print(f"Recall: {base_metrics['recall']:.4f}")
    print(f"F1 Score: {base_metrics['f1_score']:.4f}")
    print(f"False Positive Rate: {base_metrics['false_positive_rate']:.4f}")
    print(f"Accuracy: {base_metrics['accuracy']:.4f}")

    print("Threshold sweep:")
    best_threshold = None
    best_metrics = None
    for threshold in config.EVAL_THRESHOLDS:
        sweep_predicted = scores < threshold
        sweep_metrics = _compute_metrics(sweep_predicted, true_anomaly.to_numpy())
        print(
            f"T={threshold:.2f} "
            f"F1={sweep_metrics['f1_score']:.4f} "
            f"P={sweep_metrics['precision']:.4f} "
            f"R={sweep_metrics['recall']:.4f} "
            f"FPR={sweep_metrics['false_positive_rate']:.4f} "
            f"ACC={sweep_metrics['accuracy']:.4f}"
        )
        if best_metrics is None or sweep_metrics["f1_score"] > best_metrics["f1_score"]:
            best_metrics = sweep_metrics
            best_threshold = threshold

    if best_metrics is not None:
        print(
            "Best threshold by F1: "
            f"T={best_threshold:.2f} "
            f"F1={best_metrics['f1_score']:.4f} "
            f"P={best_metrics['precision']:.4f} "
            f"R={best_metrics['recall']:.4f}"
        )
        print(f"Recommended T_BASE (best F1): {best_threshold:.2f}")

    attack_counts = labeled.loc[labeled["Label"] != "BENIGN", "Label"].value_counts()
    print("Top 10 attack types:")
    for label, count in attack_counts.head(10).items():
        print(f"{label}: {count}")

    summary_lines = [
        "Confusion Matrix Summary",
        f"Total flows: {total_flows}",
        f"Total real attacks: {total_attacks}",
        f"Total real benign: {total_benign}",
        f"TP: {base_metrics['tp']}",
        f"TN: {base_metrics['tn']}",
        f"FP: {base_metrics['fp']}",
        f"FN: {base_metrics['fn']}",
        f"Precision: {base_metrics['precision']:.4f}",
        f"Recall: {base_metrics['recall']:.4f}",
        f"F1 Score: {base_metrics['f1_score']:.4f}",
        f"False Positive Rate: {base_metrics['false_positive_rate']:.4f}",
        f"Accuracy: {base_metrics['accuracy']:.4f}",
    ]

    output_path = Path(config.DATA_PROCESSED_DIR) / "evaluation_results.txt"
    _save_evaluation_summary(output_path, summary_lines)


if __name__ == "__main__":
    main()
