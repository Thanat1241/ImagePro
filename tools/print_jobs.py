import json
from database import store

jobs = store.list_jobs(200)
print(json.dumps(jobs, ensure_ascii=False, indent=2))
