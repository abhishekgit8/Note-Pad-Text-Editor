import { Component, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NoteService } from './note.service';
import { Note } from './note';
import { Subject } from 'rxjs';
import { debounceTime, finalize } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html'
})

export class AppComponent {
  notes: Note[] = [];

  // modal state
  showAdd = false;
  showView = false;
  viewing?: Note | null = null;

  // creation UI state
  adding = false;

  // deletion UI state
  deleting = false;
  deletingId?: string | null = null;

  newNote: Note = {
    title: '',
    content: '',
    priority: 1,
    status: 'active',
    reminder_time: ''
  };

  saveSubject = new Subject<Note>();

  // timer updated from websocket 'tick'
  timerNow?: string;

  constructor(private service: NoteService, private zone: NgZone, private cdr: ChangeDetectorRef) {
    // subscribe to reactive notes stream
    this.service.notes$.subscribe(n => {
      console.log('AppComponent received notes:', n);
      this.zone.run(() => {
        this.notes = n || [];
        this.cdr.detectChanges();
      });
    });

    // subscribe to server tick timer
    this.service.timer$.subscribe(ts => this.zone.run(() => this.timerNow = ts));

    // debounce inline edits
    this.saveSubject
      .pipe(debounceTime(1500))
      .subscribe(note => {
        if (note.id) {
          this.service.updateNote(note.id, note);
        }
      });
  }

  // Derived groups for the Kanban columns
  inStatus(status: string) {
    return this.notes.filter(n => n.status === status);
  }

  openAdd() { this.showAdd = true; }
  closeAdd() { this.showAdd = false; }

  submitAdd() {
    this.adding = true;
    this.service.addNote(this.newNote)
      .pipe(finalize(() => { this.zone.run(() => { this.adding = false; }); }))
      .subscribe({
        next: (created) => {
          // clear newNote and close on success (run inside zone)
          this.zone.run(() => {
            this.newNote = { title: '', content: '', priority: 1, status: 'active', reminder_time: '' };
            this.closeAdd();
          });
        },
        error: (err) => {
          console.error('create failed', err);
        }
      });
  }

  openView(note: Note) { this.viewing = { ...note }; this.showView = true; }
  closeView() { this.viewing = null; this.showView = false; }

  saveView() {
    if (this.viewing?.id) {
      this.service.updateNote(this.viewing.id, this.viewing);
      this.closeView();
    }
  }

  deleteNote(id?: string) {
    if (!id) return;
    // set UI state
    this.deleting = true;
    this.deletingId = id;

    this.service.deleteNote(id)
      .pipe(finalize(() => { this.zone.run(() => { this.deleting = false; this.deletingId = undefined; }); }))
      .subscribe({
        next: () => {
          // If modal was open for this note, close it
          this.zone.run(() => {
            if (this.viewing?.id === id) {
              this.closeView();
            }
          });
        },
        error: () => {
          // revert optimistic change by reloading
          this.service.loadNotes();
        }
      });
  }

  // Inline edit debounce
  onEdit(note: Note) {
    this.saveSubject.next(note);
  }

  currentTime() {
    return new Date().toLocaleTimeString();
  }

  // compute relative remaining time to a note reminder_time using the server tick
  remaining(note: Note) {
    if (!note.reminder_time) return '';
    try {
      const now = new Date(this.timerNow || new Date().toISOString());
      const target = new Date(note.reminder_time);
      const diff = Math.floor((target.getTime() - now.getTime()) / 1000);
      if (diff <= 0) return 'due';

      const hours = Math.floor(diff / 3600);
      const minutes = Math.floor((diff % 3600) / 60);
      const seconds = diff % 60;

      return `${hours}H:${minutes}M:${seconds}S`;
    } catch (e) {
      return '';
    }
  }

  // Drag & Drop handlers
  onDragStart(e: DragEvent, noteId?: string) {
    if (!noteId) return;
    e.dataTransfer?.setData('text/plain', noteId);
    e.dataTransfer!.effectAllowed = 'move';
  }

  onDragOver(e: DragEvent) {
    e.preventDefault();
    e.dataTransfer!.dropEffect = 'move';
  }

  async onDrop(e: DragEvent, status: string) {
    e.preventDefault();
    const id = e.dataTransfer?.getData('text/plain');
    if (!id) return;
    const note = this.notes.find(n => n.id === id);
    if (!note) return;
    // compute new priority (append to end of column)
    const column = this.inStatus(status);
    const maxPriority = column.reduce((m, it) => Math.max(m, it.priority || 0), 0);
    const updated = { ...note, status, priority: maxPriority + 1 } as Note;
    this.service.updateNote(id, updated);
  }

}
