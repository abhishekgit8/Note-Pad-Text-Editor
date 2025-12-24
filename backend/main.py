from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Note
from pydantic import BaseModel, validator
from typing import List
from datetime import datetime

app = FastAPI()

# Configure CORS for development (allow frontend origin)
origins = [
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class NoteSchema(BaseModel):
    title: str
    content: str
    priority: int
    status: str
    reminder_time: datetime | None = None

    @validator("reminder_time", pre=True)
    def empty_string_to_none(cls, v):
        # Accept empty strings from clients (e.g., Angular date input) and convert to None
        if v == "":
            return None
        return v

@app.get("/notes")
def get_notes(db: Session = Depends(get_db)):
    return db.query(Note).order_by(Note.priority.asc()).all()

@app.post("/notes")
def create_note(note: NoteSchema, db: Session = Depends(get_db)):
    new_note = Note(**note.dict())
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.put("/notes/{note_id}")
def update_note(note_id: str, note: NoteSchema, db: Session = Depends(get_db)):
    db_note = db.query(Note).filter(Note.id == note_id).first()
    for key, value in note.dict().items():
        setattr(db_note, key, value)
    db.commit()
    return db_note

@app.delete("/notes/{note_id}")
def delete_note(note_id: str, db: Session = Depends(get_db)):
    db_note = db.query(Note).filter(Note.id == note_id).first()
    db.delete(db_note)
    db.commit()
    return {"ok": True}
