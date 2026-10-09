# AI Worker

โฟลเดอร์นี้แยกงานโหลดโมเดลและสร้างภาพออกจาก Backend API โดย `worker.py` อ่านงานจาก SQLite, เรียก `image_generator.py` ทำ inference และเขียนสถานะ/ผลลัพธ์กลับ database

## สิ่งที่ต้องติดตั้ง

- ใช้ Python virtual environment เดียวกับ backend
- ติดตั้ง PyTorch ให้ตรงกับ CPU หรือ CUDA ของเครื่อง แล้วติดตั้งรายการใน `backend/requirements.txt` ตาม [README หลัก](../README.md#ติดตั้งครั้งแรก)
- วางไฟล์โมเดลไว้ใน `backend/models/`

AI worker ไม่มี IP ที่ต้องแก้ในไฟล์ ถ้ารัน Backend และ worker บนเครื่องเดียวกันจะใช้ database และโฟลเดอร์โมเดลชุดเดียวกัน

## วิธีรัน

```powershell
cd c:\proAi
.\backend\.venv\Scripts\Activate.ps1
python -m ai.worker
```

คง terminal นี้เปิดไว้ระหว่างใช้งาน worker อ่านโมเดลจาก `backend/models/` และบันทึกรูปใน `backend/outputs/`