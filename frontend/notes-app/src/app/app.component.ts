import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { NoteService } from './note.service';
import { Note } from './note';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './app.component.html'
})

export class AppComponent {
  notes: Note[] = [];

  newNote: Note = {
    title: '',
    content: '',
    priority: 1,
    status: 'active',
    reminder_time: ''
  };

  saveSubject = new Subject<Note>();

  constructor(private service: NoteService) {
    this.loadNotes();

    this.saveSubject
      .pipe(debounceTime(3000))
      .subscribe(note => {
        if (note.id) {
          this.service.updateNote(note.id, note).subscribe();
        }
      });
  }

  loadNotes() {
    this.service.getNotes().subscribe(n => this.notes = n);
  }

  addNote() {
    this.service.addNote(this.newNote).subscribe(() => {
      this.newNote = {
        title: '',
        content: '',
        priority: 1,
        status: 'active',
        reminder_time: ''
      };
      this.loadNotes();
    });
  }

  onEdit(note: Note) {
    this.saveSubject.next(note);
  }

  currentTime() {
    return new Date().toLocaleTimeString();
  }

  deleteNote(id: string) {
  this.service.deleteNote(id).subscribe(() => {
    this.loadNotes();
  });
}

}
