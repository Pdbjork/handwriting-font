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

# Redis client
redis_client = redis.Redis(host="redis", port=6379, db=0)

@app.get("/template")
def get_template():
    # returns printable PNG/PDF grid
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "assets", "template.pdf")
    if not os.path.exists(template_path):
        return {"error": "Template not found"}
    return FileResponse(template_path)

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
    try:
        while True:
            data = redis_client.hget("jobs", job_id)  # Returns bytes
            if data:
                # Decode bytes to string, then parse JSON
                status = json.loads(data.decode('utf-8'))
                await ws.send_json(status)
                if status.get("state") == "DONE":
                    break
            else:
                # Job not found yet, send waiting status
                await ws.send_json({"state": "WAITING"})
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error for job {job_id}: {e}")
        await ws.close()

# Serve frontend in production (mount last so routes take precedence)
if os.path.exists("/static"):
    app.mount("/", StaticFiles(directory="/static", html=True), name="static")
