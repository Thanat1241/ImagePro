# AI Worker

โฟลเดอร์นี้แยกงานโหลดโมเดลและสร้างภาพออกจาก Backend API โดย `worker.py` อ่านงานจาก SQLite, เรียก `image_generator.py` ทำ inference และเขียนสถานะ/ผลลัพธ์กลับ database

## สิ่งที่ต้องติดตั้ง

- ใช้ Python virtual environment เดียวกับ backend
- ติดตั้ง PyTorch ให้ตรงกับ CPU หรือ CUDA ของเครื่อง แล้วติดตั้งรายการใน `backend/requirements.txt` ตาม [README หลัก](../README.md#ติดตั้งครั้งแรก)
- วางไฟล์โมเดลไว้ใน `backend/models/`

AI worker ไม่มี IP ที่ต้องแก้ในไฟล์ ถ้ารัน Backend และ worker บนเครื่องเดียวกันจะใช้ database และโฟลเดอร์โมเดลชุดเดียวกัน

## วิธีรันแบบแยกเครื่อง

เมื่อ AI worker อยู่คนละเครื่องจาก backend ให้ตั้ง environment variables ด้านล่างก่อนรัน:

```powershell
$env:AI_IMAGE_DATABASE = "\\server\share\ai_image_studio.sqlite3"
$env:AI_MODELS_DIR = "\\server\share\models"
$env:AI_OUTPUTS_DIR = "\\server\share\outputs"
$env:PUBLIC_BASE_URL = "http://192.168.1.20:8000"
python -m ai.worker
```

ถ้ารันบนเครื่องเดียวกัน ก็ไม่จำเป็นต้องตั้งค่าเพิ่มเติม เพราะจะใช้ค่า default เป็น `backend/models` และ `backend/outputs`

## วิธีรัน

```powershell
cd c:\proAi
.\backend\.venv\Scripts\Activate.ps1
python -m ai.worker
```

คง terminal นี้เปิดไว้ระหว่างใช้งาน worker อ่านโมเดลจาก shared model directory และบันทึกรูปใน shared output directory