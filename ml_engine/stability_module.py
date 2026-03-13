"""Temporal stability analysis for anomaly sequences within a sliding window."""

from __future__ import annotations

from collections import deque
import sys
from typing import Deque, Tuple

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402


class TemporalStabilityModule:
    """Compute temporal stability metrics for anomaly scores over a sliding window."""

    def __init__(self, window_size: int = config.WINDOW_SIZE) -> None:
        self.window_size = window_size
        self.window: Deque[Tuple[float, bool]] = deque()

    def update(self, timestamp: float, is_anomaly: bool) -> None:
        """Add a new observation and evict entries older than the window size."""

        self.window.append((timestamp, is_anomaly))
        cutoff = timestamp - self.window_size
        while self.window and self.window[0][0] < cutoff:
            self.window.popleft()

    def compute_stability_score(self) -> dict:
        """Compute and return temporal stability metrics for the current window."""

        count = sum(1 for _, is_anomaly in self.window if is_anomaly)
        C = min(count / config.COUNT_CEILING, 1.0)

        freq = count / config.WINDOW_SIZE
        F = min(freq / config.FREQ_CEILING, 1.0)

        max_consecutive = 0
        current_streak = 0
        for _, is_anomaly in self.window:
            if is_anomaly:
                current_streak += 1
                if current_streak > max_consecutive:
                    max_consecutive = current_streak
            else:
                current_streak = 0

        D = min(max_consecutive / config.DURATION_CEILING, 1.0)

        stability_score = (
            config.W_COUNT * C + config.W_FREQ * F + config.W_DURATION * D
        )

        if stability_score < config.STABILITY_LOW:
            stability_level = "LOW"
        elif stability_score < config.STABILITY_MEDIUM:
            stability_level = "MEDIUM"
        elif stability_score < config.STABILITY_HIGH:
            stability_level = "HIGH"
        else:
            stability_level = "CRITICAL"

        return {
            "count": count,
            "frequency": round(freq, 4),
            "max_consecutive": max_consecutive,
            "C": round(C, 4),
            "F": round(F, 4),
            "D": round(D, 4),
            "stability_score": round(stability_score, 4),
            "stability_level": stability_level,
        }
