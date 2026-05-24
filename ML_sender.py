"""
ml_sender.py — Integration bridge between ML engine and Percepta backend API.

HOW IT WORKS:
  1. Loads the trained Isolation Forest model
  2. Receives a network flow (as a dict with raw feature columns)
  3. Runs the full ML pipeline: threshold → anomaly score → stability → risk → decision
  4. Sends the result as a POST request to FastAPI backend
  5. Returns the API response

USAGE (by Mirkomil):
  from ml_sender import MLSender

  sender = MLSender()

  # For a single flow (dict with raw CIC-IDS-2017 feature columns):
  flow = {
      "Flow Duration": 1200,
      "Total Fwd Packets": 20,
      "Total Backward Packets": 10,
      "Total Length of Fwd Packets": 8000,
      "Total Length of Bwd Packets": 4000,
      "Flow Bytes/s": 500000,
      "Flow Packets/s": 25,
      "Flow IAT Mean": 50,
      "Fwd IAT Mean": 60,
      "Bwd IAT Mean": 80,
      "Fwd PSH Flags": 0,
      "Bwd PSH Flags": 0,
      "Fwd URG Flags": 0,
      "Bwd URG Flags": 0,
      "FIN Flag Count": 1,
      "SYN Flag Count": 1,
      "RST Flag Count": 0,
      "PSH Flag Count": 0,
      "ACK Flag Count": 1,
      "URG Flag Count": 0,
      "Fwd Packet Length Max": 400,
      "Bwd Packet Length Max": 400,
      "Fwd Packet Length Mean": 200,
      "Bwd Packet Length Mean": 200,
      "Packet Length Mean": 200,
      "Packet Length Std": 50,
      "Average Packet Size": 200,
      "Avg Fwd Segment Size": 200,
      "Avg Bwd Segment Size": 200,
      # Optional network metadata (not used by ML, but sent to API):
      "source_ip": "192.168.1.15",       # optional, default: "0.0.0.0"
      "destination_ip": "10.0.0.5",      # optional
      "protocol": "TCP",                  # optional
      "destination_port": 443,            # optional
  }

  response = sender.process_and_send(flow)
  print(response)
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import requests

# ── make sure project root is in path ────────────────────────────────────────
if "" not in sys.path:
    sys.path.insert(0, "")

import config  # noqa: E402
from ml_engine.anomaly_detection import load_model, get_anomaly_score, flag_anomalies
from ml_engine.threshold_controller import AdaptiveThresholdController, compute_network_load
from ml_engine.stability_module import TemporalStabilityModule
from ml_engine.risk_engine import RiskEngine
from ml_engine.decision_engine import DecisionEngine

# ─────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# Backend API URL — change to 0.0.0.0 or server IP for network deployment
API_BASE_URL = "http://127.0.0.1:8000"
API_EVENTS_ENDPOINT = f"{API_BASE_URL}/api/events/"

# Optional metadata columns that may be present in the flow dict
# They are extracted and sent to API, but NOT passed to the ML model
METADATA_COLUMNS = {"source_ip", "destination_ip", "protocol", "destination_port"}


class MLSender:
    """
    Full pipeline: raw flow → ML inference → API POST.

    One instance is meant to be reused across many flows so that the
    TemporalStabilityModule accumulates state correctly over time.
    """

    def __init__(self, api_url: str = API_EVENTS_ENDPOINT) -> None:
        self.api_url = api_url

        logger.info("Loading Isolation Forest model from %s", config.MODEL_PATH)
        self.model = load_model()

        self.threshold_ctrl = AdaptiveThresholdController()
        self.stability_module = TemporalStabilityModule(window_size=config.WINDOW_SIZE)
        self.risk_engine = RiskEngine()
        self.decision_engine = DecisionEngine()

        logger.info("MLSender ready.")

    # ── public API ──────────────────────────────────────────────────────────

    def process_and_send(self, flow: dict) -> dict:
        """
        Run the full pipeline for one network flow and POST result to backend.

        Args:
            flow: dict with CIC-IDS-2017 feature columns (+ optional metadata).

        Returns:
            dict with keys:
              "event_payload"  — the JSON body sent to the API
              "api_status"     — HTTP status code (or None on connection error)
              "api_response"   — parsed JSON from API (or error string)
        """

        # 1. Separate metadata from ML features
        metadata = {k: flow.get(k) for k in METADATA_COLUMNS}
        feature_row = {k: v for k, v in flow.items() if k not in METADATA_COLUMNS}

        # 2. Build DataFrame for ML pipeline
        X = pd.DataFrame([feature_row])

        # Keep only known feature columns (fill missing with 0)
        for col in config.FEATURE_COLUMNS:
            if col not in X.columns:
                logger.warning("Missing feature column '%s' — filling with 0", col)
                X[col] = 0.0
        X = X[config.FEATURE_COLUMNS].astype(float)

        # 3. Compute network load from this single flow window
        network_load = compute_network_load(X)

        # 4. Adaptive threshold based on load
        adaptive_threshold = self.threshold_ctrl.get_threshold(network_load)

        # 5. Anomaly score from Isolation Forest (normalized 0–1)
        scores = get_anomaly_score(self.model, X)
        anomaly_score = float(scores[0])

        # 6. Flag as anomaly
        is_anomaly = bool(flag_anomalies(scores, threshold=adaptive_threshold)[0])

        # 7. Update temporal stability window
        now_ts = time.time()
        self.stability_module.update(timestamp=now_ts, is_anomaly=is_anomaly)
        stability_data = self.stability_module.compute_stability_score()

        stability_score = stability_data["stability_score"]
        anomaly_count_window = stability_data["count"]
        max_consecutive_anomalies = stability_data["max_consecutive"]
        frequency_window = stability_data["frequency"]

        # 8. Risk engine
        risk_data = self.risk_engine.compute_risk(
            anomaly_score=anomaly_score,
            stability_score=stability_score,
            network_load=network_load,
        )
        risk_score = risk_data["risk_score"]
        risk_level = risk_data["risk_level"]

        # 9. Decision engine
        decision = self.decision_engine.decide(
            risk_level=risk_level, network_load=network_load
        )
        action_taken = decision["action"]
        action_duration_seconds = decision["block_seconds"]

        # 10. Compute block expiry time (only for TEMP_BLOCK)
        block_expires_at: Optional[str] = None
        if action_taken == "TEMP_BLOCK" and action_duration_seconds > 0:
            expiry_dt = datetime.fromtimestamp(
                now_ts + action_duration_seconds, tz=timezone.utc
            )
            block_expires_at = expiry_dt.isoformat()

        # 11. Build event payload matching API contract
        event_id = f"evt_{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        timestamp = datetime.fromtimestamp(now_ts, tz=timezone.utc).isoformat()

        # Extract optional network metadata
        source_ip = metadata.get("source_ip") or "0.0.0.0"
        destination_ip = metadata.get("destination_ip")
        protocol = metadata.get("protocol")
        destination_port = metadata.get("destination_port")

        # Try to extract flow characteristics from the raw feature row
        flow_duration_ms = _safe_int(feature_row.get("Flow Duration"))
        total_packets = _safe_int(
            (feature_row.get("Total Fwd Packets") or 0)
            + (feature_row.get("Total Backward Packets") or 0)
        )
        total_bytes = _safe_int(
            (feature_row.get("Total Length of Fwd Packets") or 0)
            + (feature_row.get("Total Length of Bwd Packets") or 0)
        )

        event_payload = {
            "event_id": event_id,
            "timestamp": timestamp,
            # Network
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "protocol": protocol,
            "destination_port": destination_port,
            # Flow
            "flow_duration_ms": flow_duration_ms,
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            # ML
            "anomaly_score": round(anomaly_score, 6),
            "adaptive_threshold": round(adaptive_threshold, 4),
            "is_anomaly": is_anomaly,
            # Temporal stability
            "anomaly_count_window": anomaly_count_window,
            "max_consecutive_anomalies": max_consecutive_anomalies,
            "frequency_window": round(frequency_window, 4),
            "stability_score": round(stability_score, 4),
            # Context & risk
            "network_load": round(network_load, 4),
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            # IPS
            "action_taken": action_taken,
            "action_duration_seconds": action_duration_seconds if action_duration_seconds > 0 else None,
            "block_expires_at": block_expires_at,
            # System
            "system_mode": "ADAPTIVE",
            "model_version": "IF_v1.0",
        }

        # 12. Send to backend
        api_status, api_response = self._post_event(event_payload)

        result = {
            "event_payload": event_payload,
            "api_status": api_status,
            "api_response": api_response,
        }

        self._log_result(event_payload, api_status)
        return result

    # ── internal ─────────────────────────────────────────────────────────────

    def _post_event(self, payload: dict):
        try:
            resp = requests.post(self.api_url, json=payload, timeout=5)
            try:
                return resp.status_code, resp.json()
            except Exception:
                return resp.status_code, resp.text
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to backend at %s — is FastAPI running?", self.api_url)
            return None, "ConnectionError: backend not reachable"
        except requests.exceptions.Timeout:
            logger.error("Request to backend timed out.")
            return None, "TimeoutError"

    def _log_result(self, payload: dict, status: Optional[int]) -> None:
        icon = "✅" if status in (200, 201) else "❌"
        logger.info(
            "%s [%s] %s | risk=%s | action=%s | score=%.4f | stability=%.4f",
            icon,
            status,
            payload["source_ip"],
            payload["risk_level"],
            payload["action_taken"],
            payload["anomaly_score"],
            payload["stability_score"],
        )


# ── helpers ───────────────────────────────────────────────────────────────────

def _safe_int(value) -> Optional[int]:
    try:
        v = float(value)
        if np.isnan(v) or np.isinf(v):
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


# ── standalone test / demo ────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print("\n" + "=" * 60)
    print("  MLSender — integration test")
    print("=" * 60)
    print("Make sure FastAPI backend is running:")
    print("  cd percepta_backend && uvicorn main:app --reload --port 8000")
    print("=" * 60 + "\n")

    # Example flow — replace with real Scapy-captured data
    test_flow = {
        # ML features
        "Flow Duration": 1200,
        "Total Fwd Packets": 20,
        "Total Backward Packets": 10,
        "Total Length of Fwd Packets": 8000,
        "Total Length of Bwd Packets": 4000,
        "Flow Bytes/s": 500000.0,
        "Flow Packets/s": 25.0,
        "Flow IAT Mean": 50.0,
        "Fwd IAT Mean": 60.0,
        "Bwd IAT Mean": 80.0,
        "Fwd PSH Flags": 0,
        "Bwd PSH Flags": 0,
        "Fwd URG Flags": 0,
        "Bwd URG Flags": 0,
        "FIN Flag Count": 1,
        "SYN Flag Count": 1,
        "RST Flag Count": 0,
        "PSH Flag Count": 0,
        "ACK Flag Count": 1,
        "URG Flag Count": 0,
        "Fwd Packet Length Max": 400.0,
        "Bwd Packet Length Max": 400.0,
        "Fwd Packet Length Mean": 200.0,
        "Bwd Packet Length Mean": 200.0,
        "Packet Length Mean": 200.0,
        "Packet Length Std": 50.0,
        "Average Packet Size": 200.0,
        "Avg Fwd Segment Size": 200.0,
        "Avg Bwd Segment Size": 200.0,
        # Optional metadata (not used by ML model)
        "source_ip": "192.168.1.15",
        "destination_ip": "10.0.0.5",
        "protocol": "TCP",
        "destination_port": 443,
    }

    sender = MLSender()
    result = sender.process_and_send(test_flow)

    print("\n── Event Payload sent to API ──")
    for k, v in result["event_payload"].items():
        print(f"  {k}: {v}")

    print(f"\n── API Response ──")
    print(f"  Status:   {result['api_status']}")
    print(f"  Response: {result['api_response']}")