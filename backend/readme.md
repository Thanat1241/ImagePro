# Backend

Flask API for user accounts and image-processing task queues. The service stores uploaded input images in `backend/uploads/inputs` and serves input/output images under `/uploads/`.

## Requirements

- Python 3.10 or newer
- PostgreSQL with `users` and `image_tasks` tables

Install dependencies from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

## Database configuration

Set these environment variables before starting the API:

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"
$env:DB_NAME = "postgres"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "your-database-password"
```

The database must provide `users(id, username, email, password_hash)` and `image_tasks(id, user_id, task_type, prompt_text, input_image_path, output_image_path, status, created_at, updated_at)`. Passwords registered through this API are stored as hashes.

## Run and check

Run from the project root:

```powershell
.\.venv\Scripts\python.exe backend\backend\black.py
```

The API listens on `http://127.0.0.1:5000` by default. Check `GET /health` for `{"status":"ok"}`. Set `HOST`, `PORT`, and `FLASK_DEBUG` to override the server settings.

## Endpoints

- `POST /api/register` - create an account with JSON `username`, `email`, and `password`.
- `POST /api/login` - authenticate with JSON `email` and `password`.
- `POST /api/tasks` - create a task using JSON fields or `multipart/form-data` with an optional `image` file.
- `GET /api/tasks?user_id=<id>&limit=50` - list a user's tasks.
- `GET /api/tasks/<task_id>` - get task status and output image path.
- `GET /uploads/<inputs|outputs>/<filename>` - retrieve an uploaded or generated image.