"""Risk score computation for IDS/IPS decisions."""

from __future__ import annotations

import sys

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402


class RiskEngine:
    """Compute final risk score and level from anomaly, stability, and load inputs."""

    def compute_risk(
        self, anomaly_score: float, stability_score: float, network_load: float
    ) -> dict:
        """Return a dict with normalized anomaly, risk score, and risk level."""

        A_norm = 1.0 - anomaly_score
        risk_score = (
            (config.W_ANOMALY * A_norm)
            + (config.W_STABILITY * stability_score)
            + (config.W_LOAD * (1 - network_load))
        )

        risk_score = max(0.0, min(1.0, risk_score))

        if risk_score < config.RISK_LOW:
            risk_level = "LOW"
        elif risk_score < config.RISK_MEDIUM:
            risk_level = "MEDIUM"
        elif risk_score < config.RISK_HIGH:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return {
            "A_norm": round(A_norm, 4),
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
        }
