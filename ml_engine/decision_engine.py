"""Decision engine for mapping risk levels to IPS actions."""

from __future__ import annotations

import sys

if "" not in sys.path:
    sys.path.append("")

import config  # noqa: E402


class DecisionEngine:
    """Map risk levels to IPS actions and escalation durations."""

    def decide(self, risk_level: str, network_load: float = 0.5) -> dict:
        """Return action, block duration, and description for a risk level."""

        if risk_level == "LOW":
            action = "LOG"
            block_seconds = 0
            description = "Logging only, likely noise"
        elif risk_level == "MEDIUM":
            action = "MONITOR"
            block_seconds = 0
            description = "Increased monitoring, no block"
        elif risk_level == "HIGH":
            action = "RATE_LIMIT"
            block_seconds = config.RATE_LIMIT_DURATION
            description = "Rate limiting applied"
        else:
            action = "TEMP_BLOCK"
            block_seconds = config.BLOCK_DURATION
            description = "Temporary IP block applied"

        return {
            "action": action,
            "block_seconds": block_seconds,
            "description": description,
        }

    def escalate(self, strike_count: int) -> int:
        """Return block duration based on repeated CRITICAL strikes."""

        if strike_count <= 1:
            return config.BLOCK_DURATION
        if strike_count == 2:
            return config.BLOCK_ESCALATION_2X
        return config.BLOCK_ESCALATION_3X
