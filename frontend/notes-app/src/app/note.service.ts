import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Note } from './note';

@Injectable({ providedIn: 'root' })
export class NoteService {
  api = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getNotes() {
    return this.http.get<Note[]>(`${this.api}/notes`);
  }

  private sanitize(note: Note) {
    const sanitized: any = { ...note };
    if (sanitized.reminder_time === '') sanitized.reminder_time = null;
    return sanitized;
  }

  addNote(note: Note) {
    return this.http.post(`${this.api}/notes`, this.sanitize(note));
  }

  updateNote(id: string, note: Note) {
    return this.http.put(`${this.api}/notes/${id}`, this.sanitize(note));
  }

  deleteNote(id: string) {
    return this.http.delete(`${this.api}/notes/${id}`);
  }
}
