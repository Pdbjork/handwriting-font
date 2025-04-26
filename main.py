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
