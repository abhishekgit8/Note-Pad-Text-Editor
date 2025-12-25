from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Note
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime
import asyncio
from enum import Enum


class Status(str, Enum):
    active = "active"
    hold = "hold"
    finished = "finished"


class NoteOut(BaseModel):
    id: str
    title: str
    content: str
    priority: int
    status: Status
    reminder_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

app = FastAPI()

# Configure CORS for development (allow frontend origin)
origins = [
    "https://note-kanban-m28kpy6ne-abhisheks-projects-08f6a222.vercel.app/",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple WebSocket connection manager to broadcast changes to clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # send_json concurrently to all connections
        coros = [conn.send_json(message) for conn in self.active_connections]
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

manager = ConnectionManager()

# Background task that broadcasts a 'tick' message every second to connected clients
async def _broadcast_tick_loop():
    try:
        while True:
            await asyncio.sleep(1)
            if not manager.active_connections:
                continue
            now = datetime.utcnow().isoformat()
            await manager.broadcast({"action": "tick", "now": now})
    except asyncio.CancelledError:
        # task cancelled on shutdown
        return

# Start the tick loop on application startup and cancel it on shutdown
@app.on_event("startup")
async def _start_tick_loop():
    app.state._tick_task = asyncio.create_task(_broadcast_tick_loop())

@app.on_event("shutdown")
async def _stop_tick_loop():
    task = getattr(app.state, "_tick_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def note_to_dict(note_obj):
    return {
        "id": str(note_obj.id),
        "title": note_obj.title,
        "content": note_obj.content,
        "priority": note_obj.priority,
        "status": note_obj.status,
        "reminder_time": note_obj.reminder_time.isoformat() if note_obj.reminder_time else None,
        "created_at": note_obj.created_at.isoformat() if getattr(note_obj, 'created_at', None) else None,
        "updated_at": note_obj.updated_at.isoformat() if getattr(note_obj, 'updated_at', None) else None,
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # send an initial sync with current notes so the client has immediate state
    db = SessionLocal()
    try:
        notes = db.query(Note).order_by(Note.priority.asc()).all()
        await websocket.send_json({"action": "sync", "notes": [note_to_dict(n) for n in notes]})
    finally:
        db.close()

    try:
        while True:
            # keep the connection open; clients may send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


class NotePatch(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[Status] = None
    reminder_time: Optional[datetime] = None

    @validator("reminder_time", pre=True)
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

    @validator("priority")
    def priority_positive(cls, v):
        if v is None:
            return v
        if v < 1:
            raise ValueError("priority must be >= 1")
        return v

class NoteSchema(BaseModel):
    title: str
    content: str
    priority: int
    status: Status
    reminder_time: datetime | None = None

    @validator("reminder_time", pre=True)
    def empty_string_to_none(cls, v):
        # Accept empty strings from clients (e.g., Angular date input) and convert to None
        if v == "":
            return None
        return v

    @validator("priority")
    def priority_positive(cls, v):
        if v < 1:
            raise ValueError("priority must be >= 1")
        return v

@app.get("/notes", response_model=List[NoteOut])
def get_notes(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Note)
    if status:
        query = query.filter(Note.status == status)
    notes = query.order_by(Note.priority.asc()).all()
    return [note_to_dict(n) for n in notes]

@app.post("/notes", response_model=NoteOut)
def create_note(note: NoteSchema, db: Session = Depends(get_db)):
    new_note = Note(**note.dict())
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    # broadcast create event (schedule asynchronously / fallback to sync in test env)
    def _payload(note_obj):
        return {"action": "create", "note": {
            "id": str(note_obj.id),
            "title": note_obj.title,
            "content": note_obj.content,
            "priority": note_obj.priority,
            "status": note_obj.status,
            "reminder_time": note_obj.reminder_time.isoformat() if note_obj.reminder_time else None,
            "created_at": note_obj.created_at.isoformat() if getattr(note_obj, 'created_at', None) else None,
            "updated_at": note_obj.updated_at.isoformat() if getattr(note_obj, 'updated_at', None) else None
        }}
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(manager.broadcast(_payload(new_note)))
    except RuntimeError:
        # test client or thread without running loop: run synchronously
        asyncio.run(manager.broadcast(_payload(new_note)))
    return note_to_dict(new_note)

@app.patch("/notes/{note_id}", response_model=NoteOut)
def patch_note(note_id: str, patch: NotePatch, db: Session = Depends(get_db)):
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    for key, value in patch.dict(exclude_unset=True).items():
        setattr(db_note, key, value)
    db.commit()
    db.refresh(db_note)
    def _payload(note_obj):
        return {"action": "update", "note": {
            "id": str(note_obj.id),
            "title": note_obj.title,
            "content": note_obj.content,
            "priority": note_obj.priority,
            "status": note_obj.status,
            "reminder_time": note_obj.reminder_time.isoformat() if note_obj.reminder_time else None,
            "created_at": note_obj.created_at.isoformat() if getattr(note_obj, 'created_at', None) else None,
            "updated_at": note_obj.updated_at.isoformat() if getattr(note_obj, 'updated_at', None) else None
        }}
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(manager.broadcast(_payload(db_note)))
    except RuntimeError:
        asyncio.run(manager.broadcast(_payload(db_note)))
    return note_to_dict(db_note)

@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: str, note: NoteSchema, db: Session = Depends(get_db)):
    db_note = db.query(Note).filter(Note.id == note_id).first()
    for key, value in note.dict().items():
        setattr(db_note, key, value)
    db.commit()
    db.refresh(db_note)
    def _payload(note_obj):
        return {"action": "update", "note": {
            "id": str(note_obj.id),
            "title": note_obj.title,
            "content": note_obj.content,
            "priority": note_obj.priority,
            "status": note_obj.status,
            "reminder_time": note_obj.reminder_time.isoformat() if note_obj.reminder_time else None,
            "created_at": note_obj.created_at.isoformat() if getattr(note_obj, 'created_at', None) else None,
            "updated_at": note_obj.updated_at.isoformat() if getattr(note_obj, 'updated_at', None) else None
        }}
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(manager.broadcast(_payload(db_note)))
    except RuntimeError:
        asyncio.run(manager.broadcast(_payload(db_note)))
    return note_to_dict(db_note)

@app.delete("/notes/{note_id}", response_model=dict)
def delete_note(note_id: str, db: Session = Depends(get_db)):
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(db_note)
    db.commit()
    payload = {"action": "delete", "note": {"id": str(note_id)}}
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(manager.broadcast(payload))
    except RuntimeError:
        asyncio.run(manager.broadcast(payload))
    return {"ok": True}
