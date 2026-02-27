# VitalNote — AI Medical Scribe

> **Prototype / portfolio project. Not intended for clinical use.**

VitalNote listens to a doctor–patient consultation, transcribes the audio, strips all patient identifiers, and generates a structured SOAP note — automatically. The entire pipeline runs in seconds, freeing clinicians from manual documentation.

---

## ✨ Features

| | |
|---|---|
| 🎙️ **Upload or Record** | Drag-and-drop an audio file or record directly in the browser |
| 📝 **Auto-Transcription** | AssemblyAI with speaker-diarisation labels |
| 🔒 **PII Redaction** | Microsoft Presidio (local, zero-data-egress) strips names, dates, locations, and other identifiers |
| 🧠 **SOAP Note Generation** | Groq + Llama 3.3 70B produces a structured Subjective / Objective / Assessment / Plan note |
| 📄 **PDF Export** | Download the finished note as a print-ready PDF (WeasyPrint) |
| 📊 **Dashboard** | Full history of consultations with real-time status polling |
| 🔐 **Auth** | Email / password registration and login, session-based |

---

## 🏗️ Architecture

```
Browser
  │
  ├── POST /upload/           → Django (Gunicorn)
  │                                │
  │                                ├── Saves audio → Cloudflare R2 (prod) / local (dev)
  │                                └── Enqueues Celery task
  │
  └── GET  /encounters/<id>/  → Polls every 3 s until COMPLETED / FAILED
                                       │
                               Celery Worker
                                       │
                               ┌───────▼────────┐
                               │  Transcription  │  AssemblyAI API
                               └───────┬────────┘
                               ┌───────▼────────┐
                               │  PII Redaction  │  Presidio (local · en_core_web_sm)
                               └───────┬────────┘
                               ┌───────▼────────┐
                               │  SOAP Generation│  Groq · Llama 3.3 70B
                               └───────┬────────┘
                               ┌───────▼────────┐
                               │   PDF Render    │  WeasyPrint
                               └────────────────┘
```

**Status flow:** `PENDING → TRANSCRIBED → REDACTED → COMPLETED` (or `FAILED`)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5.1, Django REST Framework, drf-spectacular |
| **Task Queue** | Celery 5 + Redis |
| **Database** | PostgreSQL (prod) · SQLite (dev) |
| **File Storage** | Cloudflare R2 via S3-compatible API (prod) · local media (dev) |
| **Transcription** | AssemblyAI |
| **PII Redaction** | Microsoft Presidio + spaCy `en_core_web_sm` |
| **AI / LLM** | Groq API · Llama 3.3 70B |
| **PDF** | WeasyPrint |
| **Frontend** | Django templates · Tailwind CSS CDN · Vanilla JS |
| **Server** | Gunicorn |
| **Containerisation** | Docker + Docker Compose |
| **Deployment** | Render (Docker runtime) |

---

## 🚀 Running Locally

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker + Docker Compose v2)
- API keys for **AssemblyAI** and **Groq**

### 1 — Clone & configure

```bash
git clone https://github.com/<your-username>/vitalnote.git
cd vitalnote
cp .env.example .env   # then fill in the values below
```

**.env values required for local dev:**

```env
SECRET_KEY=any-long-random-string
DEBUG=True

# Transcription
ASSEMBLYAI_API_KEY=...

# SOAP generation
GROQ_API_KEY=...

# Leave blank to use local file storage
USE_R2=False
```

### 2 — Build & start

```bash
docker compose -f docker-compose.yml up --build
```

This starts three services:

| Service | Description |
|---|---|
| `redis` | Message broker for Celery |
| `web` | Django + Gunicorn on `localhost:8000` |
| `celery_worker` | Background pipeline worker |

> First build takes a few minutes — it installs all Python dependencies and downloads the spaCy language model.

### 3 — Open the app

Navigate to **[http://localhost:8000](http://localhost:8000)**, create an account, and upload a consultation audio file.

---

## ☁️ Deploying to Render

The repo includes a `render.yaml` blueprint. Connect your GitHub repo in the Render dashboard, then add a **vitalnote-env** environment variable group with:

```
DATABASE_URL          # Render PostgreSQL connection string
REDIS_URL             # Render Redis connection string
ALLOWED_HOSTS         # your-app.onrender.com
SECRET_KEY
ASSEMBLYAI_API_KEY
GROQ_API_KEY
USE_R2=True
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME
R2_ENDPOINT_URL       # https://<account-id>.r2.cloudflarestorage.com
```

Render will build the Docker image and deploy both the web service and the Celery worker automatically.

---

## 📁 Project Structure

```
vitalnote/
├── apps/
│   ├── encounters/          # Core domain: models, views, API, Celery tasks
│   │   └── services/        # transcription.py · redaction.py · soap.py
│   └── users/               # Custom user model, registration, login
├── config/
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── development.py   # SQLite, local media, DEBUG=True
│   │   └── production.py    # PostgreSQL, R2, WhiteNoise
│   └── urls.py
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh        # Runs migrations → collectstatic → Gunicorn / Celery
├── static/
│   └── js/upload.js         # File upload + in-browser recording (MediaRecorder)
├── templates/
│   ├── base.html            # Dark-theme shell, navbar, flash messages
│   ├── home.html            # Landing page (standalone)
│   └── encounters/          # dashboard · upload · result · soap_pdf
├── docker-compose.yml
├── render.yaml
└── requirements.txt
```

---

## 🔌 API

Interactive docs are available at **`/api/docs/`** (Swagger UI, powered by drf-spectacular).

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/encounters/` | Create encounter + enqueue pipeline |
| `GET` | `/api/encounters/<id>/` | Poll status & retrieve SOAP note |
| `GET` | `/api/encounters/<id>/pdf/` | Download PDF |

---

## ⚠️ Disclaimer

VitalNote is a **portfolio / demonstration project**. It is not validated for clinical use, does not meet HIPAA requirements in its current form, and must not be used with real patient data.

---

## 📄 License

[MIT](LICENSE)
