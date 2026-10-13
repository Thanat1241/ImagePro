# AI Worker

AI worker รัน inference และเชื่อมต่อ backend ผ่าน HTTP API จึงติดตั้งบนเครื่องที่มี GPU/โมเดลแยกจาก backend ได้ ไม่ต้องใช้ SQLite หรือโฟลเดอร์ผลลัพธ์ร่วมกัน

## เตรียมเครื่อง AI

ติดตั้ง Python packages บนเครื่อง AI โดยเลือก PyTorch build ให้ตรงกับ CPU หรือ CUDA ของเครื่องก่อน:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

วางไฟล์โมเดล เช่น `meinamix_v12Final.safetensors` ไว้ใน `ai/models/` บนเครื่อง AI หรือกำหนดโฟลเดอร์อื่นผ่าน `AI_MODELS_DIR`.

## รัน worker

จาก PowerShell ที่โฟลเดอร์โปรเจกต์:

```powershell
$env:AI_BACKEND_URL = "http://<backend-address>:8000"
$env:AI_WORKER_TOKEN = "replace-with-the-same-long-random-secret"
.\run_worker.bat
```

`AI_WORKER_TOKEN` ต้องตรงกับค่าบน backend. `AI_OUTPUTS_DIR` ใช้เป็นโฟลเดอร์ชั่วคราวในเครื่อง AI; worker จะส่งไฟล์ภาพไปเก็บที่ backend เอง ไม่ต้องแชร์โฟลเดอร์นี้ผ่าน network.

พอร์ต TCP `8000` ของ backend ต้องเข้าถึงได้จากเครื่อง AI ส่วน worker ไม่ต้องเปิดพอร์ต inbound. ถ้า backend ยังไม่ทำงาน worker จะลองเชื่อมต่อใหม่เป็นระยะ
