Percepta — Web Platform & Backend
Developer: Asilbek Tashpulatov
FastAPI Backend  •  PostgreSQL  •  React Dashboard

Overview
This document covers the web platform and backend API component of the Percepta IDS/IPS system. My responsibility is the FastAPI backend that stores network events from the ML engine, manages blocked IPs, and exposes a REST API — and the React dashboard that gives administrators a real-time view of network activity.
The backend acts as the central hub of the system: the ML engine sends events to it, and the React frontend reads from it. It is the only component that talks to the PostgreSQL database.

Tech Stack
Layer	Technology	Purpose
Backend	FastAPI	REST API framework — high performance, automatic /docs generation
Backend	SQLAlchemy	ORM — Python classes map to PostgreSQL tables
Backend	Pydantic v2	Request/response validation — rejects bad data before it hits the DB
Backend	Uvicorn	ASGI server that runs the FastAPI app
Database	PostgreSQL	Main production database
Database	SQLite	Optional local dev database (no setup needed)
Frontend	React + Vite	Component-based UI, fast dev server
Frontend	React Router	Client-side page navigation
Frontend	Fetch API	Built-in browser API for HTTP calls — no extra libraries
Export	openpyxl	Generates .xlsx Excel files for Export Today button


Folder Structure
percepta_backend/
percepta_backend/
├── main.py                    ← App entry point
├── requirements.txt
├── .env                       ← Database URL (not in GitHub)
├── migrate_sessions.py        ← One-time migration script
└── api/
    ├── __init__.py
    ├── database.py            ← PostgreSQL connection
    ├── models.py              ← Table definitions (ORM)
    ├── schemas.py             ← Pydantic validation schemas
    ├── crud.py                ← All database operations
    └── routes/
        ├── __init__.py
        ├── events.py          ← /api/events/
        ├── stats.py           ← /api/stats/
        ├── blocked.py         ← /api/blocked, /api/block, /api/unblock
        ├── ip.py              ← /api/ip/{ip}
        └── sessions.py        ← /api/sessions/

percepta-frontend/
percepta-frontend/
├── index.html
├── vite.config.js             ← host: 127.0.0.1, port: 5173
├── package.json
└── src/
    ├── main.jsx               ← React entry point
    ├── App.jsx                ← Routes + providers
    ├── index.css              ← CSS variables, global styles
    ├── api/
    │   └── index.js           ← All fetch() calls to backend
    ├── hooks/
    │   ├── useAuth.jsx        ← Login/logout/sessionStorage
    │   └── useToast.jsx       ← Toast notifications
    ├── components/
    │   ├── Layout.jsx         ← Sidebar + topbar
    │   └── EventModal.jsx     ← Event detail popup + Block IP
    └── pages/
        ├── LoginPage.jsx
        ├── DashboardPage.jsx  ← Charts + stat cards
        ├── EventsPage.jsx     ← Events table
        ├── BlockedPage.jsx    ← Blocked IPs
        └── LogsPage.jsx       ← Session log + Export Today


Backend — File by File
main.py
Entry point. Does three things on startup:
• Calls 
• Runs Base.metadata.create_all() — creates all tables in PostgreSQL if they don't exist yet
• Adds CORS middleware allowing the React app at localhost:5173 to call the API
• Registers all 5 routers: events, stats, blocked, ip, sessions

api/database.py
Manages the PostgreSQL connection. Reads DATABASE_URL from the .env file. The key function is get_db() — a FastAPI dependency that automatically opens a database session at the start of each request and closes it when the request is done, even if an error occurred.

api/models.py
Defines the three database tables as Python classes:
Table	Rows represent	Key columns
events	Every event received from the ML engine	source_ip, anomaly_score, risk_level, action_taken, timestamp
blocked_ips	Currently blocked IP addresses	ip_address, strike_count, block_expires_at, is_active
user_sessions	One network session per IP per day	ip_address, session_date, login_time, logout_time, traffic_bytes, status

Tables are created automatically by SQLAlchemy on first backend startup — no manual SQL needed.

api/schemas.py
Pydantic v2 schemas define what data is allowed in and out of each endpoint. If the ML engine sends a wrong field type (e.g. a string where a float is expected), FastAPI returns HTTP 422 automatically without any code in the route handler.
Schema	Used for
EventCreate	Validating incoming POST /api/events/ from ML engine (25 fields)
EventResponse	Formatting outgoing event data to the frontend
BlockedIPResponse	Blocked IP data sent to the Blocked IPs page
IPStatusResponse	Single IP block status check
StatsResponse	Dashboard stat cards (total flows, blocked IPs, network load, risk distribution)
UserSessionResponse	Session rows for the Logs page

api/crud.py
All database read/write logic. Routes never touch the database directly — they always call a function from crud.py. This keeps routes clean and makes the database logic easy to test.
Important functions:
• create_event() — saves a new event. Also automatically calls _upsert_blocked_ip() if action is TEMP_BLOCK, and _upsert_user_session() to update the sessions table
• get_stats() — runs COUNT, AVG, and GROUP BY queries to compute dashboard card data
• _upsert_user_session() — for a new IP on a new day: creates a session row. For a returning IP: updates logout_time and adds traffic bytes
• _upsert_blocked_ip() — creates or updates a blocked_ips row. Increments strike_count on repeated blocks

api/routes/events.py
Two endpoints:
• [object Object] — the ML engine sends one event here after analyzing a network flow. The body is validated by EventCreate schema and saved via crud.create_event().
• [object Object] — the frontend reads events for the Events page. Supports query params: limit, risk_level, source_ip. Always returns newest first.

api/routes/stats.py
Two endpoints:
• [object Object] — returns aggregated numbers for the dashboard stat cards: total flows, total anomalies, risk distribution (LOW/MEDIUM/HIGH/CRITICAL counts), active blocked IPs, and average network load.
• [object Object] — returns time-bucketed data for the chart. For 24h: 12 buckets of 2 hours each, labeled 00/02/04.../22. For 7d: 7 daily buckets. Each bucket has unique IP count and TEMP_BLOCK count.

api/routes/blocked.py
• [object Object] — returns all IPs where is_active = True, newest first.
• [object Object] — admin manually blocks an IP. Creates or updates a blocked_ips row with a 120-second expiry.
• [object Object] — sets is_active = False for the given IP.

api/routes/sessions.py
Serves the Logs page. The key detail: for each session row, the route looks up the first event from that IP on that day and attaches its event_id to the response. This makes the Event ID column in Logs match exactly what is shown on the Events page.
• [object Object] — all sessions, newest first. Optional session_date filter.
• [object Object] — streams an Excel file (.xlsx) with today's sessions. Columns: Event ID, IP Address, Login Time, Logout Time, Duration, Traffic Used, Destination, Anomaly Score, Stability Score, Network Load, Risk Level.


API Reference
Base URL: http://127.0.0.1:8000   |   Interactive docs: http://127.0.0.1:8000/docs

Method	Endpoint	Who calls it	What it does
GET	/	Anyone	Health check — returns system status
POST	/api/events/	ML engine	Receive and store a new network event
GET	/api/events/	React	List events (params: limit, risk_level, source_ip)
GET	/api/events/{event_id}	React	Get one event by ID
GET	/api/stats/	React	Dashboard stat card data
GET	/api/stats/chart-data	React	Time-series data for chart (period=24h or 7d)
GET	/api/blocked	React	List active blocked IPs
POST	/api/block/{ip}	React (admin)	Manually block an IP for 120 seconds
POST	/api/unblock/{ip}	React (admin)	Unblock an IP
GET	/api/ip/{ip}	React	Check block status of one IP
GET	/api/sessions/	React	List user sessions
GET	/api/sessions/today	React	Sessions for today only
GET	/api/sessions/export	React (admin)	Download today's sessions as .xlsx


Database
Setting	Value
Database name	percepta_db
Username	percepta_user
Password	percepta_pass
Host	localhost
Port	5432

The .env file in percepta_backend/ must contain:
DATABASE_URL=postgresql://percepta_user:percepta_pass@localhost:5432/percepta_db


Frontend — Page by Page
Page	File	What it shows	Refresh
Dashboard	DashboardPage.jsx	Stat cards, time-series chart, recent events, protocol mix	Every 15s
Events	EventsPage.jsx	Full event table with search, filter, sort, View modal	Every 10s
Blocked IPs	BlockedPage.jsx	Active blocked IPs, unblock button, count synced to dashboard	Every 10s
Logs	LogsPage.jsx	Session log table, Export Today → downloads .xlsx	On load

api/index.js
Single file that contains every API call the frontend makes. All fetch() calls go through a shared request() helper that sets the base URL and handles errors. To change the backend address, only this one file needs to be updated.

EventModal.jsx
Popup that appears when admin clicks View on an event. Shows all 12 ML fields (anomaly score, threshold, stability, risk score, network load, etc.). Contains a Block IP button that calls POST /api/block/{ip} directly. If the IP is already blocked it shows Already Blocked (greyed out).


How to Run
Requirements
• Python 3.11+
• Node.js 18+
• PostgreSQL 15+ running on localhost:5432
• pgAdmin 4 (optional — for inspecting the database)

Step 1 — Install Python dependencies
cd percepta_backend
pip install -r requirements.txt
pip install openpyxl      # needed for Export Today button

Step 2 — Create .env file
Create a file at percepta_backend/.env with this content:
DATABASE_URL=postgresql://percepta_user:percepta_pass@localhost:5432/percepta_db

Step 3 — Start the backend
cd percepta_backend
uvicorn main:app --reload --port 8000
PostgreSQL tables are created automatically on first startup. API will be at http://127.0.0.1:8000.
To see all endpoints with live testing: http://127.0.0.1:8000/docs

Step 4 — Start the frontend
cd percepta-frontend
npm install
npm run dev
Dashboard opens at http://127.0.0.1:5173.

Step 5 — Populate Logs (first time only)
If the Logs page shows 0 sessions after the first run, execute the migration script once:
cd percepta_backend
python migrate_sessions.py
This reads all existing events from the database and creates the corresponding session rows. Only needs to be run once.


How the Three Parts Connect
My backend is the middle layer between the ML engine and the frontend:
ML Engine  →  POST /api/events/  →  Backend  →  PostgreSQL
React      →  GET  /api/events/  →  Backend  →  PostgreSQL
React      →  GET  /api/stats/   →  Backend  →  PostgreSQL

The ML engine (Mirkomil) calls POST /api/events/ after analyzing each network flow. The backend validates the data, saves it to the events table, and if the action is TEMP_BLOCK, also updates the blocked_ips and user_sessions tables automatically.
The React frontend never writes to the database directly. It only reads via GET requests and sends admin actions (block/unblock) via POST. The frontend does not need to know anything about the ML engine — it only knows the backend API.


Percepta  •  Web Platform & Backend  •  Asilbek Tashpulatov  •  2026
