# Database

โปรเจกต์ใช้ SQLite เป็นที่เก็บคิวงานและประวัติ Backend กับ AI worker ใช้ไฟล์ฐานข้อมูลร่วมกัน โดยไม่ต้องติดตั้ง PostgreSQL/MySQL หรือเปิด database server

- `schema.sql` สร้างตาราง job และ index โดยไม่ลบข้อมูลเดิม
- `store.py` จัดการเพิ่มงาน, claim งานแบบ transaction, อัปเดตสถานะ และอ่านประวัติ
- `ai_image_studio.sqlite3` ถูกสร้างอัตโนมัติเมื่อ backend หรือ worker เริ่มทำงาน

ไม่มี IP ของ database ให้แก้ เพราะ SQLite เป็นไฟล์ในเครื่อง ค่าเริ่มต้นคือ `database/ai_image_studio.sqlite3` หากต้องย้ายไฟล์ ให้ตั้ง `AI_IMAGE_DATABASE` เป็น path เดียวกันใน terminal ที่รัน backend และ AI worker และตรวจให้ทั้งสอง process ใช้ไฟล์โมเดล/ผลลัพธ์ร่วมกันด้วย