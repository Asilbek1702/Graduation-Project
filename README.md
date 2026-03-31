# Percepta — Web Platform & Backend

**Developer:** Asilbek Tashpulatov  
**Stack:** FastAPI · PostgreSQL · React · Vite

> Part of the university graduate project:  
> *Anomaly Detection and Intrusion Prevention in University Networks via Isolation Forest–Based IDS/IPS*

---

## Overview

This repository contains the **web platform and backend API** for the Percepta IDS/IPS system.

The backend is the central hub of the system — the ML engine sends events to it, and the React dashboard reads from it. It is the only component that communicates directly with the PostgreSQL database.

```
ML Engine  →  POST /api/events/  →  FastAPI Backend  →  PostgreSQL
React      →  GET  /api/events/  →  FastAPI Backend  →  PostgreSQL
```

---

## Tech Stack

| Layer     | Technology      | Purpose                                                    |
|-----------|-----------------|------------------------------------------------------------|
| Backend   | FastAPI         | REST API framework — fast, automatic /docs generation      |
| Backend   | SQLAlchemy      | ORM — Python classes map to PostgreSQL tables              |
| Backend   | Pydantic v2     | Request/response validation — rejects bad data before DB   |
| Backend   | Uvicorn         | ASGI server that runs the FastAPI app                      |
| Database  | PostgreSQL      | Main production database                                   |
| Frontend  | React + Vite    | Component-based UI, fast dev server                        |
| Frontend  | React Router    | Client-side page navigation                                |
| Frontend  | Fetch API       | Built-in browser HTTP calls — no extra libraries needed    |
| Export    | openpyxl        | Generates .xlsx Excel files for the Export Today button    |

---

## Project Structure

### Backend — `percepta_backend/`

```
percepta_backend/
├── main.py                    # App entry point — CORS, table creation, router registration
├── requirements.txt
├── .env                       # Database URL (not committed to GitHub)
├── migrate_sessions.py        # One-time script to populate user_sessions from existing events
└── api/
    ├── __init__.py
    ├── database.py            # PostgreSQL connection and session factory
    ├── models.py              # SQLAlchemy ORM — defines all 3 tables
    ├── schemas.py             # Pydantic validation schemas (in/out)
    ├── crud.py                # All database read/write logic
    └── routes/
        ├── __init__.py
        ├── events.py          # GET/POST /api/events/
        ├── stats.py           # GET /api/stats/ and /api/stats/chart-data
        ├── blocked.py         # GET /api/blocked, POST /api/block, POST /api/unblock
        ├── ip.py              # GET /api/ip/{ip}
        └── sessions.py        # GET /api/sessions/, GET /api/sessions/export
```

### Frontend — `percepta-frontend/`

```
percepta-frontend/
├── index.html
├── vite.config.js             # host: 127.0.0.1, port: 5173
├── package.json
└── src/
    ├── main.jsx               # React entry point
    ├── App.jsx                # Routes + AuthProvider + ToastProvider
    ├── index.css              # CSS variables and global styles
    ├── api/
    │   └── index.js           # All fetch() calls to the backend (single source of truth)
    ├── hooks/
    │   ├── useAuth.jsx        # Login / logout / sessionStorage
    │   └── useToast.jsx       # Toast notifications
    ├── components/
    │   ├── Layout.jsx         # Sidebar + topbar shell (wraps all pages)
    │   └── EventModal.jsx     # Event detail popup + Block IP button
    └── pages/
        ├── LoginPage.jsx
        ├── DashboardPage.jsx  # Stat cards, chart, recent events, protocol mix
        ├── EventsPage.jsx     # Events table with search, filter, sort
        ├── BlockedPage.jsx    # Blocked IPs management
        └── LogsPage.jsx       # Session log table + Export Today (.xlsx)
```

---

## Backend — File Descriptions

### `main.py`
Entry point for the FastAPI application. On startup it:
- Runs `Base.metadata.create_all()` — creates all PostgreSQL tables if they don't exist yet
- Adds CORS middleware so the React app at `localhost:5173` can call the API
- Registers all 5 routers: events, stats, blocked, ip, sessions

### `api/database.py`
Manages the PostgreSQL connection. Reads `DATABASE_URL` from the `.env` file.  
The `get_db()` function is a FastAPI dependency — it opens a session at the start of each request and closes it automatically when done, even if an error occurred.

### `api/models.py`
Defines 3 database tables as SQLAlchemy Python classes:

| Table           | Rows represent                          | Key columns                                                        |
|-----------------|-----------------------------------------|--------------------------------------------------------------------|
| `events`        | Every event from the ML engine          | source_ip, anomaly_score, risk_level, action_taken, timestamp      |
| `blocked_ips`   | Currently blocked IP addresses          | ip_address, strike_count, block_expires_at, is_active              |
| `user_sessions` | One network session per IP per day      | ip_address, session_date, login_time, logout_time, traffic_bytes   |

Tables are created automatically on first backend startup — no manual SQL needed.

### `api/schemas.py`
Pydantic v2 schemas define what data is allowed in and out of each endpoint. If the ML engine sends a wrong field type (e.g. a string where a float is expected), FastAPI returns HTTP 422 automatically — no extra validation code needed in the routes.

| Schema                | Used for                                                           |
|-----------------------|--------------------------------------------------------------------|
| `EventCreate`         | Validating incoming POST /api/events/ from ML engine (25 fields)  |
| `EventResponse`       | Formatting outgoing event data to the frontend                     |
| `BlockedIPResponse`   | Blocked IP rows for the Blocked IPs page                          |
| `IPStatusResponse`    | Single IP block status check                                       |
| `StatsResponse`       | Dashboard stat cards                                               |
| `UserSessionResponse` | Session rows for the Logs page                                     |

### `api/crud.py`
All database read/write logic. Routes never touch the database directly — they always call a function from `crud.py`. Key functions:

- `create_event()` — saves a new event, then automatically calls `_upsert_blocked_ip()` if action is `TEMP_BLOCK` and `_upsert_user_session()` to update the sessions table
- `get_stats()` — runs COUNT, AVG, GROUP BY queries to compute dashboard card data
- `_upsert_user_session()` — creates a new session row for a new IP, or updates `logout_time` and adds traffic bytes for a returning IP on the same day
- `_upsert_blocked_ip()` — creates or updates a `blocked_ips` row, increments `strike_count` on repeated blocks

### `api/routes/events.py`
- `POST /api/events/` — ML engine sends one event here after analyzing a flow
- `GET /api/events/` — frontend reads events for the Events page (params: `limit`, `risk_level`, `source_ip`)

### `api/routes/stats.py`
- `GET /api/stats/` — aggregated numbers for dashboard cards: total flows, anomalies, risk distribution, blocked IPs, average network load
- `GET /api/stats/chart-data?period=24h` — time-bucketed data for the chart. For `24h`: 12 buckets of 2 hours each, labeled `00/02/04.../22`. For `7d`: 7 daily buckets. Each bucket has unique IP count and TEMP_BLOCK count.

### `api/routes/blocked.py`
- `GET /api/blocked` — all IPs where `is_active = True`
- `POST /api/block/{ip}` — admin manually blocks an IP for 120 seconds
- `POST /api/unblock/{ip}` — sets `is_active = False`

### `api/routes/sessions.py`
Serves the Logs page. For each session, looks up the first event from that IP on that day and attaches its `event_id` — so the Event ID column in Logs matches exactly what is shown on the Events page.

- `GET /api/sessions/` — all sessions, newest first
- `GET /api/sessions/export` — streams an `.xlsx` file with today's sessions including columns: Event ID, IP Address, Login Time, Logout Time, Duration, Traffic Used, Destination, Anomaly Score, Stability Score, Network Load, Risk Level

---

## API Reference

Base URL: `http://127.0.0.1:8000`  
Interactive docs: `http://127.0.0.1:8000/docs`

| Method | Endpoint                      | Caller          | Description                                      |
|--------|-------------------------------|-----------------|--------------------------------------------------|
| GET    | `/`                           | Anyone          | Health check                                     |
| POST   | `/api/events/`                | ML engine       | Receive and store a new network event            |
| GET    | `/api/events/`                | React           | List events (limit, risk_level, source_ip)       |
| GET    | `/api/events/{event_id}`      | React           | Get one event by ID                              |
| GET    | `/api/stats/`                 | React           | Dashboard stat card data                         |
| GET    | `/api/stats/chart-data`       | React           | Time-series chart data (period=24h or 7d)        |
| GET    | `/api/blocked`                | React           | List active blocked IPs                          |
| POST   | `/api/block/{ip}`             | React (admin)   | Manually block an IP for 120 seconds             |
| POST   | `/api/unblock/{ip}`           | React (admin)   | Unblock an IP                                    |
| GET    | `/api/ip/{ip}`                | React           | Check block status of one IP                     |
| GET    | `/api/sessions/`              | React           | List user sessions                               |
| GET    | `/api/sessions/today`         | React           | Sessions for today only                          |
| GET    | `/api/sessions/export`        | React (admin)   | Download today's sessions as .xlsx               |

---

## Database

```
Database: percepta_db
User:     percepta_user
Password: percepta_pass
Host:     localhost
Port:     5432
```

The `.env` file inside `percepta_backend/` must contain:

```env
DATABASE_URL=postgresql://percepta_user:percepta_pass@localhost:5432/percepta_db
```

---

## Frontend — Page Descriptions

| Page        | File                  | Description                                                                 | Auto-refresh |
|-------------|-----------------------|-----------------------------------------------------------------------------|--------------|
| Dashboard   | `DashboardPage.jsx`   | Stat cards (flows, blocked IPs, network load), time-series chart, recent events, protocol mix | Every 15s |
| Events      | `EventsPage.jsx`      | Full event table with search by IP/event ID, filter by risk/stability/time, sort. View button opens modal with all ML fields + Block IP button | Every 10s |
| Blocked IPs | `BlockedPage.jsx`     | Active blocked IPs with expiry time and strike count. Admin can unblock manually. Count syncs with dashboard | Every 10s |
| Logs        | `LogsPage.jsx`        | Session log — one row per IP per day. Event ID matches the Events page. Export Today downloads .xlsx | On load |

### `api/index.js`
Single file containing every API call the frontend makes. All `fetch()` calls go through a shared `request()` helper. To change the backend address, only this one file needs updating.

### `EventModal.jsx`
Popup showing all 12 ML fields for a selected event. Contains a **Block IP** button that calls `POST /api/block/{ip}`. If the IP is already blocked it shows **Already Blocked** (disabled).

---

## How to Run

### Requirements
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ running on `localhost:5432`

### 1. Install Python dependencies
```bash
cd percepta_backend
pip install -r requirements.txt
pip install openpyxl    # needed for Export Today button
```

### 2. Create `.env` file
Create `percepta_backend/.env`:
```env
DATABASE_URL=postgresql://percepta_user:percepta_pass@localhost:5432/percepta_db
```

### 3. Start the backend
```bash
cd percepta_backend
uvicorn main:app --reload --port 8000
```
Tables are created automatically on first run.  
API: `http://127.0.0.1:8000` | Docs: `http://127.0.0.1:8000/docs`

### 4. Start the frontend
```bash
cd percepta-frontend
npm install
npm run dev
```
Dashboard: `http://127.0.0.1:5173`

### 5. Populate Logs (one-time migration)
If the Logs page shows 0 sessions after the first run:
```bash
cd percepta_backend
python migrate_sessions.py
```
This reads all existing events and creates the corresponding session rows. Run once only.

---

## How It All Connects

```
Scapy (Muhammad)
    ↓ captures packets
ML Engine (Mirkomil)
    ↓ POST /api/events/  {anomaly_score, risk_level, action_taken, ...}
FastAPI Backend  ←→  PostgreSQL
    ↓ GET /api/stats/, /api/events/, /api/sessions/, ...
React Dashboard (Asilbek)
    ↓
Admin sees real-time network security data
```

The ML engine calls `POST /api/events/` after analyzing each flow. The backend validates, saves the event, and automatically updates `blocked_ips` and `user_sessions` tables if needed.

The React frontend never writes to the database directly — it only reads via GET requests and sends admin actions (block/unblock) via POST. The frontend has no knowledge of the ML engine; it only knows the backend API address.

---

*Percepta · Web Platform & Backend · Asilbek Tashpulatov · 2026*
