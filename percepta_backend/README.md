# Percepta Backend — Setup Guide

## Structure

```
percepta_backend/
├── main.py              ← FastAPI entry point
├── requirements.txt
├── .env.example         ← copy to .env and set your DB URL
└── api/
    ├── database.py      ← PostgreSQL connection
    ├── models.py        ← DB tables: Event, BlockedIP
    ├── schemas.py       ← Pydantic schemas (API contract)
    ├── crud.py          ← DB query functions
    └── routes/
        ├── events.py    ← POST/GET /api/events
        ├── stats.py     ← GET /api/stats
        ├── blocked.py   ← GET /api/blocked, POST /api/unblock/{ip}
        └── ip.py        ← GET /api/ip/{ip}
```

## 1. PostgreSQL setup

```sql
CREATE DATABASE percepta_db;
CREATE USER percepta_user WITH PASSWORD 'percepta_pass';
GRANT ALL PRIVILEGES ON DATABASE percepta_db TO percepta_user;
```

## 2. Environment

```bash
cp .env.example .env
# Edit .env with your actual DB credentials
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Run the server

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 5. API Docs (auto-generated)

Open in browser: http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/events/` | Create new event (from ML engine) |
| GET | `/api/events/` | Get latest events (filters: limit, risk_level, source_ip) |
| GET | `/api/events/{event_id}` | Get single event details |
| GET | `/api/stats/` | Dashboard overview stats |
| GET | `/api/blocked` | List all blocked IPs |
| POST | `/api/unblock/{ip}` | Admin: unblock an IP |
| GET | `/api/ip/{ip_address}` | Check IP block status |

## Example: Send an event (test with curl)

```bash
curl -X POST http://127.0.0.1:8000/api/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_20260212_001245",
    "timestamp": "2026-02-12T14:05:10Z",
    "source_ip": "192.168.1.15",
    "destination_ip": "10.0.0.5",
    "protocol": "TCP",
    "destination_port": 443,
    "flow_duration_ms": 1200,
    "total_packets": 45,
    "total_bytes": 18200,
    "anomaly_score": 0.22,
    "adaptive_threshold": 0.68,
    "is_anomaly": true,
    "anomaly_count_window": 6,
    "max_consecutive_anomalies": 4,
    "frequency_window": 0.20,
    "stability_score": 0.74,
    "network_load": 0.80,
    "risk_score": 0.65,
    "risk_level": "HIGH",
    "action_taken": "RATE_LIMIT",
    "action_duration_seconds": 60,
    "system_mode": "ADAPTIVE",
    "model_version": "IF_v1.0"
  }'
```
