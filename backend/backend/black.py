import os
import uuid
from pathlib import Path

import psycopg2
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
INPUT_DIR = UPLOAD_DIR / "inputs"
OUTPUT_DIR = UPLOAD_DIR / "outputs"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE
CORS(app)


def get_db_connection():
	return psycopg2.connect(
		host=os.getenv("DB_HOST", "localhost"),
		port=os.getenv("DB_PORT", "5432"),
		dbname=os.getenv("DB_NAME", "postgres"),
		user=os.getenv("DB_USER", "postgres"),
		password=os.getenv("DB_PASSWORD", ""),
	)


def json_body():
	data = request.get_json(silent=True)
	return data if isinstance(data, dict) else {}


@app.errorhandler(psycopg2.Error)
def handle_database_error(error):
	app.logger.error("Database request failed: %s", error)
	return jsonify({"error": "ไม่สามารถเชื่อมต่อฐานข้อมูลได้"}), 503


@app.errorhandler(413)
def handle_large_upload(_error):
	return jsonify({"error": "ไฟล์ต้องมีขนาดไม่เกิน 10 MB"}), 413


@app.route("/health", methods=["GET"])
def health():
	return jsonify({"status": "ok"}), 200


@app.route("/api/register", methods=["POST"])
def register():
	data = json_body()
	username = str(data.get("username", "")).strip()
	email = str(data.get("email", "")).strip().lower()
	password = data.get("password")

	if not username or not email or not isinstance(password, str) or not password:
		return jsonify({"error": "กรุณากรอกข้อมูลให้ครบถ้วน"}), 400

	with get_db_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
			if cursor.fetchone():
				return jsonify({"error": "อีเมลนี้ถูกใช้งานไปแล้ว"}), 409

			cursor.execute(
				"""INSERT INTO users (username, email, password_hash)
				   VALUES (%s, %s, %s) RETURNING id""",
				(username, email, generate_password_hash(password)),
			)
			user_id = cursor.fetchone()[0]

	return jsonify({"message": "สมัครสมาชิกสำเร็จ", "user_id": user_id}), 201


@app.route("/api/login", methods=["POST"])
def login():
	data = json_body()
	email = str(data.get("email", "")).strip().lower()
	password = data.get("password")
	if not email or not isinstance(password, str):
		return jsonify({"error": "กรุณากรอกอีเมลและรหัสผ่าน"}), 400

	with get_db_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(
				"SELECT id, password_hash FROM users WHERE email = %s", (email,)
			)
			user = cursor.fetchone()

	if not user or not check_password_hash(user[1], password):
		return jsonify({"error": "อีเมลหรือรหัสผ่านไม่ถูกต้อง"}), 401
	return jsonify({"message": "Login successful", "user_id": user[0]}), 200


@app.route("/api/tasks", methods=["POST"])
def create_task():
	if request.mimetype == "multipart/form-data":
		user_id = request.form.get("user_id", type=int)
		task_type = request.form.get("task_type", "").strip()
		prompt_text = request.form.get("prompt_text")
		input_image_path = None

		uploaded_file = request.files.get("image")
		if uploaded_file and uploaded_file.filename:
			original_name = secure_filename(uploaded_file.filename)
			if not original_name:
				return jsonify({"error": "ชื่อไฟล์ไม่ถูกต้อง"}), 400
			filename = f"{uuid.uuid4().hex}_{original_name}"
			uploaded_file.save(INPUT_DIR / filename)
			input_image_path = f"/uploads/inputs/{filename}"
	else:
		data = json_body()
		user_id = data.get("user_id")
		task_type = str(data.get("task_type", "")).strip()
		prompt_text = data.get("prompt_text")
		input_image_path = None

	if not user_id or not task_type:
		return jsonify({"error": "ข้อมูลไม่ครบถ้วน"}), 400
	try:
		user_id = int(user_id)
	except (TypeError, ValueError):
		return jsonify({"error": "user_id ไม่ถูกต้อง"}), 400

	with get_db_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(
				"""INSERT INTO image_tasks
				   (user_id, task_type, prompt_text, input_image_path, status)
				   VALUES (%s, %s, %s, %s, 'pending') RETURNING id""",
				(user_id, task_type, prompt_text, input_image_path),
			)
			task_id = cursor.fetchone()[0]

	return jsonify({"message": "สร้างคิวงานสำเร็จ", "task_id": task_id}), 201


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
	user_id = request.args.get("user_id", type=int)
	try:
		limit = int(request.args.get("limit", "50"))
	except ValueError:
		return jsonify({"error": "limit ต้องเป็นตัวเลข"}), 400
	limit = max(1, min(limit, 100))
	if not user_id:
		return jsonify({"error": "ต้องระบุ user_id"}), 400

	with get_db_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(
				"""SELECT id, task_type, status, prompt_text, input_image_path,
						  output_image_path, created_at, updated_at
				   FROM image_tasks WHERE user_id = %s
				   ORDER BY created_at DESC LIMIT %s""",
				(user_id, limit),
			)
			rows = cursor.fetchall()

	tasks = [
		{
			"task_id": row[0],
			"task_type": row[1],
			"status": row[2],
			"prompt_text": row[3],
			"input_image_path": row[4],
			"output_image_path": row[5],
			"created_at": row[6].isoformat() if row[6] else None,
			"updated_at": row[7].isoformat() if row[7] else None,
		}
		for row in rows
	]
	return jsonify({"tasks": tasks}), 200


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task_status(task_id):
	with get_db_connection() as connection:
		with connection.cursor() as cursor:
			cursor.execute(
				"SELECT status, output_image_path FROM image_tasks WHERE id = %s",
				(task_id,),
			)
			task = cursor.fetchone()

	if not task:
		return jsonify({"error": "ไม่พบงานนี้"}), 404
	return jsonify(
		{
			"task_id": task_id,
			"status": task[0],
			"output_image_path": task[1],
		}
	), 200


@app.route("/uploads/<folder>/<path:filename>", methods=["GET"])
def serve_image(folder, filename):
	if folder not in {"inputs", "outputs"}:
		return jsonify({"error": "ไม่พบไฟล์"}), 404
	directory = INPUT_DIR if folder == "inputs" else OUTPUT_DIR
	return send_from_directory(directory, filename)


if __name__ == "__main__":
	app.run(
		host=os.getenv("HOST", "0.0.0.0"),
		port=int(os.getenv("PORT", "5000")),
		debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
	)
