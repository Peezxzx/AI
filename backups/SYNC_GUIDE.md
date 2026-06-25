# ATSAWIN CROSS-MACHINE SYNC GUIDE

## วิธีเชื่อมต่อ 2 เครื่องผ่าน GitHub

GitHub ทำหน้าที่เป็น **ตัวกลาง** ระหว่างเครื่อง — Push จากเครื่องนึง Pull อีกเครื่อง

### เครื่องที่ 1 (Main PC ปัจจุบัน)

```
# Push ขึ้น GitHub
bash /c/Users/Administrator/backups/scripts/sync_bridge.sh push

# หรือ Two-way sync
bash /c/Users/Administrator/backups/scripts/sync_bridge.sh sync
```

### เครื่องที่ 2 (เครื่องใหม่)

```bash
# 1. ติดตั้ง git
# 2. Clone repos ทั้งหมด
git clone https://github.com/Peezxzx/AI.git /c/Users/Administrator/repos/AI
git clone https://github.com/Peezxzx/ai-trading-rpg.git /c/Users/Administrator/repos/ai-trading-rpg
git clone https://github.com/Peezxzx/atsawin-trading-cafe.git /c/Users/Administrator/repos/atsawin-trading-cafe

# 3. Copy sync script จาก AI repo
cp /c/Users/Administrator/repos/AI/backups/scripts/sync_bridge.sh ~/

# 4. Pull latest
bash ~/sync_bridge.sh pull
```

### การทำงานประจำวัน

```
# เครื่อง 1: ก่อนปิด — push ทุกอย่างขึ้น GitHub
bash /c/Users/Administrator/backups/scripts/sync_bridge.sh push

# เครื่อง 2: เปิดมา — pull ลงมา
bash ~/sync_bridge.sh pull
```

### Auto-backup (Cron)

มี cron job รัน auto-push ทุกวันเวลา 23:00 น.
ดูสถานะ: `hermes cron list`

### Repos ที่ sync

| Repo | GitHub |
|------|--------|
| AI (main) | Peezxzx/AI |
| ai-trading-rpg | Peezxzx/ai-trading-rpg |
| atsawin-trading-cafe | Peezxzx/atsawin-trading-cafe |

---

## การย้ายเครื่องแบบเต็มระบบ (Full Migration)

ใช้ script อัตโนมัติ:

```bash
# บนเครื่องใหม่ หลังจากติดตั้ง Windows, Python, Git, MT5
bash /c/Users/Administrator/repos/AI/backups/scripts/migrate_to_new_machine.sh
```

Script จะ:
1. Clone ทุก repo จาก GitHub
2. Restore Desktop trading files
3. ติดตั้ง Python dependencies
4. ตั้งค่า sync bridge
5. แสดงขั้นตอนที่ต้องทำเอง (MT5 login, copy EA)