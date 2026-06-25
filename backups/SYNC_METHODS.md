# ATSAWIN SYNC METHODS — STABILITY COMPARISON

## สรุป: แบบไหนเสถียรสุด?

| วิธี | ความเสถียร | Real-time | ขนาดไฟล์ | ต้องทำเอง |
|------|:---------:|:---------:|---------|:---------:|
| **Syncthing** | ⭐⭐⭐⭐⭐ | ✅ ใช่ | ไม่จำกัด | ❌ อัตโนมัติ |
| Git + cron | ⭐⭐⭐⭐ | ❌ ต้องรอ | <100MB/ไฟล์ | ❌ กึ่งอัตโนมัติ |
| Dropbox/Drive | ⭐⭐⭐ | ✅ ใช่ | ตาม plan | ❌ อัตโนมัติ |
| rsync | ⭐⭐⭐⭐ | ❌ manual | ไม่จำกัด | ✅ ต้องรัน |

## แนะนำ: ใช้ 2 ระบบคู่กัน

### 1. GIT → code, scripts, config
- Push/Pull ตามรอบ (cron ทุก 23:00)
- ย้อนเวอร์ชั่นได้
- ✅ ตั้งไว้แล้ว

### 2. SYNCTHING → live data, signals, shared files
- sync ทันทีที่ไฟล์เปลี่ยน
- ไม่ต้อง commit
- ไม่มี conflict (last-write-wins)
- เข้ารหัส end-to-end
- ฟรี ไม่จำกัดขนาด

## ระบบที่เหมาะกับ Atsawin

```
GitHub (code)
├── repos/AI/          ← cron push ทุกวัน
├── repos/ai-trading-rpg/
└── repos/atsawin-trading-cafe/

Syncthing (live data)
├── Desktop/bridge signals    ← sync ทันที
├── MT5 Common/Files/atsawin/ ← signal files
└── backups/configs/          ← config sync
```

## วิธีเซ็ตอัพ Syncthing

### เครื่องหลัก (Windows)
1. โหลด: https://syncthing.net/downloads/
2. ติดตั้ง → เปิด browser http://127.0.0.1:8384
3. Add Folder → เลือกโฟลเดอร์ที่ต้องการ sync
4. จด Device ID

### เครื่องใหม่
1. ติดตั้ง Syncthing เหมือนกัน
2. Add Remote Device → ใส่ Device ID จากเครื่องหลัก
3. Share โฟลเดอร์เดียวกัน

### โฟลเดอร์ที่ควร sync ผ่าน Syncthing

| โฟลเดอร์ | เหตุผล |
|----------|--------|
| Desktop/*.py, *.json | bridge scripts ต้องตรงกัน |
| MT5 Common/Files/atsawin/ | signal files ระหว่าง MT5 |
| backups/configs/ | Hermes configs |

## One-liner: Syncthing เหนือกว่าเพราะ

- ไฟล์เปลี่ยน → sync ทันที (ไม่เกิน 60 วิ)
- ไม่ต้อง commit/push/pull
- ไม่มีปัญหา merge conflict
- ต่อตรง machine-to-machine
- ฟรี ไม่จำกัด
- ทำงาน offline ได้ (sync ทีหลังเมื่อต่อเน็ต)