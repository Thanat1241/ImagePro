<<<<<<< HEAD
# คู่มือติดตั้ง ImagePro

คู่มือนี้อธิบายการติดตั้งบน Windows และการรัน Frontend, Backend และ AI Worker แยกกันคนละเครื่อง โดยต้องติดตั้ง Python environment แยกบนแต่ละเครื่อง

## สิ่งที่ต้องเตรียม

- ติดตั้ง Python 3.10 ขึ้นไปบนทุกเครื่อง แล้วตรวจสอบด้วย `python --version`
- ซิงก์หรือ clone โค้ดโปรเจกต์ไว้บนเครื่อง Backend, AI Worker และ Frontend
- เลือก IP ที่ติดต่อกันได้ผ่าน LAN หรือ VPN อย่าใช้ `127.0.0.1` เป็น URL ของ Backend เมื่อเชื่อมต่อจากเครื่องอื่น
- เตรียมไฟล์โมเดล `meinamix_v12Final.safetensors` แยกไว้สำหรับเครื่อง AI Worker ไฟล์โมเดลไม่อยู่ใน Git เพราะมีขนาดใหญ่

## ติดตั้ง Backend และ AI Worker

ทำขั้นตอนนี้แยกกันทั้งบนเครื่อง Backend และเครื่อง AI Worker โดยเปิด PowerShell ที่โฟลเดอร์โปรเจกต์:

```powershell
python --version
=======
# คู่มือติดตั้ง ImagePro บน Windows

ใช้คู่มือนี้เมื่อติดตั้งโปรเจกต์ใหม่หลัง clone หรือ sync จาก Git โดยแยกบริการ Frontend, Backend และ AI Worker ไว้คนละเครื่องได้

## 1. เตรียมเครื่อง

- ติดตั้ง Python 3.10 ขึ้นไปบนทุกเครื่อง แล้วตรวจด้วย `python --version`
- วางหรือ clone โปรเจกต์ไว้บนเครื่องที่จะรัน Backend, AI Worker และ Frontend
- ใช้ IP ที่ติดต่อกันได้ผ่าน LAN หรือ VPN; อย่าใช้ `127.0.0.1` เป็น URL ของ Backend เมื่อเรียกจากเครื่องอื่น
- เตรียมไฟล์โมเดลแยกต่างหาก เพราะ Git ไม่เก็บไฟล์โมเดลขนาดใหญ่

## 2. ติดตั้งแพ็กเกจบน Backend และ AI Worker

ทำคำสั่งต่อไปนี้แยกกันบนเครื่อง Backend และเครื่อง AI Worker จาก PowerShell ที่โฟลเดอร์โปรเจกต์:

```powershell
>>>>>>> main
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

<<<<<<< HEAD
ถ้ามี `.venv` อยู่แล้ว ไม่ต้องสร้างใหม่ ให้ใช้ Python ใน environment นั้นเพื่อติดตั้งหรืออัปเดต requirements:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

เครื่อง AI ที่ใช้ NVIDIA GPU ต้องติดตั้ง PyTorch build ให้ตรงกับระบบ CUDA ก่อน โดยเลือก Windows, Pip, Python และ CUDA version จาก [หน้าเลือกคำสั่งติดตั้ง PyTorch](https://pytorch.org/get-started/locally/) แล้วรันคำสั่งใน environment `.venv` เดียวกันก่อนติดตั้ง requirements ข้างต้น เครื่อง CPU สามารถติดตั้งจาก requirements ได้โดยตรง

## เตรียมโมเดลบนเครื่อง AI

คัดลอกไฟล์โมเดลมาไว้ที่:
=======
ถ้ามี `.venv` อยู่แล้ว ข้ามคำสั่งสร้าง environment ได้ ส่วนเครื่อง AI ที่ใช้ NVIDIA GPU ให้ติดตั้ง PyTorch สำหรับ Windows/Pip/CUDA ที่ตรงกับเครื่องจาก [หน้าเลือกคำสั่งติดตั้ง PyTorch](https://pytorch.org/get-started/locally/) ใน `.venv` ก่อน แล้วจึงติดตั้ง requirements ข้างต้น หากใช้ CPU ให้ติดตั้ง requirements ได้เลย

ไฟล์ requirements ของโปรเจกต์อยู่ที่ [backend/requirements.txt](./backend/requirements.txt) เครื่อง Frontend ไม่ต้องลง pip packages หรือ Node.js เพิ่ม

## 3. เตรียมโมเดลบนเครื่อง AI

คัดลอกโมเดลไปไว้ในโฟลเดอร์นี้บนเครื่อง AI:
>>>>>>> main

```text
ai\models\meinamix_v12Final.safetensors
```

<<<<<<< HEAD
หากใช้โฟลเดอร์อื่น ให้ตั้ง `AI_MODELS_DIR` ก่อนเริ่ม Worker ชื่อไฟล์ต้องตรงกับชื่อโมเดลที่เลือกในหน้าเว็บ

## ตั้งค่าและเริ่ม Backend

บนเครื่อง Backend เปิด PowerShell ที่โฟลเดอร์โปรเจกต์ กำหนด secret ที่จะใช้ร่วมกับ AI Worker แล้วเริ่มบริการ:

```powershell
$env:AI_WORKER_TOKEN = "ใส่-secret-ที่ใช้ค่าเดียวกันบนเครื่อง-AI"
.\run_backend.bat
```

Backend เปิดรับการเชื่อมต่อที่พอร์ต `8000` โดยค่าเริ่มต้น ตรวจสอบได้ที่ `http://127.0.0.1:8000/api/health` บนเครื่อง Backend

ปกติไม่ต้องตั้ง `PUBLIC_BASE_URL`; Backend จะสร้างลิงก์ภาพจาก URL ที่ browser ใช้เรียก API หากใช้ reverse proxy หรือ host ที่ Backend ตรวจจับไม่ตรงกับ URL ที่ browser เข้าถึง ให้กำหนด `PUBLIC_BASE_URL` เป็น URL ของ Backend ที่ browser เปิดได้

## ตั้งค่าและเริ่ม AI Worker

บนเครื่อง AI เปิด PowerShell ที่โฟลเดอร์โปรเจกต์ กำหนด URL ของ Backend และใช้ secret เดียวกันกับ Backend:

```powershell
$env:AI_BACKEND_URL = "http://<IP-เครื่อง-backend>:8000"
$env:AI_WORKER_TOKEN = "ใส่-secret-เดียวกับเครื่อง-backend"
.\run_worker.bat
```

Worker เชื่อมต่อออกไปยัง Backend เอง จึงไม่ต้องเปิดพอร์ตรับการเชื่อมต่อบนเครื่อง AI ภาพที่สร้างจะถูกส่งไปเก็บบน Backend ผ่าน API โดยไม่ต้องแชร์โฟลเดอร์หรือไฟล์ SQLite

## ตั้งค่าและเริ่ม Frontend

บนเครื่อง Frontend เปิด PowerShell ที่โฟลเดอร์โปรเจกต์:
=======
ไฟล์โมเดลไม่ถูก sync จาก Git จึงต้องคัดลอกหรือดาวน์โหลดแยกเอง ถ้าใช้โฟลเดอร์อื่น ให้กำหนด `AI_MODELS_DIR` ก่อนเริ่ม worker

## 4. เริ่ม Backend

บนเครื่อง Backend เปิด PowerShell ที่โฟลเดอร์โปรเจกต์ ตั้ง token แล้วเริ่มบริการ:

```powershell
$env:AI_WORKER_TOKEN = "ตั้ง-secret-เดียวกับเครื่อง-AI"
.\run_backend.bat
```

Backend รับการเชื่อมต่อที่ TCP port `8000` โดยค่าเริ่มต้น ตรวจสถานะได้ที่ `http://127.0.0.1:8000/api/health` บนเครื่อง Backend ปกติไม่ต้องตั้ง `PUBLIC_BASE_URL`; ถ้าใช้ reverse proxy หรือ URL ที่ browser เข้าถึงต่างจาก host ที่ Backend เห็น ให้ตั้งค่านี้เป็น URL ของ Backend ที่ browser เข้าถึงได้

## 5. เริ่ม AI Worker

บนเครื่อง AI ใช้ token เดียวกับ Backend และระบุ URL ที่เครื่อง AI ใช้เข้าถึง Backend:

```powershell
$env:AI_BACKEND_URL = "http://<IP-เครื่อง-backend>:8000"
$env:AI_WORKER_TOKEN = "ตั้ง-secret-เดียวกับเครื่อง-backend"
.\run_worker.bat
```

Worker เชื่อมต่อออกไปยัง Backend เอง จึงไม่ต้องเปิด inbound port บนเครื่อง AI และไม่ต้องแชร์ SQLite หรือโฟลเดอร์ผลลัพธ์

## 6. เริ่ม Frontend

บนเครื่อง Frontend:
>>>>>>> main

```powershell
$env:AI_BACKEND_URL = "http://<IP-เครื่อง-backend>:8000"
.\run_frontend.bat
```

<<<<<<< HEAD
เปิด `http://<IP-เครื่อง-frontend>:5500` ใน browser เครื่องที่เปิด browser ต้องเข้าถึงทั้ง Frontend และ Backend ได้ Frontend ใช้ Python standard library จึงไม่ต้องติดตั้ง pip packages หรือ Node.js เพิ่ม

## Firewall และเครือข่าย

- อนุญาต TCP port `8000` ให้เครื่อง Frontend และ AI Worker เชื่อมต่อเข้า Backend
- อนุญาต TCP port `5500` หาก browser อยู่คนละเครื่องกับ Frontend
- ทุกเครื่องต้องมองเห็นกันผ่าน LAN หรือ VPN; Worker ไม่ต้องเปิด inbound port
- ตั้ง `AI_WORKER_TOKEN` ให้ตรงกันระหว่าง Backend กับ Worker และอย่าเก็บ secret ไว้ใน Git

## รันทุกส่วนบนเครื่องเดียว

ใช้ `run_all.bat` เพื่อเริ่ม Backend, Frontend และ AI Worker ใน terminal แยกกัน สคริปต์ตั้งค่า `dev-secret` สำหรับการรันบนเครื่องเดียวเท่านั้น

## แก้ปัญหาเบื้องต้น

- **Worker ต่อ Backend ไม่ได้:** ตรวจ `AI_BACKEND_URL`, IP/พอร์ต `8000` และ Firewall
- **Backend ตอบ 401 หรือ Worker ไม่ claim งาน:** ตรวจว่า `AI_WORKER_TOKEN` ตรงกันทั้งสองเครื่อง
- **งานล้มเหลวเพราะไม่พบโมเดล:** ตรวจว่ามีไฟล์โมเดลอยู่ใน `AI_MODELS_DIR` บนเครื่อง Worker และชื่อไฟล์ตรงกับที่เลือก
- **หน้าเว็บติดต่อ Backend ไม่ได้:** ตรวจ `AI_BACKEND_URL` บนเครื่อง Frontend และให้ browser เข้าถึง Backend ได้โดยตรง
=======
เปิด `http://<IP-เครื่อง-frontend>:5500` ใน browser เครื่องที่เปิด browser ต้องเข้าถึงทั้ง Frontend ที่ port `5500` และ Backend ที่ port `8000` ได้ เปิดพอร์ตตามความจำเป็นใน Firewall

## รันทุกส่วนบนเครื่องเดียว

ใช้ `run_all.bat` เพื่อเปิด Backend, Frontend และ AI Worker ใน terminal แยกกัน ค่า `dev-secret` ในสคริปต์นี้มีไว้สำหรับรันบนเครื่องเดียวเท่านั้น หากแยกเครื่อง ต้องกำหนด secret ใหม่และตั้งค่าเดียวกันบน Backend กับ Worker อย่าเก็บ secret จริงไว้ใน Git

## แก้ปัญหาเบื้องต้น

- Worker ติดต่อ Backend ไม่ได้: ตรวจ `AI_BACKEND_URL`, IP, port `8000` และ Firewall
- Worker ไม่รับงานหรือ Backend ตอบ 401: ตรวจว่า `AI_WORKER_TOKEN` ตรงกันทั้งสองเครื่อง
- งานแจ้งว่าไม่พบโมเดล: ตรวจไฟล์ใน `AI_MODELS_DIR` บนเครื่อง AI และชื่อไฟล์ที่เลือก
- หน้าเว็บติดต่อ Backend ไม่ได้: ตรวจ `AI_BACKEND_URL` บนเครื่อง Frontend และให้ browser เข้าถึง Backend ได้โดยตรง
>>>>>>> main
