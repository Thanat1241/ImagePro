# Database

Backend ใช้ SQLite เก็บคิวงานและประวัติไว้ที่ `database/ai_image_studio.sqlite3` โดยค่าเริ่มต้น กำหนด path อื่นได้ด้วย `AI_IMAGE_DATABASE` บนเครื่อง backend

AI worker ติดต่อคิวผ่าน backend HTTP API จึงไม่ต้องอ่านหรือเขียนไฟล์ SQLite และไม่ต้องแชร์ฐานข้อมูลข้ามเครื่อง
