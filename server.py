
import os
import uuid
import datetime
import hmac
import hashlib
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Header, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, desc, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Security Configuration ---
# Beta-grade command signing: HMAC shared secret.
# For enterprise, use asymmetric signatures + rotation.
COMMAND_SIGNING_SECRET = os.getenv("COMMAND_SIGNING_SECRET", "change-me-in-prod")
GENAI_API_KEY = os.getenv("GENAI_API_KEY", "")

# --- Database Setup ---
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@db:5432/ivecguard")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---
class TenantSettings(Base):
    __tablename__ = "tenant_settings"
    id = Column(String, primary_key=True, default="tenant-001")
    name = Column(String, default="Global Dynamics")
    plan = Column(String, default="ENTERPRISE")
    print_limit = Column(Integer, default=20)
    risk_decay_rate = Column(Integer, default=5)
    idle_timeout = Column(Integer, default=30)
    critical_alert_level = Column(Integer, default=80)
    keywords = Column(JSON, default=["confidential", "internal-only", "salary"])

class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    hostname = Column(String)
    employee_name = Column(String, default="Auto-Identified Agent")
    department = Column(String, default="Infrastructure")
    os_info = Column(String)
    ip_address = Column(String)
    status = Column(String, default="ONLINE")
    risk_score = Column(Integer, default=0)
    predictive_risk_score = Column(Integer, default=0)
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)
    work_stats = Column(JSON, default={"uptime": 0, "activeTime": 0, "idleTime": 0, "printCount": 0, "fileModCount": 0})
    policy = Column(JSON, default={
        "fileMonitoring": True, "usbMonitoring": True, "printMonitoring": True,
        "searchKeywordMonitoring": True, "idleTracking": True
    })
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)

class SecurityEvent(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("devices.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String)
    severity = Column(String)
    description = Column(String)
    risk_weight = Column(Integer)
    metadata_json = Column(JSON)

class Command(Base):
    __tablename__ = "commands"
    id = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("devices.id"))
    action = Column(String)
    status = Column(String, default="PENDING")
    issued_by = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    executed_at = Column(DateTime, nullable=True)


def _sign_command(cmd_id: str, device_id: str, action: str, expires_at: datetime.datetime) -> str:
    """Return a hex HMAC signature for a command payload."""
    msg = f"{cmd_id}|{device_id}|{action}|{expires_at.isoformat()}".encode("utf-8")
    return hmac.new(COMMAND_SIGNING_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()

Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class EventIn(BaseModel):
    type: str
    description: str
    weight: int
    metadata: dict

class TelemetryIn(BaseModel):
    agent_id: str
    events: List[EventIn]
    work_stats: dict

class CommandIn(BaseModel):
    deviceId: str
    action: str

class ConfigUpdateIn(BaseModel):
    printLimit: int
    riskDecayRate: int
    keywords: List[str]


class AIAnalyzeIn(BaseModel):
    events: List[Dict[str, Any]]


class AIAnalysisOut(BaseModel):
    summary: str
    threatDetected: bool
    correlationChain: List[str]
    recommendedActions: List[str]
    behaviorScore: int
    predictiveForecast: Dict[str, Any]

# --- FastAPI App Initialization ---
app = FastAPI(title="IVECGuard AI Core")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.on_event("startup")
def startup_populate():
    db = SessionLocal()
    if not db.query(TenantSettings).first():
        db.add(TenantSettings())
        db.commit()
    db.close()

# --- Unified v1 Router ---
v1_router = APIRouter(prefix="/api/v1")

# --- Agent Endpoints ---
@v1_router.post("/agent/register")
async def register_agent(req: Request, db: Session = Depends(get_db)):
    data = await req.json()
    did = data.get('agent_id')
    if not did: raise HTTPException(status_code=400, detail="agent_id required")
    dev = db.query(Device).filter(Device.id == did).first()
    if not dev:
        dev = Device(id=did, hostname=data.get('hostname', 'Unknown'), os_info=data.get('os_info', 'Unknown'), ip_address=req.client.host)
        db.add(dev)
        db.commit()
    return {"status": "success", "policy": dev.policy}

@v1_router.post("/agent/telemetry")
async def receive_telemetry(payload: TelemetryIn, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == payload.agent_id).first()
    if not dev: raise HTTPException(status_code=404)
    dev.last_heartbeat = datetime.datetime.utcnow()
    dev.status = "ONLINE"
    dev.work_stats = payload.work_stats
    for e in payload.events:
        event = SecurityEvent(id=str(uuid.uuid4()), device_id=payload.agent_id, type=e.type, 
                             severity="CRITICAL" if e.weight > 60 else "NORMAL",
                             description=e.description, risk_weight=e.weight, metadata_json=e.metadata)
        db.add(event)
        dev.risk_score = min(100, dev.risk_score + e.weight)
    db.commit()
    return {"status": "success", "policy": dev.policy}

@v1_router.get("/agent/commands/{agent_id}")
async def poll_commands(agent_id: str, db: Session = Depends(get_db)):
    cmds = db.query(Command).filter(Command.device_id == agent_id, Command.status == "PENDING", 
                                  Command.expires_at > datetime.datetime.utcnow()).all()
    results = []
    for c in cmds:
        sig = _sign_command(c.id, c.device_id, c.action, c.expires_at)
        results.append({
            "id": c.id,
            "action": c.action,
            "expiresAt": c.expires_at.isoformat() if c.expires_at else None,
            "signature": sig,
        })
    for c in cmds: c.status = "SENT"
    db.commit()
    return results

@v1_router.post("/agent/commands/{cid}/ack")
async def ack_command(cid: str, data: dict, db: Session = Depends(get_db)):
    cmd = db.query(Command).filter(Command.id == cid).first()
    if cmd:
        cmd.status = data.get("status", "EXECUTED")
        cmd.executed_at = datetime.datetime.utcnow()
        db.commit()
    return {"status": "ok"}

# --- Admin Endpoints ---
@v1_router.get("/admin/devices")
async def get_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return [{
        "id": d.id, 
        "name": d.hostname, 
        "employeeName": d.employee_name, 
        "department": d.department,
        "os": d.os_info, 
        "status": d.status, 
        "lastHeartbeat": d.last_heartbeat.isoformat() if d.last_heartbeat else None,
        "riskScore": d.risk_score, 
        "predictiveRiskScore": min(100, d.risk_score + 10),
        "ipAddress": d.ip_address, 
        "profileId": "p1", 
        "tenantId": "tenant-001",
        "agentVersion": "2.5.0", 
        "peerDeviation": 0, 
        "isTamperProtected": True, 
        "workStats": d.work_stats,
        "policy": d.policy
    } for d in devices]

@v1_router.put("/admin/devices/{id}/policy")
async def update_policy(id: str, policy: dict, db: Session = Depends(get_db)):
    dev = db.query(Device).filter(Device.id == id).first()
    if not dev: raise HTTPException(status_code=404)
    dev.policy = policy
    db.commit()
    return {"status": "updated"}

@v1_router.get("/admin/events")
async def get_events(db: Session = Depends(get_db)):
    events = db.query(SecurityEvent).order_by(desc(SecurityEvent.timestamp)).limit(50).all()
    return [{
        "id": e.id, 
        "deviceId": e.device_id, 
        "tenantId": "tenant-001",
        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        "type": e.type, 
        "severity": e.severity, 
        "description": e.description,
        "riskWeight": e.risk_weight, 
        "metadata": e.metadata_json
    } for e in events]

@v1_router.get("/admin/config")
async def get_config(db: Session = Depends(get_db)):
    s = db.query(TenantSettings).first()
    return {
        "id": s.id, 
        "name": s.name, 
        "plan": s.plan,
        "thresholds": {
            "printLimit": s.print_limit, 
            "riskDecayRate": s.risk_decay_rate / 100,
            "idleTimeout": s.idle_timeout, 
            "criticalAlertLevel": s.critical_alert_level 
        },
        "keywords": s.keywords
    }

@v1_router.put("/admin/config")
async def update_config(data: ConfigUpdateIn, db: Session = Depends(get_db)):
    s = db.query(TenantSettings).first()
    s.print_limit = data.printLimit
    s.risk_decay_rate = data.riskDecayRate
    s.keywords = data.keywords
    db.commit()
    return {"status": "success"}

@v1_router.post("/admin/commands")
async def issue_command(payload: CommandIn, db: Session = Depends(get_db)):
    cmd = Command(id=str(uuid.uuid4()), device_id=payload.deviceId, action=payload.action,
                 issued_by="ADMIN_UI", timestamp=datetime.datetime.utcnow(),
                 expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=5))
    db.add(cmd)
    db.commit()
    return {"id": cmd.id, "status": "PENDING"}

@v1_router.get("/admin/commands/history")
async def get_command_history(db: Session = Depends(get_db)):
    cmds = db.query(Command).order_by(desc(Command.timestamp)).limit(20).all()
    return [{"id": c.id, "deviceId": c.device_id, "action": c.action, "status": c.status, 
             "timestamp": c.timestamp.isoformat() if c.timestamp else None} for c in cmds]


# --- AI (Server-side only) ---
@v1_router.post("/ai/analyze", response_model=AIAnalysisOut)
async def ai_analyze(payload: AIAnalyzeIn):
    """Server-side AI analysis.

    For beta pilots, this endpoint returns a robust heuristic analysis if no AI key is configured.
    If GENAI_API_KEY is provided, you can extend this to call the provider from the server only.
    """

    events = payload.events or []
    risk = 0
    chain = []
    for e in events:
        w = int(e.get("riskWeight") or e.get("weight") or 0)
        risk += w
        t = e.get("type") or "EVENT"
        chain.append(str(t))

    behavior_score = max(0, min(100, risk))
    threat = behavior_score >= 60
    rec = ["monitor_closely"]
    if behavior_score >= 80:
        rec = ["lock_device", "isolate_network"]
    elif behavior_score >= 60:
        rec = ["increase_monitoring", "review_print_activity"]

    # Heuristic summary – safe default.
    summary = (
        "Heuristic correlation based on aggregated event weights. "
        "Configure GENAI_API_KEY on the backend to enable LLM narrative summaries."
    )

    return {
        "summary": summary,
        "threatDetected": threat,
        "correlationChain": chain[-10:],
        "recommendedActions": rec,
        "behaviorScore": behavior_score,
        "predictiveForecast": {
            "probability7d": min(int(behavior_score * 0.8), 100),
            "topRiskFactors": ["High-weight event sequence" if threat else "Normal variability"],
            "timeToEscalation": "Immediate" if threat else "Unknown",
        },
    }

# Include the unified router
app.include_router(v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
