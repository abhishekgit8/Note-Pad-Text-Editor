export interface Note {
  id?: string;
  title: string;
  content: string;
  priority: number;
  status: 'active' | 'hold' | 'finished';
  reminder_time?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}
