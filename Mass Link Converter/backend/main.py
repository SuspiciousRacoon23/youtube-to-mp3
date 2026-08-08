from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import uuid
import os
import shutil
import time
from worker import process_batch

app = FastAPI(title="Mass Link Converter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BatchRequest(BaseModel):
    urls: List[str]
    format: str = "mp3"

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, batch_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[batch_id] = websocket

    def disconnect(self, batch_id: str):
        if batch_id in self.active_connections:
            del self.active_connections[batch_id]

    async def send_message(self, message: dict, batch_id: str):
        if batch_id in self.active_connections:
            await self.active_connections[batch_id].send_json(message)

manager = ConnectionManager()

@app.post("/api/batch")
async def create_batch(request: BatchRequest):
    batch_id = str(uuid.uuid4())
    process_batch.delay(batch_id, request.urls, request.format)
    return {"batch_id": batch_id, "status": "processing"}

@app.get("/api/batch/{batch_id}")
async def get_batch_status(batch_id: str):
    return {"batch_id": batch_id, "status": "In progress"}

@app.websocket("/ws/progress/{batch_id}")
async def websocket_endpoint(websocket: WebSocket, batch_id: str):
    await manager.connect(batch_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(batch_id)

@app.post("/api/internal/progress")
async def internal_progress(data: dict):
    batch_id = data.get("batch_id")
    if batch_id:
        await manager.send_message(data, batch_id)
    return {"ok": True}

def cleanup_batch(batch_id: str):
    time.sleep(3600) # wait 1 hour before deleting
    dir_path = f"downloads/{batch_id}"
    zip_path = f"downloads/{batch_id}.zip"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    if os.path.exists(zip_path):
        os.remove(zip_path)

@app.get("/api/download/{batch_id}")
async def download_batch(batch_id: str, background_tasks: BackgroundTasks):
    dir_path = f"downloads/{batch_id}"
    if not os.path.exists(dir_path):
        return {"error": "Batch not found"}
        
    zip_path = f"downloads/{batch_id}.zip"
    if not os.path.exists(zip_path):
        shutil.make_archive(f"downloads/{batch_id}", 'zip', dir_path)
        
    # Schedule cleanup in the background
    background_tasks.add_task(cleanup_batch, batch_id)
    
    return FileResponse(zip_path, media_type="application/zip", filename=f"Batch_{batch_id}.zip")
