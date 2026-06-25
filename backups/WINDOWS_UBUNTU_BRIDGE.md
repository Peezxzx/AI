# ATSAWIN: Windows ↔ Ubuntu Cross-Machine Bridge

## Architecture

```
┌──────────────────────┐         ┌──────────────────────┐
│   WINDOWS (Dev)      │         │   UBUNTU (Production)│
│   DESKTOP-4NRHFGA    │         │   VPS/Server         │
├──────────────────────┤         ├──────────────────────┤
│ • MT5 Trading        │         │ • FastAPI Backend    │
│ • EA Bridge          │         │ • PostgreSQL + Redis │
│ • Hermes Agent       │         │ • Telegram Bot       │
│ • Desktop scripts    │  sync   │ • Signal processing  │
│                      │ ◄═════► │                      │
│   Syncthing (P2P)    │  real-  │   Syncthing (P2P)    │
│   GitHub (code)      │  time   │   GitHub (code)      │
└──────────────────────┘         └──────────────────────┘
```

## Connection Methods

### Layer 1: Syncthing (Real-time files)
- Trading signals, configs, scripts sync ทันที
- 4 shared folders
- P2P encrypted, no cloud storage

### Layer 2: GitHub (Versioned code)
- All repos synced
- Cron auto-push from Windows at 23:00
- Pull on Ubuntu before deploy

### Layer 3: API (Runtime)
- Ubuntu runs FastAPI at `<ubuntu-ip>:8000`
- Windows bridge scripts call Ubuntu API
- Signal flow: Windows MT5 → Ubuntu API → Process → Back to Windows

---

## HOW TO CONNECT (Step by Step)

### ON UBUNTU (run once)

```bash
# SSH into Ubuntu, then:
curl -sL https://raw.githubusercontent.com/Peezxzx/AI/main/backups/scripts/setup_ubuntu.sh | bash
```

This installs everything: Docker, Python, Syncthing, PostgreSQL, Redis, FastAPI.

### ON WINDOWS (connect to Ubuntu)

```bash
# 1. Get Ubuntu's Syncthing Device ID
ssh ubuntu@<ip> "grep -oP 'device id=\"\K[^\"]+' ~/.local/state/syncthing/config.xml | head -1"

# 2. Open Syncthing Web UI → Add Remote Device → Paste ID
start http://127.0.0.1:8384

# 3. Share folders with Ubuntu device
```

### Auto-connect script (for Windows)

```bash
# Run on Windows to connect to Ubuntu
bash /c/Users/Administrator/backups/scripts/connect_ubuntu.sh <ubuntu-ip>
```

---

## Daily Workflow

```
เช้า:
  Windows: เปิด MT5 + bridge
  Ubuntu:   systemctl start atsawin-api (auto-starts)

ระหว่างวัน:
  ไฟล์เปลี่ยน → Syncthing sync อัตโนมัติ → ทั้งสองเครื่องตรงกัน

เย็น:
  Windows: bash sync_bridge.sh push  (push code to GitHub)
  Ubuntu:   bash sync_bridge.sh pull  (pull latest code)
  Ubuntu:   systemctl restart atsawin-api  (deploy new code)
```

---

## Services on Ubuntu

| Service | Port | Command |
|---------|------|---------|
| FastAPI | 8000 | `systemctl status atsawin-api` |
| PostgreSQL | 5433 | `docker ps \| grep atsawin-db` |
| Redis | 6380 | `docker ps \| grep atsawin-cache` |
| Syncthing | 8384 | `systemctl status syncthing@ubuntu` |

## Syncthing Shared Folders

| Folder ID | Path (Windows) | Path (Ubuntu) |
|-----------|---------------|---------------|
| atsawin-desktop | C:\Users\Administrator\syncthing\desktop-scripts | /home/ubuntu/syncthing/desktop-scripts |
| atsawin-signals | C:\Users\Administrator\syncthing\trading-signals | /home/ubuntu/syncthing/trading-signals |
| atsawin-hermes | C:\Users\Administrator\syncthing\hermes-configs | /home/ubuntu/syncthing/hermes-configs |
| atsawin-mt5 | C:\Users\Administrator\syncthing\mt5-common | /home/ubuntu/syncthing/mt5-common |