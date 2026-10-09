# Backend API

Backend รับและตรวจ request จาก frontend, บันทึกคิวใน SQLite, ให้บริการ status/history และเสิร์ฟไฟล์ผลลัพธ์ ส่วนโหลดโมเดลและสร้างภาพทำโดย worker ใน `ai/`

## ติดตั้งและรัน

สร้าง environment และติดตั้ง dependency ตามลำดับใน [README หลัก](../README.md#ติดตั้งครั้งแรก) จากนั้นเปิด backend จากโฟลเดอร์หลัก:

```powershell
cd c:\proAi
.\backend\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --port 8000
```

ถ้า frontend/browser อยู่คนละเครื่อง ให้เพิ่ม `--host 0.0.0.0` เพื่อให้ backend รับ connection จาก network:

```powershell
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

`0.0.0.0` คือ address สำหรับให้ server ฟังทุก network interface ไม่ใช่ IP ที่ client ใช้เรียก backend ใน frontend ให้ใส่ IPv4 จริงของเครื่อง backend ใน `--api-url` เช่น `http://172.20.5.197:8000` โดยหา IP ด้วย `ipconfig`

ปกติไม่ต้องแก้ IP ใน `main.py` หากมี reverse proxy หรือ URL ภายนอกสำหรับลิงก์รูป ให้ตั้ง environment variable `PUBLIC_BASE_URL` เป็น URL ที่ client เปิดถึงได้ก่อน start backend

## Endpoints

- `GET /api/health` checks that the API is available.
- `POST /api/generate` validates and queues a generation job.
- `GET /api/generate/{job_id}` returns its status, progress, and images.
- `GET /api/history?limit=50` lists saved generation jobs.
- `GET /api/models` lists model files in `backend/models/`.

ไฟล์ SQLite เริ่มต้นคือ `database/ai_image_studio.sqlite3` ไม่มี database IP ให้ตั้ง ถ้ากำหนด `AI_IMAGE_DATABASE` ต้องตั้ง path เดียวกันใน environment ของ backend และ AI worker