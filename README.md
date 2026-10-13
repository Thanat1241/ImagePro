# ImagePro

<<<<<<< HEAD
ดูขั้นตอนติดตั้งแบบละเอียดที่ [INSTALL.md](./INSTALL.md)
=======
คู่มือติดตั้งหลัง clone หรือ sync อยู่ที่ [INSTALL.md](./INSTALL.md)
>>>>>>> main

โปรเจกต์สร้างภาพแบ่งเป็น 3 ส่วนที่รันคนละเครื่องได้: frontend ให้บริการหน้าเว็บ, backend รับงานและเก็บคิวใน SQLite, ส่วน AI worker รับงานผ่าน HTTP สร้างภาพบนเครื่อง AI แล้วอัปโหลดผลกลับไปที่ backend โดย worker ไม่ต้องเข้าถึงไฟล์ฐานข้อมูลหรือโฟลเดอร์ของ backend โดยตรง

## รันแยกเครื่อง

วางโค้ดโปรเจกต์ไว้บนเครื่อง backend, frontend และ AI เครื่อง backend กับ AI ต้องติดตั้ง Python และแพ็กเกจจาก `backend/requirements.txt`; ให้ติดตั้ง PyTorch ให้ตรงกับ CPU/CUDA ของเครื่อง AI ก่อน ส่วน frontend ใช้ Python standard library

ใช้ IP ที่เครื่องอื่นเข้าถึงได้ผ่าน LAN หรือ VPN แทนค่าตัวอย่างด้านล่าง และกำหนด `AI_WORKER_TOKEN` ให้เป็น secret เดียวกันบนเครื่อง backend กับ AI

### เครื่อง Backend

เปิด PowerShell ที่โฟลเดอร์โปรเจกต์:

```powershell
$env:AI_WORKER_TOKEN = "ใส่-secret-ชุดเดียวกับเครื่อง-AI"
.\run_backend.bat
```

ค่าเริ่มต้น backend ฟังที่ `0.0.0.0:8000` หาก browser ใช้ host ที่ต่างจาก URL ที่ backend มองเห็น (เช่น ผ่าน reverse proxy) ให้ตั้ง `PUBLIC_BASE_URL` เป็น URL ที่ browser ใช้เปิดรูป เช่น `http://192.168.1.20:8000` ก่อนเริ่ม backend หากไม่ตั้ง ระบบจะใช้ host ที่ browser เรียก API เข้ามา

### เครื่อง AI

คัดลอกไฟล์โมเดลไปไว้ที่ `ai/models/` บนเครื่องนี้ ชื่อโมเดลเริ่มต้นคือ `meinamix_v12Final.safetensors` จาก PowerShell ที่โฟลเดอร์โปรเจกต์:

```powershell
$env:AI_BACKEND_URL = "http://192.168.1.20:8000"
$env:AI_WORKER_TOKEN = "ใส่-secret-ชุดเดียวกับเครื่อง-backend"
.\run_worker.bat
```

Worker เชื่อมต่อออกไปหา backend จึงไม่ต้องเปิดพอร์ตรับการเชื่อมต่อ `AI_MODELS_DIR` และ `AI_OUTPUTS_DIR` กำหนดเป็นโฟลเดอร์เฉพาะเครื่องได้ ภาพที่สร้างจะถูกอัปโหลดไปเก็บบน backend อัตโนมัติ

### เครื่อง Frontend

จาก PowerShell ที่โฟลเดอร์โปรเจกต์:

```powershell
$env:AI_BACKEND_URL = "http://192.168.1.20:8000"
.\run_frontend.bat
```

เปิด `http://<IP-เครื่อง-frontend>:5500` ใน browser เครื่องที่เปิด browser ต้องเข้าถึง frontend ที่ TCP port `5500` และ backend ที่ TCP port `8000`; อนุญาตพอร์ตเหล่านี้ใน firewall ตามที่จำเป็น Browser ติดต่อ backend โดยตรง ส่วน frontend ส่งหน้าเว็บให้ browser เท่านั้น

กำหนดค่าผ่าน environment variable ได้ ได้แก่ `BACKEND_HOST`, `BACKEND_PORT`, `FRONTEND_HOST`, `FRONTEND_PORT`, `AI_BACKEND_URL`, `AI_WORKER_TOKEN`, `AI_MODELS_DIR`, `AI_OUTPUTS_DIR`, `AI_IMAGE_DATABASE` และ `PUBLIC_BASE_URL`; `AI_IMAGE_DATABASE` ใช้เฉพาะเครื่อง backend

## รันทุกส่วนบนเครื่องเดียว

รัน `run_all.bat` เพื่อเปิด backend, frontend และ worker ใน terminal แยกกันด้วยค่าท้องถิ่น ค่า `dev-secret` ที่สคริปต์ตั้งให้นี้ใช้สำหรับรันบนเครื่องเดียวเท่านั้น หากแยกเครื่องให้กำหนด secret ใหม่และตั้งค่าเดียวกันบน backend กับ AI worker

## ตรวจสถานะ

เมื่อ backend ทำงานแล้ว เปิด `http://<IP-เครื่อง-backend>:8000/api/health` ควรได้ `{"status":"ok","service":"ai-image-backend"}`
