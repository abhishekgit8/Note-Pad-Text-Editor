import { HttpClient } from '@angular/common/http';
import { Injectable, NgZone } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

import { Note } from './note';

import { environment } from '../environments/environment';

@Injectable({ providedIn: 'root' })
export class NoteService {
  api = environment.apiUrl;

  private notesSubject = new BehaviorSubject<Note[]>([]);
  notes$: Observable<Note[]> = this.notesSubject.asObservable();

  private ws?: WebSocket;

  // timer observable updated from the server 'tick' messages
  private timerSubject = new BehaviorSubject<string>(new Date().toISOString());
  timer$ = this.timerSubject.asObservable();

  constructor(private http: HttpClient, private zone: NgZone) {
    this.loadNotes();
    this.connectWs();
  }

  private sanitize(note: Note) {
    const sanitized: any = { ...note };
    if (sanitized.reminder_time === '') sanitized.reminder_time = null;
    return sanitized;
  }

  loadNotes() {
    this.http.get<Note[]>(`${this.api}/notes`).subscribe({
      next: (n) => {
        console.log('NoteService loaded notes:', n);
        this.zone.run(() => this.notesSubject.next(n));
      },
      error: (e) => console.error('NoteService load failed', e)
    });
  }

  addNote(note: Note) {
    // return observable and append to state when server confirms
    // return observable and append to state when server confirms
    return this.http.post<Note>(`${this.api}/notes`, this.sanitize(note));
  }

  updateNote(id: string, note: Note) {
    // optimistic update
    const cur = this.notesSubject.getValue();
    const updatedLocal = (cur || []).map(n => n.id === id ? { ...n, ...note } : n);
    this.notesSubject.next(updatedLocal);

    return this.http.put<Note>(`${this.api}/notes/${id}`, this.sanitize(note)).subscribe(updated => {
      const cur2 = this.notesSubject.getValue();
      this.notesSubject.next((cur2 || []).map(n => n.id === id ? updated : n));
    });
  }

  deleteNote(id: string) {
    // optimistic remove
    const cur = this.notesSubject.getValue();
    this.notesSubject.next((cur || []).filter(n => n.id !== id));

    // return observable to allow caller handle success/failure and UI state
    return this.http.delete(`${this.api}/notes/${id}`);
  }

  private connectWs() {
    try {
      this.ws = new WebSocket(`${environment.wsUrl}/ws`);

      // When the socket opens, ensure we load notes (fresh sync) in case server wasn't ready earlier
      this.ws.onopen = () => {
        this.loadNotes();
      };

      this.ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          const cur = this.notesSubject.getValue();
          switch (msg.action) {
            case 'sync':
              // replace entire state with server-provided snapshot
              this.notesSubject.next(msg.notes || []);
              break;
            case 'create':
              this.zone.run(() => {
                const exists = (cur || []).find(n => n.id === msg.note.id);
                if (!exists) {
                  this.notesSubject.next([...(cur || []), msg.note]);
                }
              });
              break;
            case 'update':
              this.zone.run(() => this.notesSubject.next((cur || []).map(n => n.id === msg.note.id ? { ...n, ...msg.note } : n)));
              break;
            case 'delete':
              this.zone.run(() => this.notesSubject.next((cur || []).filter(n => n.id !== msg.note.id)));
              break;
            case 'tick':
              // update timer observable inside Angular zone so components update
              if (msg.now) this.zone.run(() => this.timerSubject.next(msg.now));
              break;
          }
        } catch (e) {
          console.error('ws message parse', e);
        }
      };

      this.ws.onclose = () => setTimeout(() => this.connectWs(), 2000);
    } catch (e) {
      console.error('ws connect failed', e);
    }
  }
}
