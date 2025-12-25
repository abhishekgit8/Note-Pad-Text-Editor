# Real-time Note Pad Application

A modern, real-time note-taking application featuring a Kanban-style board, live updates, and task management capabilities. Built with Angular and FastAPI.

## 🚀 Features

- **Real-time Updates**: Changes made by one user (add, edit, delete, move) are instantly reflected for all connected users via WebSockets.
- **Kanban Board Layout**: Organize notes by status: **Active**, **Hold**, and **Finished**.
- **Drag & Drop**: Easily move notes between columns to update their status.
- **Countdown Timer**: Set reminder times for notes and see a live countdown (HH:MM:SS) to the deadline.
- **Optimistic UI**: Immediate UI updates for a snappy user experience, with background synchronization.
- **Responsive Design**: Built with Tailwind CSS for a clean, mobile-friendly interface.

## 🛠️ Tech Stack

### Frontend
- **Framework**: Angular 19 (Standalone Components)
- **Styling**: Tailwind CSS
- **State Management**: RxJS (BehaviorSubjects)
- **Real-time**: Native WebSockets

### Backend
- **Framework**: FastAPI (Python)
- **Database**: Supabase
- **ORM**: SQLAlchemy
- **Real-time**: FastAPI WebSockets

### DevOps
- **Containerization**: Docker & Docker Compose
- **Deployment**: Vercel (Frontend) & Render (Backend)

## 🏃‍♂️ Local Development Setup

### Prerequisites
- Node.js (v20+)
- Python (v3.10+)
- Docker (optional)

### Option 1: Using Docker Compose (Recommended)

Run the entire stack with a single command:

```bash
docker-compose up --build
```

- Frontend: http://localhost:4200
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the server:
    ```bash
    uvicorn main:app --reload
    ```

#### Frontend

1.  Navigate to the frontend directory:
    ```bash
    cd frontend/notes-app
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    ng serve
    ```

## 🚀 Deployment

### Backend (Render)

1.  Connect your repository to [Render](https://render.com/).
2.  Create a new **Web Service**.
3.  Render will automatically detect the `render.yaml` or `Dockerfile` in the `backend` directory.
4.  Deploy the service.
5.  **Note the URL** (e.g., `https://your-app.onrender.com`).

### Frontend (Vercel)

1.  Update `src/environments/environment.prod.ts` with your deployed Backend URL:
    ```typescript
    export const environment = {
      production: true,
      apiUrl: 'https://your-app.onrender.com',
      wsUrl: 'wss://your-app.onrender.com'
    };
    ```
2.  Push changes to GitHub.
3.  Connect your repository to [Vercel](https://vercel.com/).
4.  Select the `frontend/notes-app` directory as the root.
5.  Vercel will detect Angular and deploy automatically.

## 📂 Project Structure

```
├── backend/                 # FastAPI Backend
│   ├── main.py             # App entry point & WebSocket logic
│   ├── models.py           # Database models
│   ├── render.yaml         # Render deployment config
│   └── Dockerfile          # Backend Dockerfile
├── frontend/notes-app/      # Angular Frontend
│   ├── src/app/            # Components & Services
│   ├── src/environments/   # Environment config (Dev/Prod)
│   ├── vercel.json         # Vercel deployment config
│   └── Dockerfile          # Frontend Dockerfile
└── docker-compose.yml       # Local orchestration
```
