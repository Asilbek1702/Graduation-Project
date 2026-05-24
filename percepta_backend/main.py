"""
Percepta — IDS/IPS Backend API
Anomaly Detection and Intrusion Prevention in University Networks
via Isolation Forest–Based IDS/IPS
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import Base, engine
from api.routes import events, stats, blocked, ip, sessions

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Percepta API",
    description="Backend for Anomaly Detection and Intrusion Prevention in University Networks via Isolation Forest–Based IDS/IPS",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(blocked.router)
app.include_router(ip.router)
app.include_router(sessions.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "system": "Percepta IDS/IPS", "version": "1.0.0"}