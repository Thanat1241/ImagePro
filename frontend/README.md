# Frontend

`ai_image_frontend.py` รวมหน้าเว็บ, CSS และ browser code ไว้ในไฟล์ Python เดียว ใช้ Python standard library จึงไม่ต้องติดตั้ง pip package เพิ่ม แต่ต้องมี backend และ AI worker ทำงานอยู่เพื่อสร้างภาพ

## รันบนเครื่องเดียวกับ Backend

```powershell
cd c:\proAi\frontend
python ai_image_frontend.py
```

เปิด `http://127.0.0.1:5500`

## รันบนเครื่องอื่น หรือเปิดให้เครื่องอื่นเข้าหน้าเว็บ

`--api-url` คือ URL ของ backend ที่ frontend จะเรียก ต้องใช้ IP จริงของเครื่อง backend เมื่ออยู่คนละเครื่อง ส่วน `--host 0.0.0.0` ทำให้ frontend รับ browser จาก network ได้:

```powershell
cd c:\proAi\frontend
python ai_image_frontend.py --api-url http://172.20.5.197:8000 --host 0.0.0.0 --port 5500
```

เปลี่ยน `172.20.5.197` เป็น IP ปัจจุบันของเครื่อง backend ซึ่งดูได้ด้วย `ipconfig` ถ้าเปิด browser บนเครื่องอื่น ให้เข้า `http://<IP-เครื่องที่รัน-frontend>:5500` และอนุญาต Firewall สำหรับพอร์ต `5500` หากถูกบล็อก