# AI Image Studio

โปรเจกต์ถูกแยกเป็น 4 ส่วน:

- `frontend/` หน้าเว็บสำหรับกรอก prompt และแสดงผลลัพธ์
- `backend/` FastAPI สำหรับรับคำขอสร้างภาพผ่าน REST API
- `ai/` worker แยก process สำหรับโหลดโมเดลและประมวลผลภาพ
- `database/` SQLite queue และประวัติงานสร้างภาพ

Backend และ AI worker ต้องรันบนเครื่องเดียวกัน เพราะใช้ไฟล์โมเดล โฟลเดอร์รูปผลลัพธ์ และ SQLite database ชุดเดียวกัน ส่วน frontend จะรันเครื่องเดียวกันหรืออีกเครื่องใน Wi-Fi ก็ได้

## เริ่มใช้งาน

เปิด terminal 3 หน้าต่างจากโฟลเดอร์หลัก `c:\proAi` และเปิดใช้งานแต่ละส่วนตามลำดับ

### ติดตั้งครั้งแรก

ต้องติดตั้ง Python แบบ 64-bit ที่ PyTorch รองรับก่อน จากนั้นสร้าง environment และติดตั้ง dependency ตามลำดับนี้ ถ้าใช้ GPU ให้เลือกคำสั่งติดตั้ง PyTorch ให้ตรงกับ CUDA/driver และ Python ที่เครื่องใช้จาก [ตัวเลือกติดตั้ง PyTorch](https://pytorch.org/get-started/locally/) ก่อนติดตั้ง requirements ของโปรเจกต์

สร้างและ activate environment ก่อน:

```powershell
cd c:\proAi
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

เลือกติดตั้ง PyTorch เพียงแบบเดียว ก่อนติดตั้ง requirements:

```powershell
# เครื่อง CPU
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

ถ้าใช้ NVIDIA GPU ให้ใช้คำสั่งที่เว็บไซต์ PyTorch สร้างให้ตามรุ่น CUDA แทนคำสั่ง CPU ด้านบน จากนั้นติดตั้งแพ็กเกจที่เหลือและ dependencies ของโปรเจกต์:

```powershell
pip install -r backend\requirements.txt
```

ทำขั้นตอนสร้าง environment และติดตั้งแพ็กเกจครั้งแรกครั้งเดียวเท่านั้น SQLite เป็นส่วนหนึ่งของ Python ไม่ต้องติดตั้ง database server

### คำสั่งรันหลังติดตั้ง (เปิด PowerShell 3 หน้าต่าง)

รันแต่ละชุดคำสั่งใน terminal แยกกัน และเปิด terminal ทั้งสามค้างไว้ระหว่างใช้งาน

#### Terminal 1: Backend API

```powershell
cd c:\proAi
.\backend\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --port 8000
```

#### Terminal 2: AI worker

```powershell
cd c:\proAi
.\backend\.venv\Scripts\Activate.ps1
python -m ai.worker
```

#### Terminal 3: Frontend

```powershell
cd c:\proAi\frontend
python ai_image_frontend.py
```

เปิด `http://127.0.0.1:5500` ในเบราว์เซอร์ Frontend ใช้ Python standard library ไม่ต้อง `pip install` เพิ่ม

## จุดตั้งค่า IP และเหตุผล

หา IPv4 ของเครื่องที่รัน backend ด้วย `ipconfig` แล้วดูอะแดปเตอร์ Wi-Fi ที่ใช้งานอยู่ IP อาจเปลี่ยนเมื่อเปลี่ยนเครือข่ายหรือ router แจก IP ใหม่

| ค่า/ตำแหน่ง | ใช้ทำอะไร | ต้องตั้งเมื่อไร |
| --- | --- | --- |
| `uvicorn ... --host 0.0.0.0` | ให้ backend รับ request จากเครื่องอื่น ไม่ใช่แค่เครื่องตัวเอง | เมื่อ frontend อยู่คนละเครื่อง |
| `--api-url http://<IP-backend>:8000` | บอก frontend ว่าจะส่ง request ไป backend เครื่องไหน | เมื่อ backend ไม่ได้อยู่เครื่องเดียวกับ frontend หรือใช้ IP แทน localhost |
| `ai_image_frontend.py --host 0.0.0.0` | ให้ frontend server รับ browser จากเครื่องอื่น | เมื่อเปิดหน้าเว็บผ่าน IP จากอุปกรณ์อื่น |
| `PUBLIC_BASE_URL` ใน `backend/main.py` | บังคับ base URL ที่ backend ส่งกลับสำหรับรูปผลลัพธ์ | ปกติไม่ต้องตั้ง; ใช้เมื่อมี reverse proxy หรือ URL สาธารณะต่างจาก URL ที่เรียก API |
| `AI_IMAGE_DATABASE` | เปลี่ยนตำแหน่งไฟล์ SQLite ไม่ใช่ IP | ปกติไม่ต้องตั้ง; หากเปลี่ยน ต้องให้ backend และ AI worker ใช้ path เดียวกัน |

`0.0.0.0` เป็น address สำหรับ bind ให้ server ฟังทุก network interface ไม่ใช่ IP ที่นำไปกรอกใน browser ส่วน IP ใน URL ต้องเป็น IPv4 จริงของเครื่องที่รัน frontend/backend นั้น และเครื่องลูกข่ายต้องอยู่เครือข่ายที่ติดต่อกันได้

### เปิดให้เครื่องอื่นใน Wi-Fi ใช้งาน

1. บนเครื่องที่รัน backend เปิด PowerShell แล้วดู IP:

	```powershell
	ipconfig
	```

	ใช้ค่า `IPv4 Address` ของอะแดปเตอร์ที่เชื่อม Wi-Fi เช่น `172.20.5.197`

2. เปิด backend โดย bind ให้เครื่องอื่นเข้าถึงได้:

	```powershell
	cd c:\proAi
	.\backend\.venv\Scripts\Activate.ps1
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
	```

3. เปิด AI worker ใน terminal อีกหน้าต่าง บนเครื่องเดียวกับ backend:

	```powershell
	cd c:\proAi
	.\backend\.venv\Scripts\Activate.ps1
	python -m ai.worker
	```

4. รัน frontend แบบไฟล์ Python เดียว:

	```powershell
	cd c:\proAi\frontend
	python ai_image_frontend.py --api-url http://172.20.5.197:8000 --host 0.0.0.0 --port 5500
	```

	เปลี่ยน IP ตัวอย่างให้เป็น IP ของเครื่อง backend จริง จากอุปกรณ์อื่นเปิด `http://172.20.5.197:5500` ถ้า frontend อยู่คนละเครื่อง ให้ใช้ IP ของเครื่อง frontend ใน URL ที่เปิด browser แทน

5. ทดสอบ backend โดยเปิด URL นี้จากเครื่อง client:

	```text
	http://172.20.5.197:8000/api/health
	```

	ควรได้สถานะ `ok` หากเข้าไม่ได้ ให้ตรวจ Windows Firewall ว่าอนุญาตพอร์ต `8000` และ `5500` ในเครือข่าย Private แล้ว

ถ้า frontend/backend อยู่เครื่องเดียวกัน รัน `python ai_image_frontend.py` ได้โดยไม่ต้องระบุ `--api-url` และเปิดที่ `http://127.0.0.1:5500` ส่วน SQLite ถูกสร้างอัตโนมัติที่ `database/ai_image_studio.sqlite3`

## ดาวน์โหลดโมเดลจาก Civitai

Backend มี endpoint สำหรับค้นหาและดาวน์โหลดโมเดลจาก Civitai และเก็บโมเดลไว้ใน `backend/models/` ส่วน frontend ปัจจุบันแสดงรายการไฟล์โมเดลที่มีในโฟลเดอร์นี้เพื่อเลือกก่อนสร้างภาพ

ตั้งค่า API key เฉพาะเมื่อ URL ของ Civitai ต้องยืนยันตัวตน:

```powershell
$env:CIVITAI_API_KEY = "ใส่คีย์ของคุณใน terminal เท่านั้น"
```

เมื่อเลือกโมเดลในหน้าเว็บแล้ว `POST /api/generate` จะโหลด checkpoint ด้วย `StableDiffusionPipeline.from_single_file`, ใช้ GPU CUDA ถ้ามี และบันทึกภาพจริงไว้ที่ `backend/outputs/` สามารถเปิดดูผ่าน `/outputs/...` ได้ หากยังไม่ได้ติดตั้ง PyTorch/Diffusers API จะตอบ `501` พร้อมข้อความที่บอกว่าต้องติดตั้งอะไร
