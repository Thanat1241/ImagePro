# Frontend

`ai_image_frontend.py` ให้บริการหน้าเว็บแบบ standalone โดยใช้ Python standard library. Browser ติดต่อ backend โดยตรงเพื่อส่งงาน ตรวจสถานะ และโหลดภาพ

## รันบนเครื่องแยก

จาก PowerShell ในโฟลเดอร์โปรเจกต์:

```powershell
$env:AI_BACKEND_URL = "http://<backend-address>:8000"
.\run_frontend.bat
```

เปิด `http://<frontend-address>:5500` จาก browser. ค่าเริ่มต้นของสคริปต์คือฟังทุก network interface ที่พอร์ต `5500`; ตั้ง `FRONTEND_HOST` และ `FRONTEND_PORT` เพื่อเปลี่ยนค่า

เครื่องที่เปิด browser ต้องเข้าถึงทั้ง frontend ที่พอร์ต TCP `5500` และ backend ที่พอร์ต TCP `8000`. หากรัน frontend และ backend บนเครื่องเดียวกัน ใช้ `http://127.0.0.1:8000` เป็น `AI_BACKEND_URL` ได้

รันโดยตรงได้ด้วย `python frontend\ai_image_frontend.py --api-url http://<backend-address>:8000 --host 0.0.0.0 --port 5500`.
