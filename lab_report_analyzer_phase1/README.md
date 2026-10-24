# Lab Report Analyzer Agent — Phase 2

Phase 2 prototype: MedGemma 1.5 4B adapter, structured extraction, deterministic report comparison, trend display, grounded follow-up Q&A, consent-gated local SQLite history, and guardrails.

## Safety
This is a development prototype, not a diagnostic tool. Never use its output for diagnosis, treatment, medication decisions, or emergencies. Verify all extracted values against the original report and have a qualified clinician review them. Use synthetic data until privacy/security review is complete.

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the UI with MedGemma disabled (no model download):
```powershell
$env:USE_MEDGEMMA="false"
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 and API docs at http://127.0.0.1:8000/docs.

To enable real extraction with Ollama, install Ollama from https://ollama.com, pull the model that your local Ollama registry exposes (for example `ollama pull medgemma1.5` if that exact tag is available), then set `$env:USE_MEDGEMMA="true"` and restart. Check the installed tag with `ollama list`; set `$env:OLLAMA_MODEL` to match it exactly. CPU-only inference on a 16 GB RAM laptop can be slow. The application calls Ollama's local HTTP API and does not download Hugging Face weights itself.

## Features
- PDF/image upload (10 MB max; PDF first page only)
- MedGemma multimodal structured extraction, lazy-loaded
- LangGraph orchestration for extraction validation and human-review routing
- Pydantic schema and deterministic missing-field/reference-bound validation
- Two-report comparisons; differing/missing units are flagged and never converted automatically
- Browser chart of an extracted biomarker value/reference interval
- Follow-up questions grounded in the saved report and a small example curated note file
- Optional consent-based local SQLite report history
- No raw report contents written to logs
- Tests for comparison and guardrails (`pytest`)

## API
- `GET /api/health`
- `POST /api/analyze` multipart fields `file`, `consent_to_store`
- `GET /api/reports`
- `GET /api/reports/{report_id}`
- `POST /api/compare` JSON `previous_report_id`, `current_report_id`
- `POST /api/chat` JSON `report_id`, `question`
- `GET /api/trends/{report_id}?biomarker=Hemoglobin`

History is disabled unless the user explicitly consents. Stored data is local at `data/reports.db`; stop the server and delete this file to remove prototype history. The included curated reference notes are illustrative, not medical authority. Replace them only with clinician-reviewed, licensed, versioned sources.


## React frontend (recommended UI)
The `frontend-react/` directory contains a separate React + Vite dashboard. It includes Overview, Analyze Report, Compare Reports, Report Q&A, Report History, light/dark theme, status indicators, guardrail notices, and responsive layout.

Run the backend in one PowerShell terminal:
```powershell
.\.venv\Scripts\Activate.ps1
$env:USE_MEDGEMMA="false"
uvicorn app.main:app --reload
```

Run the React frontend in a second terminal:
```powershell
cd frontend-react
npm install
npm run dev
```
Open http://localhost:5173. The React frontend calls the backend at `http://127.0.0.1:8000` by default. To change it, create `frontend-react/.env` with `VITE_API_BASE_URL=http://127.0.0.1:8000`.

Note: React UI is a separate development server; FastAPI also retains the basic HTML frontend at http://127.0.0.1:8000. Real analysis needs `USE_MEDGEMMA=true`, accepted model access, and enough RAM/GPU memory.

## Phase 3 additions
- Browser voice input for report Q&A where Web Speech API is supported; microphone permission is controlled by the browser.
- Local Ollama-based summary translation for Hindi, Kannada, Tamil, Telugu, Marathi, Bengali, Spanish, French, and English. Translation is advisory and must be verified.
- Minimal FHIR R4 `Bundle` export at `GET /api/reports/{report_id}/fhir`. This is a basic interoperability prototype, not a validated clinical integration; no patient identity is included.
- Local clinician-review status and notes at `GET/PUT /api/reports/{report_id}/review` with statuses `pending`, `in_review`, `reviewed`, `needs_correction`.
- Evaluation dashboard at `GET /api/evaluation`, showing operational counts from saved reports.

## Phase 4 reliability additions
- Explicit request schemas and bounded inputs for translation and review updates.
- Local review-state persistence in SQLite; raw report contents are not written to application logs.
- Test coverage for extraction guardrails, report comparison, FHIR mapping, and evaluation metrics.
- Health endpoint, actionable Ollama errors, upload limits, and configuration through environment variables.

### Local model configuration (PowerShell)
```powershell
$env:USE_MEDGEMMA="true"
$env:OLLAMA_MODEL="medgemma1.5"
$env:OLLAMA_HOST="http://127.0.0.1:11434"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Keep `USE_MEDGEMMA=false` to use non-model app features without calling Ollama. Translation requires the model to be enabled. Keep the backend bound to localhost for local-only use; do not expose it publicly without authentication, authorization, HTTPS, retention controls, and a security review.

### Run checks
```powershell
python -m pytest -q
cd frontend-react
npm install
npm run build
```

### Important limitations
- PDF processing currently reads page 1 only.
- FHIR output uses a local placeholder coding system for biomarker names and is not guaranteed to pass a receiving organization's profile validation.
- Evaluation numbers are operational indicators, not extraction accuracy or clinical performance. True evaluation requires a de-identified, expert-annotated test set and measured precision/recall/exact-match metrics.
- Voice input depends on browser support and language settings; it is not a medical speech-recognition system.
- This prototype is not a diagnostic tool and has not been clinically validated.
