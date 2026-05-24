"""Adaptive thresholding based on current network load."""

from __future__ import annotations

import logging
import sys

import pandas as pd

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402

logger = logging.getLogger(__name__)


class AdaptiveThresholdController:
    """Adjust anomaly detection thresholds based on network load."""

    def get_threshold(self, network_load: float) -> float:
        """Return threshold based on current network load in [0, 1]."""

        if network_load <= config.LOAD_LOW_MAX:
            return config.T_LOW_LOAD
        if network_load > config.LOAD_HIGH_MIN:
            return config.T_HIGH_LOAD
        return config.T_MEDIUM_LOAD

    def get_load_level(self, network_load: float) -> str:
        """Return 'LOW', 'MEDIUM', or 'HIGH' based on network load."""

        if network_load <= config.LOAD_LOW_MAX:
            return "LOW"
        if network_load > config.LOAD_HIGH_MIN:
            return "HIGH"
        return "MEDIUM"


def compute_network_load(df_window: pd.DataFrame) -> float:
    """
    Estimate current network load from a window of flow data.
    Returns 0.5 if "Flow Bytes/s" is unavailable or the dataframe is empty.
    """

    if df_window is None or df_window.empty:
        logger.warning("Empty dataframe window; using default load 0.5")
        return 0.5

    if "Flow Bytes/s" not in df_window.columns:
        logger.warning("Column 'Flow Bytes/s' not found; using default load 0.5")
        return 0.5

    mean_bytes_per_sec = df_window["Flow Bytes/s"].mean()
    load = min(mean_bytes_per_sec / 1_000_000, 1.0)
    return float(load)
