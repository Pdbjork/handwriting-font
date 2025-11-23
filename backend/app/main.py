from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from uuid import uuid4
from .celery_app import celery_app
from starlette.websockets import WebSocket
from fastapi.staticfiles import StaticFiles
import os
import redis
import asyncio
import json

app = FastAPI()

# Ensure generated directory exists
os.makedirs("backend/app/generated", exist_ok=True)
app.mount("/download", StaticFiles(directory="backend/app/generated"), name="download")

# Serve frontend in production
if os.path.exists("/static"):
    app.mount("/", StaticFiles(directory="/static", html=True), name="static")

# Redis client
redis_client = redis.Redis(host="redis", port=6379, db=0)

@app.get("/template")
def get_template():
    # returns printable PNG/PDF grid
    # Ensure assets directory exists
    return FileResponse("backend/app/assets/template.pdf")

@app.post("/upload")
async def upload(sample: UploadFile):
    job_id = str(uuid4())
    # Read file content
    content = await sample.read()
    celery_app.send_task("tasks.build_font", args=[job_id, content])
    return {"job_id": job_id}

@app.websocket("/ws/{job_id}")
async def ws_status(ws: WebSocket, job_id: str):
    await ws.accept()
    while True:
        data = redis_client.hget("jobs", job_id)  # set by Celery task
        if data:
            status = json.loads(data)
            await ws.send_json(status)
            if status.get("state") == "DONE":
                break
        await asyncio.sleep(1)
