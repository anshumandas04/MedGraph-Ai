# MedGraph

MedGraph is a research prototype for organizing uploaded health documents into searchable page text, extracted events, medication and investigation records, timelines, and review signals. Processing defaults to local rules and local OCR. No OpenAI or other hosted model is called unless `AI_PROVIDER=openai` is selected explicitly.

> **Research software.** MedGraph is not a medical device and its extracted facts and signals require human verification. A completed job means the processing pipeline finished; it does not certify that the extracted information is accurate. Use real patient information only in an appropriately authorized, secured environment.

## Current implementation

- PDF, PNG, JPG, and JPEG upload with size, extension, MIME, and file-signature checks.
- Embedded PDF text extraction with PyMuPDF. Scanned pages and images are OCRed locally with Tesseract; failures appear in the document status.
- Local, rule-based document classification and conservative event extraction with source document, page, excerpt, and confidence fields.
- Database-backed pages, events, medications, investigations, search chunks, relationships, and review signals.
- Patient-scoped authorization on the main patient/document/event/signal endpoints; public registration always creates a patient role.
- Document removal deletes the stored upload, OCR pages, search chunks, source events, graph links, feedback/evidence, and orphaned medication/investigation projections after explicit confirmation in the UI.
- Reprocessing replaces derived page/event/search rows and recomputes signals.
- Docker Compose services for PostgreSQL/pgvector, API, frontend, and Nginx.

Local rules are not a clinical NLP system: they recognize a limited set of explicit phrases and values. Review all extracted data. Background processing uses FastAPI `BackgroundTasks`, so it is not a durable job queue and should not be treated as production-grade processing infrastructure.

## Requirements

For Docker hosting, install Docker Engine or Docker Desktop with the Compose plugin. The backend image installs Tesseract and English language data.

For direct host development, install Python 3.12, Node.js 18 or newer, npm, and PostgreSQL 16 with pgvector (or use the Compose `db` service). To OCR scanned PDFs/images outside Docker, install Tesseract 5 with the `eng` language data and make `tesseract` available on `PATH`; set `TESSERACT_CMD` if it is elsewhere. Embedded-text PDFs do not need the Tesseract executable. Windows users can set, for example, `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe` in `.env`.

## Configure secrets and database

Copy the root template and replace every sample credential before starting:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Generate a secret key (run from the repository root):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the output in `SECRET_KEY`. Set a strong, unique `POSTGRES_PASSWORD`, then make `DATABASE_URL` and `DATABASE_URL_SYNC` use the matching database username/password. Compose uses host `db`; for the host-run backend use `localhost`. URL-encode reserved characters in database credentials. Keep `.env`, database files, uploaded documents, and keys out of Git.

Useful defaults in `.env`:

```dotenv
ENVIRONMENT=development
DEBUG=false
SQL_ECHO=false
DATABASE_URL=postgresql+asyncpg://medgraph:YOUR_URL_ENCODED_PASSWORD@db:5432/medgraph
DATABASE_URL_SYNC=postgresql://medgraph:YOUR_URL_ENCODED_PASSWORD@db:5432/medgraph
POSTGRES_USER=medgraph
POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD
POSTGRES_DB=medgraph
SECRET_KEY=YOUR_RANDOM_SECRET
AI_PROVIDER=local
OCR_PROVIDER=auto
OCR_LANGUAGE=eng
DEMO_MODE=false
```

`OCR_PROVIDER=auto` reads embedded PDF text and OCRs pages that need it. `AI_PROVIDER=local` keeps extraction on this machine. `AI_PROVIDER=openai` sends document text to the configured OpenAI-compatible service; configure its key and endpoint only if that transfer is approved. Do not put provider secrets in frontend variables.

## Run with Docker Compose

From the repository root, with `.env` set up as above:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f backend frontend nginx
```

The UI is served at `http://localhost`; API documentation is at `http://localhost:8000/docs`. The database and API host ports bind to loopback; Nginx publishes port 80. For internet hosting, put a TLS reverse proxy or hosting load balancer in front of Nginx, restrict inbound ports with the host firewall, set a strict `CORS_ORIGINS` value for the public origin, and configure backups for both `postgres_data` and `uploads_data`. Port 80 alone is not HTTPS.

The backend runs `python -m app.db.init_db` at startup. This creates missing tables for a fresh prototype database; it is not a schema migration mechanism. Use Alembic migrations for existing deployments and review migrations before applying them. Startup does not insert synthetic documents or demo accounts.

Create the first admin account only after the database is healthy. Supply a unique email and a password of at least 14 characters through environment variables, then run:

```powershell
$env:BOOTSTRAP_ADMIN_EMAIL = "admin@example.org"
$env:BOOTSTRAP_ADMIN_PASSWORD = "use-a-unique-long-password"
docker compose exec -e BOOTSTRAP_ADMIN_EMAIL -e BOOTSTRAP_ADMIN_PASSWORD backend python -m app.create_admin
Remove-Item Env:BOOTSTRAP_ADMIN_EMAIL, Env:BOOTSTRAP_ADMIN_PASSWORD
```

The command is first-admin-only and refuses to run if any admin already exists. Change the sample values; do not use demo credentials on a hosted instance. After login, use the admin UI/API to create patients and grant access to authorized clinicians. Public signup cannot create clinicians or admins.

## Run services directly on your machine

Start PostgreSQL using your installed server, or start just the Compose database:

```bash
docker compose up -d db
```

For a host-run backend, set `DATABASE_URL` and `DATABASE_URL_SYNC` in root `.env` to use `localhost` instead of `db`. Then:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

macOS/Linux activation is `source .venv/bin/activate`. The settings loader reads the repository-root `.env`, including when commands run from `backend/`.

In another terminal:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open the URL printed by Vite (usually `http://127.0.0.1:5173`). Vite proxies `/api` to port 8000. For a new local database, bootstrap an admin as described above (replace `docker compose exec ...` with `BOOTSTRAP_ADMIN_EMAIL=... BOOTSTRAP_ADMIN_PASSWORD=... python -m app.create_admin` from the backend environment; in PowerShell use `$env:...` assignments before the command).

## OCR and document processing

1. Upload a PDF/image from the Documents page or `POST /api/patients/{patient_id}/documents` with multipart field `file`.
2. The API verifies the extension, browser MIME type, signature, and `MAX_FILE_SIZE`, then stores the file under `UPLOAD_DIR` using a generated name. The UI accepts multiple files and sends each file as a separate request in a sequential batch.
3. The background processor extracts PDF text page by page. Pages below `OCR_MIN_TEXT_CHARS` are rendered at `OCR_RENDER_DPI` and sent to local Tesseract. `OCR_MAX_PAGES` and a rendered-pixel limit bound the workload.
4. Local rules classify the text, extract supported event patterns, write page text and evidence, update record projections, create search chunks/relationships/signals, and update processing status.
5. The Documents UI polls while processing and shows the resulting status/error. `COMPLETED` means text was processed; inspect source pages and verify every event before relying on it.

If a scanned document fails, check the document error and backend logs, then confirm `pytesseract`, the Tesseract executable, and the requested language data are installed. In Docker, rebuild after changing the image. If text is unreadable, the pipeline should fail or require review rather than substitute canned text. An OCR engine reports confidence but does not guarantee transcription accuracy.

## Accounts and data

The older local database may contain demo accounts created by a previous version. The app no longer seeds them on startup; a fresh deployment has no demo users or patients. Do not rely on or publish demo passwords. If you deliberately need synthetic development data, the seed script requires a disposable DEMO_SEED_PASSWORD of at least 14 characters supplied through the environment. Run it only against a disposable development database with DEMO_MODE=true. Never use that script to populate real patient records.

The patient/caregiver experience depends on explicit patient-access rows. Do not copy actual documents into a public demo deployment.

## Verify the implementation

Python unit tests:

```bash
python -m pytest -q tests/unit
```

The local actual-document integration check, when `backend/medgraph.db` and its referenced upload files exist:

```bash
python test_upload.py
```

It copies the SQLite DB to a temporary file, reprocesses its existing uploaded files locally twice, checks output counts/provenance/repeatability, and verifies the source DB hash did not change. It prints counts and status only, not the document text. This check covers the files available in that local database; it does not validate Tesseract on scanned pages, PostgreSQL hosting, or OCR accuracy. The repo's actual-document DB and files are local user data and must not be committed.

Frontend build and tests:

```bash
cd frontend
npm ci
npm run build
npx tsc --noEmit -p tsconfig.json
```

There are currently no frontend test files, so `npm test` has no application assertions to run. The frontend build and TypeScript check are the available automated checks.

## Useful endpoints

- Health: `GET /api/health`
- OpenAPI: `/docs` (development only; restrict or disable for hosted environments)
- Login: `POST /api/auth/login`
- Patient documents: `GET /api/patients/{patient_id}/documents`
- Document detail/file: `GET /api/documents/{document_id}` and `GET /api/documents/{document_id}/file`
- Delete document and its derived data: `DELETE /api/documents/{document_id}` (write access required; the UI asks for confirmation)
- Reprocess: `POST /api/documents/{document_id}/reprocess`
- Patient search: `POST /api/patients/{patient_id}/search`
- Admin diagnostics: `GET /api/admin/logs?limit=200&level=ERROR` (admin role required)

### View logs and diagnose missing module data

1. Rebuild/restart after pulling code changes with docker compose up --build -d.
2. To rebuild derived data for existing uploads, open Documents and choose **Reprocess existing**. Confirm only if you want those files re-read by the configured providers; the confirmation warns when an external AI provider is configured.
3. Sign in with an administrator account and open **System Diagnostics** in the left navigation. It refreshes every 10 seconds; use the level filter or **Download JSON** to share the sanitized entries.
4. To query the endpoint directly, open http://localhost:8000/docs, authorize with an admin bearer token, and call GET /api/admin/logs. Use limit up to 500 and levels ALL, ERROR, WARNING, or INFO.
5. For startup failures before the web screen is available, run docker compose logs --since=30m backend in PowerShell from the repository directory.

The in-app buffer keeps the latest 2,000 backend log entries in memory and resets on backend restart. It records request method, normalized route, status, duration, exception type, and a correlation ID. It does not record request/response bodies or query strings. Tokens, common API key formats, email addresses, and UUIDs are redacted. Treat downloaded logs as operational data and review them before sharing.

An upload being accepted only confirms storage/queueing. On Documents, wait for COMPLETED before expecting derived events, medications, investigations, relationships, or signals. NEEDS_REVIEW means OCR found no readable text; FAILED means processing stopped and should have a matching error/request record in Diagnostics. A successful empty result can also mean the document contained no facts recognized by the limited local extraction rules.

Every endpoint returning patient records must be called with a bearer token and must be scoped to the user's patient access. Do not treat hidden frontend navigation as authorization.

## Codebase architecture and algorithms

See [CODEBASE_GUIDE.md](CODEBASE_GUIDE.md) for TypeScript and FastAPI architecture diagrams, data flows, implemented algorithms, persistence relationships, document deletion behavior, and known limitations.

## Operations and known limits

- Protect both Postgres data and uploaded-file volumes with access controls, encryption, tested backups, and a retention/deletion policy.
- Use TLS, restricted network access, a strong `SECRET_KEY`, strong database credentials, and exact CORS origins before hosting.
- Keep `DEBUG=false` and `SQL_ECHO=false`; SQL parameter logging can disclose health text.
- The current worker runs inside the API process. A process restart can interrupt work; use a durable queue/worker before production use.
- `create_all` initializes a blank prototype DB but does not upgrade an existing schema. Apply reviewed Alembic migrations for upgrades.
- The local extraction rules cover a limited set of text patterns and do not provide clinical interpretation. Review extracted dates, values, medications, allergies, source text, and all signals.
- The research page reports live processing counts. Precision/recall/F1 are intentionally unavailable until human-adjudicated reference labels are configured; the app does not show placeholder benchmark scores.
- External providers receive document text when explicitly configured. Confirm contractual and privacy approval before enabling them for sensitive data.
- No setup procedure here constitutes certification, regulatory approval, or permission to use real patient data.
