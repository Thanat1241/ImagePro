# Backend API

Backend รับ request จาก browser, เก็บคิวงานและประวัติใน SQLite, รายงานสถานะงาน และเก็บไฟล์ภาพที่ AI worker อัปโหลดกลับมา

## ติดตั้งและรัน

ติดตั้ง Python packages บนเครื่อง backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

ตั้ง token ให้ตรงกับ AI worker แล้วรันจากโฟลเดอร์โปรเจกต์:

```powershell
$env:AI_WORKER_TOKEN = "replace-with-the-same-long-random-secret"
.\run_backend.bat
```

ค่าเริ่มต้น backend เปิดที่ `0.0.0.0:8000` เพื่อรับการเชื่อมต่อจากเครื่องอื่น ตั้ง `BACKEND_HOST` และ `BACKEND_PORT` เพื่อเปลี่ยนค่าดังกล่าว

## การตั้งค่าสำหรับหลายเครื่อง

- `AI_WORKER_TOKEN` ต้องเป็นค่าเดียวกันบน backend และ AI worker
- `PUBLIC_BASE_URL` เป็น URL ที่ browser ใช้เปิดไฟล์ภาพ เช่น `http://192.168.1.20:8000` หากไม่ตั้ง backend จะใช้ host ที่ browser ส่ง request เข้ามา
- `AI_IMAGE_DATABASE` เป็นตำแหน่งฐานข้อมูล SQLite ของ backend เท่านั้น
- `AI_OUTPUTS_DIR` เป็นโฟลเดอร์เก็บภาพบน backend หลัง worker อัปโหลด
- `AI_MODELS_DIR` บน backend ใช้แสดงโมเดลที่อยู่บน backend เอง ในการแยกเครื่องให้เก็บไฟล์โมเดลบน AI machine ตามที่อธิบายใน [คู่มือ AI worker](../ai/README.md)

ตรวจสอบ backend ได้ที่ `http://<backend-address>:8000/api/health` พอร์ต TCP `8000` ต้องอนุญาตให้ frontend และ AI worker เข้าถึงได้

## Endpoints

- `GET /api/health` - ตรวจสอบสถานะ backend
- `POST /api/generate` - เพิ่มงานสร้างภาพลงคิว
- `GET /api/generate/{job_id}` - ดูสถานะและผลลัพธ์ของงาน
- `GET /api/history?limit=50` - ดูประวัติงาน
- `GET /api/models` - ดูไฟล์โมเดลที่อยู่ใน `AI_MODELS_DIR` ของ backend
- `POST /api/models/download` - ดาวน์โหลดโมเดลลง `AI_MODELS_DIR` ของ backend
