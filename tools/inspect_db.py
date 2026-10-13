import sqlite3

DB = r"D:\Git\ImagePro\database\ai_image_studio.sqlite3"
conn = sqlite3.connect(DB)
cur = conn.cursor()
print("DB:", DB)
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("tables:", cur.fetchall())
try:
    rows = cur.execute("SELECT * FROM generation_jobs").fetchall()
    print("rows count:", len(rows))
    if rows:
        cols = [d[0] for d in cur.description]
        for r in rows:
            print(dict(zip(cols, r)))
except Exception as e:
    print("error selecting generation_jobs:", e)
finally:
    conn.close()
