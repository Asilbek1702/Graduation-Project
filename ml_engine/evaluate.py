"""Evaluate the trained Isolation Forest model against CIC-IDS-2017 labels."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

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

    logger.info("Loading second-level Random Forest model")
    rf_model = semi_supervised.load_second_level()

    logger.info("Checking Random Forest overfitting (train vs test)")
    X_rf = labeled.loc[:, config.FEATURE_COLUMNS]
    y_rf = (labeled["Label"] != "BENIGN").astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X_rf,
        y_rf,
        test_size=0.20,
        random_state=config.IF_RANDOM_STATE,
        stratify=y_rf,
    )

    rf_train_pred = rf_model.predict(X_train)
    rf_test_pred = rf_model.predict(X_test)

    rf_train_metrics = _compute_metrics(
        rf_train_pred.astype(bool), y_train.to_numpy().astype(bool)
    )
    rf_test_metrics = _compute_metrics(
        rf_test_pred.astype(bool), y_test.to_numpy().astype(bool)
    )

    print("Random Forest only (train split):")
    print(f"Precision: {rf_train_metrics['precision']:.4f}")
    print(f"Recall: {rf_train_metrics['recall']:.4f}")
    print(f"F1 Score: {rf_train_metrics['f1_score']:.4f}")
    print(f"Accuracy: {rf_train_metrics['accuracy']:.4f}")

    print("Random Forest only (test split):")
    print(f"Precision: {rf_test_metrics['precision']:.4f}")
    print(f"Recall: {rf_test_metrics['recall']:.4f}")
    print(f"F1 Score: {rf_test_metrics['f1_score']:.4f}")
    print(f"Accuracy: {rf_test_metrics['accuracy']:.4f}")

    f1_gap = rf_train_metrics["f1_score"] - rf_test_metrics["f1_score"]
    if f1_gap > 0.05:
        print("WARNING: Possible overfitting detected (train/test F1 gap > 0.05)")

    logger.info("Scoring data")
    scores = anomaly_detection.get_anomaly_score(model, features)
    X_features = features.loc[:, config.FEATURE_COLUMNS]
    if_flags = scores < config.T_BASE
    rf_proba = rf_model.predict_proba(X_features)[:, 1]
    predicted_anomaly = if_flags & (rf_proba >= config.RF_PROBA_THRESHOLD)

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

    print("RF probability threshold sweep:")
    sweep_thresholds = [0.30, 0.40, 0.50, 0.60, 0.70]
    for threshold in sweep_thresholds:
        sweep_predicted = if_flags & (rf_proba >= threshold)
        sweep_metrics = _compute_metrics(sweep_predicted, true_anomaly.to_numpy())
        print(
            f"P={sweep_metrics['precision']:.4f} "
            f"R={sweep_metrics['recall']:.4f} "
            f"F1={sweep_metrics['f1_score']:.4f} "
            f"FPR={sweep_metrics['false_positive_rate']:.4f} "
            f"RF_T={threshold:.2f}"
        )

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
    summary_lines.extend(
        [
            "",
            "Random Forest Overfitting Check",
            "--------------------------------",
            "Train split:",
            f"  Precision:  {rf_train_metrics['precision']:.4f}",
            f"  Recall:     {rf_train_metrics['recall']:.4f}",
            f"  F1 Score:   {rf_train_metrics['f1_score']:.4f}",
            f"  Accuracy:   {rf_train_metrics['accuracy']:.4f}",
            "",
            "Test split:",
            f"  Precision:  {rf_test_metrics['precision']:.4f}",
            f"  Recall:     {rf_test_metrics['recall']:.4f}",
            f"  F1 Score:   {rf_test_metrics['f1_score']:.4f}",
            f"  Accuracy:   {rf_test_metrics['accuracy']:.4f}",
            "",
            f"Train/Test F1 Gap: {f1_gap:.4f}",
            "Overfitting status: "
            + ("WARNING (gap > 0.05)" if f1_gap > 0.05 else "PASSED (gap <= 0.05)"),
        ]
    )

    output_path = Path(config.DATA_PROCESSED_DIR) / "evaluation_results.txt"
    _save_evaluation_summary(output_path, summary_lines)


if __name__ == "__main__":
    main()
