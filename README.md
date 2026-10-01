# MedGraph AI

**AI-Based Healthcare Journey Reconstruction**

MedGraph is a research prototype that reconstructs a patient's healthcare journey from fragmented medical records. It takes raw medical documents (PDFs, images) and uses OCR + AI to extract events, map them to a timeline, identify conflicts or missing follow-ups, and provides a RAG interface to "chat" with the medical records.

---

## 🚀 Prerequisites

- **Python 3.10+** (For the FastAPI backend and AI pipelines)
- **Node.js v18+** (For the React/Vite frontend)
- **Git**

---

## 🔐 Environment Variables

Before running the application, you must set up your environment secrets. A template file is provided.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Copy the template file to create your active `.env` file:
   ```bash
   cp .env.demo .env
   # Or on Windows: copy .env.demo .env
   ```
3. Open `backend/.env` and add your secrets. The most critical is your OpenAI API key for event extraction and RAG capabilities:
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```
   *(Note: The system gracefully falls back to keyword searches and mock data responses if the API key is invalid, but full functionality requires a real key).*

---

## 🛠️ Local Setup

### 1. Backend Setup

Open a terminal and set up the Python backend:

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies (FastAPI, PaddleOCR, OpenAI, etc.)
pip install -r requirements.txt

# Seed the database with the initial demo data
python -m app.seed

# Start the backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be running at `http://localhost:8000`.

### 2. Frontend Setup

Open a new terminal and set up the React frontend:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start on `http://localhost:5173` (or 5174 if the port is busy).

---

## 🩺 Using the App

1. Open your browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
2. Log in using the seeded demo credentials:
   - **Email:** `admin@medgraph.dev`
   - **Password:** `MedGraph2026!`
3. Explore the **Dashboard**, view the patient **Timeline**, interact with the knowledge **Graph**, and test the **Ask MedGraph** feature!

---

## 🐳 Docker Deployment (Optional)

If you prefer to run the entire stack (PostgreSQL + pgvector, Backend, Frontend, Nginx) using Docker:

```bash
# Make sure your backend/.env file is configured first!
docker-compose up -d --build
```
This will automatically map the databases and start the app on port `80`.
