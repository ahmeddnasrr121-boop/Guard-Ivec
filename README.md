# IVECGuard AI (Beta Pilot)

This repo is a **beta pilot** for IVECGuard AI with an end‑to‑end runnable stack:

- **Backend**: FastAPI + PostgreSQL
- **Frontend**: React (Vite) served by Nginx
- **Windows Agent**: Python agent that sends telemetry + receives commands

## Server (Docker)

### Prerequisites
- Docker + Docker Compose

### Run

```bash
docker compose up --build
```

### URLs
- Dashboard: `http://localhost/`
- API docs (FastAPI): `http://localhost:8000/docs`

> API base path is **`/api/v1`**.

## Frontend Dev Mode (Optional)

If you want Vite dev server:

```bash
npm install
npm run dev
```

Vite is configured to proxy `/api/*` to `http://localhost:8000`.

## Windows Agent

### Prerequisites
- Windows 10/11
- Python 3.10+

### Install dependencies

```bat
pip install requests pywin32 wmi
```

### Run

```bat
set IVEC_SERVER=http://<SERVER_IP>/api/v1
python agent.py
```

### Offline mode
If the server is unreachable, the agent will persist events locally (beta) in:

`%PROGRAMDATA%\IVECGuard\offline_events.jsonl`

## Notes

- This is a beta pilot.
- **Command signing (beta-grade)** is enabled via HMAC using `COMMAND_SIGNING_SECRET` (set on server + agent).
- Enterprise hardening (tamper protection, asymmetric signatures, key rotation, etc.) can be added next.
