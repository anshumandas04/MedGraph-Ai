# Master implementation prompt: make MedGraph's end-to-end workflow real

Copy the prompt below into the coding agent that will modify this repository. It is based on the current source tree and the observed demo behavior: documents show canned Amoxicillin OCR text, extracted events are empty, core lists are empty, the research route renders for a patient when opened directly, and Docker's frontend ports do not match the image.

---

## Prompt

You are working in the existing MedGraph repository. Your goal is to repair and complete the application so the advertised synthetic-data workflow works end to end: authenticated role-aware users can upload PDFs/images; text is extracted honestly with OCR for scanned pages; events are created with dates and citations; the timeline, graph, medications, investigations, signals, research metrics, and Ask MedGraph show the same stored data; and the app can be started locally or with Docker using documented steps.

This is a research prototype. Use synthetic data only. Do not present output as a diagnosis, treatment recommendation, or proof that a real-world follow-up was missed. Every extracted fact and generated signal must preserve provenance and uncertainty and support human review.

### Non-negotiable working rules

1. First inspect the whole repository, its Git status, and all existing source/config/test files. Preserve unrelated user changes. Do not overwrite the project by running `build.py` or `create_frontend.py`: both are code generators with hard-coded developer-specific absolute paths and can rewrite the project.
2. Make focused changes to the source tree in place. Keep the existing React/FastAPI architecture unless a concrete defect requires a small change. Do not replace the app with a mockup, scaffold, or unrelated rewrite.
3. Do not fake success. Mock OCR, mock AI, low-confidence output, missing keys, provider timeouts, and failed jobs must be explicitly represented in UI/status/logs. Never substitute canned text for a user's uploaded file while marking it processed.
4. Never silently swallow model/provider/database errors into empty successful results. Return safe, actionable status to the UI and useful server-side diagnostics without logging secrets, raw medical text, or tokens.
5. Do not commit API keys, passwords, uploaded files, databases, or private data. Demo credentials may exist only as clearly development-only seed data and must be disabled in production.
6. Build the complete user workflow, not only backend helpers. Keep UI states synchronized with API data, including loading, empty, queued, processing, completed, needs-review, and failed.

### Findings from the current code that must be addressed

- `backend/app/core/config.py` defaults `AI_PROVIDER` and `OCR_PROVIDER` to `mock`.
- `backend/app/services/ocr_service.py`'s mock returns the same hard-coded Amoxicillin paragraph for every document. Its real PaddleOCR import is lazy, but `get_ocr_provider()` only catches import errors during provider construction, so a missing runtime dependency can still fail later. PaddleOCR is not in `backend/requirements.txt`.
- `backend/app/services/document_service.py` instantiates `OpenAIProvider` directly instead of selecting `AI_PROVIDER`; the OpenAI SDK is not in `backend/requirements.txt`. The provider reads `LLM_MODEL`, while settings expose `OPENAI_MODEL`. The current path can fail even when mock mode is selected.
- `backend/app/services/ai/mock_provider.py` is only a small regex demo and does not extract the seeded clinical case comprehensively (including HbA1c numeric values, allergies/NKDA, results, follow-ups, and medication status).
- `backend/app/services/extraction_service.py` date normalization can return a `date` despite its datetime annotation, and relative dates can become null. Preserve source date text and avoid inventing a specific date for unresolved relative dates.
- `backend/app/services/document_service.py` uses in-process `BackgroundTasks`, does not clearly prevent duplicate page/event/chunk creation on retry, and has a TODO for relationship/signal updates. At minimum make demo processing idempotent and observable. Do not describe in-process tasks as durable for production.
- `backend/app/seed.py` contains a rich, explicitly synthetic longitudinal case and seeded users, but returns immediately if the admin user exists; it will not repair or refresh a stale partially populated database. Add a safe deterministic versioned demo-seed/reset path. Never drop or rewrite a non-demo database automatically.
- `frontend/src/routes/index.tsx` has authentication-only `ProtectedRoute`; the research page is nested under it without a role guard. The web UI can hide research from non-admin navigation, but the route and every corresponding API endpoint must enforce role authorization. The actual data endpoint already uses `require_role(["ADMIN"])`; preserve and test that defense.
- Audit every backend patient/document endpoint for patient-level authorization. A valid token must not allow a caller to substitute a different `patient_id`, `document_id`, or signal ID. Apply PatientAccess/ownership rules consistently to read, write, upload, search, reprocess, detail, and file download routes.
- `docker-compose.yml` maps the frontend to `3000:3000` and outer `nginx/nginx.conf` proxies to `frontend:3000`, but `frontend/Dockerfile` serves Nginx on port 80. Fix the internal port contract, health checks, and startup ordering.
- Compose uses a root `.env`, while current README instructions tell users to create `backend/.env`. Standardize one documented config path and ensure Pydantic settings, migrations, and seed scripts all load the same settings. Compose also hard-codes Postgres credentials instead of reading them from the configured environment; remove this divergence.
- `frontend/vite.config.ts` contains a specific Cloudflare Quick Tunnel host allowance. Do not make development server host checks globally permissive. Document secure, temporary dev-only tunneling separately from production hosting.
- `scripts/generate_demo_data.py` writes to a hard-coded absolute path. Make it repository-relative and deterministic, or deprecate it in favor of the official seed command.
- The current `test_upload.py` sends fake PDF bytes and hard-coded IDs, which is not a valid end-to-end OCR test. Replace or repair it as appropriate so tests use a generated valid fixture and isolated database.

### Phase 1: establish the actual architecture and data contracts

- Inventory routes, ORM models, schemas, frontend services/pages, and database migrations. Map each UI view to its API endpoint and patient scope.
- Inspect `backend/app/seed.py` and current models before changing the seeded clinical timeline. Keep the case explicitly fictional and synthetic. Prefer a deterministic documented timeline with source documents, page text, events, medication/investigation records, relationships, evidence, and signals.
- Define consistent event types, normalized dates, entity values, medication statuses, source document/page references, confidence ranges, processing statuses, and error shapes. Avoid breaking API callers without updating frontend types/services.
- Make seeding repeatable and safe: idempotently create or update only a clearly marked demo dataset in a demo database; provide an explicit destructive reset command requiring a positive demo-mode guard; refuse destructive actions if `DEMO_MODE` is false or the target database is not clearly designated for demo. Do not run destructive setup on app startup.

### Phase 2: configuration and real OCR

- Add validated provider settings/factory functions. `AI_PROVIDER=mock|openai` and `OCR_PROVIDER=mock|tesseract` (or another fully installed and documented provider) must be honored from configuration everywhere. Fail startup or a processing job with a clear configuration error when a requested provider is unavailable. No accidental silent fallback to fake OCR.
- Prefer PyMuPDF native text extraction for PDFs. For image-only/scanned pages, render pages under explicit DPI, dimension, page-count, and memory limits, then call Tesseract OCR. Include `pytesseract` in Python dependencies and install the Tesseract executable plus English language data in the backend image. Provide Windows/macOS/Linux setup guidance and allow a configured executable path. Preserve per-page OCR text/confidence and relevant block metadata.
- For images, validate decodability and dimensions before OCR. Validate actual file signatures/content, not only file extension and browser MIME. Enforce upload limits and safe randomized storage paths. Avoid path traversal, malformed PDFs, decompression bombs, and unbounded work.
- Keep mock OCR available only as an explicit demo/test provider. Its UI must plainly say synthetic/mock output. Include a test fixture whose known text differs per file so tests catch regressions to constant canned output.

### Phase 3: extraction, evidence, relationships, and signals

- Add an AI provider factory and include the correct SDK dependency for the configured provider. Use `OPENAI_MODEL` consistently (or rename the setting once and update `.env.example`, backend, docs, and Compose consistently). Do not create an OpenAI client with a dummy key in mock mode.
- Make mock extraction deterministic and useful against the demo fixtures. For the synthetic longitudinal case, extract dated consults, diagnoses/symptoms, allergy and NKDA assertions, medication start/continue/stop/change, HbA1c and other lab results with units, imaging recommendations/completions, referrals, and follow-up recommendations/completions.
- When using an LLM, use a schema-validated response, strict prompt to extract only present facts, bounded text size, temperature appropriate for extraction, and robust validation. Never infer dates from the current date. Preserve unresolved relative dates such as “in 3 months” in source/evidence and represent an unresolved target date explicitly.
- Every event, medication, investigation, and signal must retain source document ID, page, excerpt, and confidence where available. Citations must resolve to an actual document and page. Do not fabricate citations like `doc_1` or sample excerpts.
- Make retries idempotent: reprocessing one document should update/replace that document's derived pages/events/chunks/relationships and recompute affected signals without duplicates. Use a transaction strategy and ensure a failed job remains inspectable/retryable.
- Implement and document rules for contradiction detection (including conflicting allergy/NKDA assertions and medication stop vs later current-list mention), longitudinal numeric trends, and missing-follow-up evidence. A missing record means “no evidence found in this dataset,” not “care was not provided.” Include supporting and contradicting sources and deduplicate signals.
- A signal review action must be persisted and reflected in the dashboard. Use explicit review states and record who/when reviewed if the schema supports it.

### Phase 4: search / Ask MedGraph

- Make `AI_PROVIDER=mock` work without network access. Mock answers must quote only retrieved source text, return “no evidence found” when context is empty, and provide citations that match real chunks/pages.
- For OpenAI mode, handle embeddings being unavailable, pgvector missing, and chat failures with a clear fallback or error. Keep keyword search scoped by patient. Ensure vector queries filter by authorized patient before ranking.
- Do not send document content to external AI unless OpenAI mode is explicitly enabled and documented. Keep prompts and keys on the server. Enforce patient access before search and before answer generation. Include citations in UI with links to document detail/page.

### Phase 5: API authorization and frontend behavior

- Add backend authorization dependencies/helpers that enforce the current user's role and patient access, consistently across every endpoint. Admin, clinician, patient, and caregiver capabilities must be explicit. Do not rely on obscured navigation as access control.
- Add role-aware frontend route guards for `/app/research`, detail routes, upload/reprocess, and other restricted actions. Handle `401` and `403` states cleanly. The API is authoritative.
- Wire all pages to actual API responses. Remove placeholder/hard-coded mock UI text from production flows. Handle loading, empty, upload progress, queued/processing/completed/failed, retry, low-confidence needs-review, and API errors.
- The dashboard counts must use consistent definitions (for example, all docs vs processed docs) and label them clearly. Research metrics must be computed from benchmark ground truth, not hard-coded zeros or self-matches. A zero metric is valid only when the evaluation set/output is truly empty and should explain that.
- Ensure timeline and graph can render source-backed events and relationships, with usable empty states. Medications and investigations should display current/history status and provenance. Signals should support review/detail and evidence. Settings should not expose another user's profile.
- Test keyboard/accessibility basics for upload, navigation, filters, and review actions; show validation errors beside the relevant control.

### Phase 6: hosting and developer experience

- Fix Compose/frontend/Nginx ports so the static frontend container listens on port 80 and the outer reverse proxy targets that port. Keep `/api` proxying to the backend. Ensure SPA deep links fall back to `index.html`.
- Use the root `.env.example` as the single documented template. Keep development host URLs and Docker service URLs distinct. Source the Postgres container credentials and both database URLs from the same environment values. Validate required production secrets; do not use sample defaults in production.
- Add service health checks, proper depends-on health conditions, persistent Postgres and uploads, restart policies appropriate to the target, and a one-shot migration/seed process. Do not execute schema creation and seeding unconditionally on every web-worker startup.
- Document local setup, Docker setup, Windows OCR setup, Linux Docker OCR dependencies, production hosting behind HTTPS, domain/CORS setup, persistent backups, upgrades/migrations, demo seeding/reset, user roles, provider choices, upload limits, troubleshooting, and known limitations in `README.md`.
- Remove the developer-specific absolute path from `scripts/generate_demo_data.py`; do not make scripts depend on one user's home folder.
- Keep `.env`, uploaded documents, SQLite/Postgres database files, logs with sensitive values, and generated OCR artifacts ignored and out of Git. Do not add real patient data to fixtures.

### Required verification before calling this complete

Run appropriate focused backend and frontend checks after implementation and report commands plus results. Add/update automated tests for at least:

1. Auth succeeds/fails and role checks return 403 for unauthorized users.
2. A user cannot access a patient/document outside their authorized scope by changing IDs.
3. Mock OCR is explicit and deterministic and does not report canned output as file-derived OCR.
4. A valid text PDF and an image-only fixture produce page text and confidence; malformed/oversize files fail safely.
5. Reprocessing is idempotent and job failure is visible/retryable.
6. The synthetic timeline populates document/page-backed events, medications, investigations, and expected signal types.
7. Q&A returns no fabricated answer/citation for empty context and citations resolve for populated context.
8. Docker configuration builds and the frontend/API routes are reachable through the single proxy port.

If a runtime/model limitation prevents a check, state the exact blocker. Do not claim a feature works solely because a page renders or a test was written. At completion, provide a concise file-by-file summary, commands actually run, results, required environment variables, and any remaining limitations. Do not deploy publicly, upload patient files, or expose the app through a public tunnel as part of this task.

---

## End prompt

### How to use this prompt

1. Commit or otherwise back up the current project before giving this prompt to a coding agent.
2. Give the agent access to the complete repository, not only the files listed in the original request.
3. Provide a synthetic sample PDF/image and a disposable local database if end-to-end processing must be verified.
4. Configure secrets locally; never paste production API keys into a prompt or commit `.env`.
5. Review its diffs and runtime evidence before deploying. The README documents the current gaps as well as the intended setup; it is not a claim that OCR/AI/production hosting has already been repaired.
