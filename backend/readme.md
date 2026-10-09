# Backend API

Backend รับและตรวจ request จาก frontend, บันทึกคิวงานใน SQLite, แสดงสถานะและประวัติ และให้บริการไฟล์ผลลัพธ์ ส่วนสร้างภาพทำโดย AI worker

## ติดตั้ง

เปิด PowerShell ที่โฟลเดอร์หลักของโปรเจกต์:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

## รัน

จากโฟลเดอร์หลักของโปรเจกต์:

```powershell
uvicorn backend.main:app --reload --port 8000
```

ถ้าต้องการให้เครื่องอื่นในเครือข่ายเรียก backend ได้:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

ตรวจสอบการทำงานได้ที่ `GET http://127.0.0.1:8000/api/health` ซึ่งควรตอบ `{"status":"ok","service":"ai-image-backend"}`

## Endpoints

- `GET /api/health` - ตรวจสอบสถานะ backend
- `POST /api/generate` - ตรวจ request และสร้างคิวงานภาพ
- `GET /api/generate/{job_id}` - ดูสถานะและผลลัพธ์ของงาน
- `GET /api/history?limit=50` - ดูประวัติงาน
- `GET /api/models` - ดูโมเดลใน `backend/models/`
- `POST /api/models/download` - ดาวน์โหลดโมเดล

ฐานข้อมูล SQLite จะถูกสร้างโดยอัตโนมัติที่ `database/ai_image_studio.sqlite3` หากต้องกำหนดตำแหน่งเอง ให้ตั้ง `AI_IMAGE_DATABASE` เป็นค่าเดียวกันทั้ง backend และ AI worker ส่วน URL สำหรับลิงก์รูปที่ frontend เข้าถึงได้กำหนดผ่าน `PUBLIC_BASE_URL`.
