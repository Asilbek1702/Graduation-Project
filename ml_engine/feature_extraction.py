"""Feature extraction and cleaning for CIC-IDS-2017 IDS/IPS pipeline."""

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

logger = logging.getLogger(__name__)


def _csv_files(data_dir: str | Path) -> List[Path]:
    data_path = Path(data_dir)
    files = sorted(data_path.glob("*.csv"))
    return files


def load_and_clean_data() -> pd.DataFrame:
    """
    Load all raw CSVs, clean feature columns, save parquet, and return dataframe.
    """

    csv_files = _csv_files(config.DATA_RAW_DIR)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {config.DATA_RAW_DIR}")

    logger.info("Loading %d CSV files from %s", len(csv_files), config.DATA_RAW_DIR)

    frames: List[pd.DataFrame] = []
    for csv_path in csv_files:
        logger.info("Reading %s", csv_path)
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        frames.append(df)

    data = pd.concat(frames, ignore_index=True)

    logger.info("Filtering to feature columns (%d)", len(config.FEATURE_COLUMNS))
    data = data.loc[:, config.FEATURE_COLUMNS]

    logger.info("Dropping rows with missing feature values")
    data = data.dropna(subset=config.FEATURE_COLUMNS)

    logger.info("Replacing infinite values and dropping NaNs")
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna(subset=config.FEATURE_COLUMNS)

    logger.info("Dropping duplicate rows")
    data = data.drop_duplicates()

    processed_dir = Path(config.DATA_PROCESSED_DIR)
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "features.parquet"

    logger.info("Saving cleaned data to %s", output_path)
    data.to_parquet(output_path, index=False)

    logger.info("Completed cleaning. Rows: %d, Columns: %d", data.shape[0], data.shape[1])
    return data


def load_processed_data() -> pd.DataFrame:
    """
    Load the processed parquet data and return a dataframe.
    """

    processed_path = Path(config.DATA_PROCESSED_DIR) / "features.parquet"
    if not processed_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_path}")

    logger.info("Loading processed data from %s", processed_path)
    return pd.read_parquet(processed_path)
