
import os
import sys
import time
import json
import uuid
import ctypes
import requests
import threading
import subprocess
import platform
import hmac
import hashlib
from datetime import datetime

# Windows low-level input tracking
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_duration():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    return 0

try:
    import win32print
    import win32api
    import pythoncom
    import wmi
except ImportError:
    print("FATAL: Missing Windows dependencies.")
    sys.exit(1)

class IVECGuardAgent:
    def __init__(self):
        self.server_url = os.getenv("IVEC_SERVER", "http://localhost:8000/api/v1")
        self.command_secret = os.getenv("COMMAND_SIGNING_SECRET", "change-me-in-prod")
        self.agent_id = str(uuid.getnode())
        self.event_queue = []
        # Simple offline queue (beta): JSONL file. If the server is unreachable, we persist events
        # locally then flush on reconnect.
        base_dir = os.getenv("PROGRAMDATA", os.path.expanduser("~"))
        self.offline_path = os.path.join(base_dir, "IVECGuard")
        os.makedirs(self.offline_path, exist_ok=True)
        self.offline_file = os.path.join(self.offline_path, "offline_events.jsonl")
        self.work_stats = {"uptime": 0, "activeTime": 0, "idleTime": 0, "printCount": 0, "fileModCount": 0}
        self.policy = {}
        self.running = True

    def _verify_command(self, cmd: dict) -> bool:
        """Verify HMAC signature on a command (beta-grade)."""
        try:
            cid = cmd.get("id")
            action = cmd.get("action")
            expires_at = cmd.get("expiresAt")
            sig = cmd.get("signature")
            if not (cid and action and expires_at and sig):
                return False
            msg = f"{cid}|{self.agent_id}|{action}|{expires_at}".encode("utf-8")
            expected = hmac.new(self.command_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, sig)
        except Exception:
            return False

    def log_event(self, etype, desc, weight, meta={}):
        evt = {"type": etype, "description": desc, "weight": weight, "metadata": meta}
        self.event_queue.append(evt)

    def _persist_offline(self, events):
        try:
            with open(self.offline_file, "a", encoding="utf-8") as f:
                for e in events:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
        except Exception:
            # Best-effort persistence (beta)
            pass

    def _load_offline(self, max_lines: int = 200):
        if not os.path.exists(self.offline_file):
            return []
        events = []
        try:
            with open(self.offline_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    events.append(json.loads(line))
        except Exception:
            return []
        return events

    def _truncate_offline(self, consumed: int):
        """Remove the first `consumed` lines from the jsonl file."""
        if consumed <= 0 or not os.path.exists(self.offline_file):
            return
        try:
            with open(self.offline_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            remaining = lines[consumed:]
            with open(self.offline_file, "w", encoding="utf-8") as f:
                f.writelines(remaining)
        except Exception:
            pass

    def monitor_printing(self):
        """Resilient Print Auditing with retry-on-spool logic"""
        pythoncom.CoInitialize()
        last_logged = set()
        while self.running:
            if not self.policy.get("printMonitoring", True):
                time.sleep(10); continue
            try:
                for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL):
                    h = win32print.OpenPrinter(printer[2])
                    jobs = win32print.EnumJobs(h, 0, -1, 1)
                    for job in jobs:
                        jid = f"{printer[2]}-{job['JobId']}"
                        if jid in last_logged: continue
                        
                        # Forensic verification: Is job count stable?
                        pages = job.get('TotalPages', 0) or 0
                        # Spooler sometimes reports 0 pages. If job is marked printed, fallback to 1.
                        # Otherwise, skip until the job advances.
                        if pages == 0:
                            status = job.get('Status', 0) or 0
                            if status & win32print.JOB_STATUS_PRINTED:
                                pages = 1
                            else:
                                continue
                        
                        self.log_event("PRINT", f"Document: {job['pDocument']}", 15 if pages < 10 else 40, {"pages": pages})
                        self.work_stats["printCount"] += pages
                        last_logged.add(jid)
                    win32print.ClosePrinter(h)
            except: pass
            time.sleep(5)

    def monitor_idle_precise(self):
        """High-precision idle tracking using ctypes GetLastInputInfo"""
        while self.running:
            if not self.policy.get("idleTracking", True):
                time.sleep(10); continue
            self.work_stats["uptime"] += 1
            idle = get_idle_duration()
            if idle > 60: # 60s threshold
                self.work_stats["idleTime"] += 1
            else:
                self.work_stats["activeTime"] += 1
            time.sleep(1)

    def monitor_usb(self):
        pythoncom.CoInitialize()
        try:
            watcher = wmi.WMI().watch_for(notification_type="Creation", wmi_class="Win32_USBHub")
            while self.running:
                if not self.policy.get("usbMonitoring", True):
                    time.sleep(10); continue
                usb = watcher()
                self.log_event("USB_INSERT", f"USB Mounted: {usb.DeviceID}", 45)
        except: pass

    def sync_loop(self):
        # Initial Registration
        try:
            resp = requests.post(f"{self.server_url}/agent/register", json={
                "agent_id": self.agent_id, "hostname": os.getenv("COMPUTERNAME", "PC"),
                "os_info": f"{platform.system()} {platform.release()}"
            }, timeout=10)
            self.policy = resp.json().get("policy", {})
        except: pass

        while self.running:
            try:
                # Telemetry & Policy Fetch
                # Merge offline queued events (beta)
                offline = self._load_offline(max_lines=200)
                merged = offline + self.event_queue[:]
                payload = {"agent_id": self.agent_id, "events": merged, "work_stats": self.work_stats}
                r = requests.post(f"{self.server_url}/agent/telemetry", json=payload, timeout=10)
                # If telemetry succeeded, clear in-memory queue and truncate offline file
                self.event_queue = []
                if offline:
                    self._truncate_offline(consumed=len(offline))
                self.policy = r.json().get("policy", {})

                # C2 Commands
                cmds = requests.get(f"{self.server_url}/agent/commands/{self.agent_id}", timeout=10).json()
                for c in cmds:
                    if not self._verify_command(c):
                        # Do not execute unsigned/invalid commands
                        continue
                    print(f"Executing: {c['action']}")
                    status = "EXECUTED"
                    try:
                        if c['action'] == "LOCK":
                            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
                        else:
                            status = "FAILED"
                    except Exception:
                        status = "FAILED"
                    requests.post(
                        f"{self.server_url}/agent/commands/{c['id']}/ack",
                        json={"status": status},
                        timeout=10,
                    )

            except Exception:
                # Persist current events offline if we couldn't reach the server
                if self.event_queue:
                    self._persist_offline(self.event_queue)
                    self.event_queue = []
            time.sleep(15)

    def run(self):
        print(f"IVECGuard Agent {self.agent_id} Beta-Start.")
        threads = [
            threading.Thread(target=self.monitor_usb, daemon=True),
            threading.Thread(target=self.monitor_printing, daemon=True),
            threading.Thread(target=self.monitor_idle_precise, daemon=True),
            threading.Thread(target=self.sync_loop, daemon=True)
        ]
        for t in threads: t.start()
        while self.running: time.sleep(1)

if __name__ == "__main__":
    IVECGuardAgent().run()
