# handwriting-font
AI-assisted browser-based handwriting font generator
# ✍️ Handwriting‑Font Generator

A browser‑based tool that lets anyone upload (or draw) their handwriting and instantly download a fully installable `.ttf / .woff` font.\
Built with **FastAPI + Celery + React (Vite)** and shipped as a single Docker stack.

---

\## Quick start

```bash
# 1) clone your fork
$ git clone git@github.com:<your‑user>/handwriting-font-generator.git && cd handwriting-font-generator

# 2) spin up the full stack (API, worker, Redis, front‑end)
$ docker compose up --build
# Visit http://localhost:5173
```

---

\## Directory layout

```
📦 handwriting-font-generator/
 ├─ backend/
 │   ├─ app/
 │   │   ├─ main.py        # FastAPI entrypoint
 │   │   ├─ celery_app.py  # Celery factory
 │   │   └─ services/
 │   │       ├─ tracing.py # OpenCV → Potrace bitmap→SVG
 │   │       └─ fontbuild.py # fontTools pipeline
 │   ├─ worker.py          # starts celery worker
 │   └─ requirements.txt
 ├─ frontend/
 │   ├─ src/
 │   │   └─ …              # React + TS + Tailwind
 │   ├─ index.html
 │   └─ package.json
 ├─ docker-compose.yml
 ├─ Dockerfile
 └─ .github/workflows/ci.yml
```

---

\## Core components

### 1 ▪ FastAPI (`backend/app/main.py`)

```python
from fastapi import FastAPI, UploadFile, BackgroundTasks
from uuid import uuid4
from .celery_app import celery_app
from starlette.websockets import WebSocket

app = FastAPI()

@app.get("/template")
def get_template():
    # returns printable PNG/PDF grid
    return FileResponse("assets/template.pdf")

@app.post("/upload")
async def upload(sample: UploadFile):
    job_id = str(uuid4())
    celery_app.send_task("tasks.build_font", args=[job_id, await sample.read()])
    return {"job_id": job_id}

@app.websocket("/ws/{job_id}")
async def ws_status(ws: WebSocket, job_id: str):
    await ws.accept()
    while True:
        status = redis.hget("jobs", job_id)  # set by Celery task
        await ws.send_json(status)
        if status.get("state") == "DONE":
            break
        await asyncio.sleep(1)
```

### 2 ▪ Celery worker (`backend/worker.py`)

```python
from .celery_app import celery_app
from .services import tracing, fontbuild
import redis, json

@celery_app.task(name="tasks.build_font")
def build_font(job_id: str, img_bytes: bytes):
    redis_client = redis.Redis(host="redis", port=6379)
    redis_client.hset("jobs", job_id, json.dumps({"state":"TRACING"}))
    svg_map = tracing.extract_glyphs(img_bytes)
    redis_client.hset("jobs", job_id, json.dumps({"state":"BUILDING"}))
    ttf_path = fontbuild.make_font(svg_map, job_id)
    redis_client.hset("jobs", job_id, json.dumps({"state":"DONE", "path": ttf_path}))
```

### 3 ▪ React front‑end (`frontend/src/App.tsx`)

```tsx
export default function App() {
  const [jobId,setJobId] = useState<string>()
  const [progress,setProgress] = useState<string>()

  const handleUpload = async (file:File) => {
    const res = await fetch("/api/upload", {method:"POST",body:file})
    const {job_id}=await res.json();
    setJobId(job_id);
    const ws = new WebSocket(`ws://${location.host}/api/ws/${job_id}`);
    ws.onmessage = (ev)=>{
      const data = JSON.parse(ev.data);
      setProgress(data.state);
      if(data.state==="DONE") window.open(data.path,"_blank");
    };
  };
}
```

---

\## Docker & Compose `docker-compose.yml`

```yaml
version: "3.9"
services:
  api:
    build: .
    command: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
    depends_on: [redis]
  worker:
    build: .
    command: celery -A backend.worker worker -l info
    depends_on: [redis]
  redis:
    image: redis:7-alpine
  web:
    build: ./frontend
    command: npm run dev
    ports: ["5173:5173"]
```

`Dockerfile` (multi‑stage, root dir):

```dockerfile
FROM python:3.12-slim AS backend
WORKDIR /code
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend ./backend

FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend ./
RUN npm ci && npm run build

FROM python:3.12-slim
COPY --from=backend /code /code
COPY --from=frontend /app/dist /static
CMD ["uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000"]
```

---

\## CI / CD — GitHub Actions `.github/workflows/ci.yml`

```yaml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & test
        run: docker compose run --rm api pytest
```

Add a second workflow for Docker Hub or GHCR publish when you’re ready.

---

\## Roadmap

-

---

\### License MIT © 2025 Peter Bjork

