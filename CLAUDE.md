# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Sheet Personalizer** is a B2B lead personalization SaaS tool. Users connect a Google Sheet of leads, map columns, configure AI prompts, and the app scrapes each company's website and generates personalized cold-outreach icebreakers using OpenAI GPT-4o. Results are written back to the sheet automatically.

## Commands

### Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run development server (port 8001)
cd backend && uvicorn server:app --reload --port 8001

# Lint
cd backend && flake8
cd backend && black .

# Run API integration tests (requires live server)
python backend_test.py
```

### Frontend
```bash
# Install dependencies
cd frontend && yarn install

# Start dev server (port 3000)
cd frontend && yarn start

# Production build
cd frontend && yarn build
```

### Infrastructure
```bash
# Check supervisor-managed services (production)
sudo supervisorctl status
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Backend health check
curl http://localhost:8001/api/health
```

### Environment
Both services are managed by supervisor in production. The backend reads from `backend/.env`. The frontend reads `REACT_APP_BACKEND_URL` from its `.env` file to know where to call the API.

## Architecture

### Backend (`backend/`)

FastAPI app in `server.py` with all routes mounted under an `/api` prefix via `APIRouter`. Services are instantiated as module-level singletons and injected into route handlers.

**Service layer** (`backend/services/`):
- `auth_service.py` — JWT auth (PyJWT + bcrypt). `get_current_user` is a FastAPI dependency that creates a new MongoDB client per request (current pattern).
- `google_service.py` — Google OAuth flow + Sheets/Drive API calls. Stores/refreshes tokens in `google_connections` collection.
- `scraper_service.py` — Fetches homepage + up to 3 scored sub-pages per lead. Scores links by matching preference patterns (`/product`, `/solutions`, `/about`, etc.) and blacklists noise paths (`/privacy`, `/cdn-cgi`, assets). Includes SSRF protection blocking localhost/private IPs.
- `llm_service.py` — OpenAI calls with user-supplied API key. Two-step pipeline: `generate_summary` (structured JSON extraction) → `generate_icebreaker` (personalized email opener). Post-processes icebreakers to strip hyphens per product spec; retries once if hyphens remain after replacement.
- `run_service.py` — Orchestrates the full pipeline. Reads sheet rows from Google Sheets, creates `run_items` in MongoDB, processes items concurrently (semaphore of 4), then batch-writes results back to the sheet.
- `credit_service.py` — Simple debit ledger; 50 credits granted on signup, 1 deducted per successfully processed row.

**Data flow for a run:**
```
POST /api/runs
  → RunService.create_run()   # reads sheet, creates run + run_items in Mongo
  → BackgroundTasks.add_task(RunService.process_run)
      → asyncio.gather(process_item × N, semaphore=4)
          → ScraperService.scrape_company()
          → LLMService.generate_summary()
          → LLMService.generate_icebreaker()
      → write_results_to_sheet()   # batch update via Google Sheets API
```

**Database (MongoDB)** collections: `users`, `credit_balances`, `credit_ledger`, `google_connections`, `projects`, `field_mappings`, `prompt_configs`, `runs`, `run_items`, `api_keys`, `oauth_states`.

Documents use a string `id` field (UUID) as the logical key; `_id` is always excluded from queries with `{"_id": 0}`.

**Security note:** `api_keys.key_encrypted` stores the OpenAI key in plaintext (marked TODO in `server.py:383`). Do not treat it as encrypted.

### Frontend (`frontend/src/`)

React 19 + React Router 7 SPA built with `craco`.

- **Routing** (`App.js`): Public routes (`/`, `/login`, `/signup`) + `PrivateRoute`-wrapped routes (`/dashboard`, `/projects/new`, `/projects/:id`, `/runs/:id`, `/settings`). Auth guard reads `token` from Zustand store.
- **State** (`store/useStore.js`): Zustand store persisted to localStorage for `user` + `token`. Also holds transient wizard state (`wizardStep`, `wizardData`).
- **API client** (`utils/api.js`): Axios instance with base URL from `REACT_APP_BACKEND_URL`. Interceptor attaches Bearer token; 401 responses clear storage and redirect to `/login`.
- **Project creation wizard** (`pages/NewProject.js` + `components/wizard/`): 5-step flow — Step1Connect (verify Google) → Step2SelectSheet → Step3MapColumns → Step4ConfigurePrompts → Step5Run. Wizard state is accumulated in `wizardData` and submitted as a single `POST /api/projects` + `POST /api/runs` at Step 5.
- **UI components** (`components/ui/`): shadcn/ui primitives (Radix UI based). Do not modify these files; add new components via shadcn CLI or follow the existing pattern.

## Design System

Defined in `design_guidelines.json`. Dark mode only — never add a light mode toggle.

- **Colors**: Background `#0a0a0a`, Primary emerald `#10b981` (`emerald-500`), Cards `#121212`, Borders `zinc-800`
- **Typography**: Headings → `Outfit` (semibold/medium), Body → `Inter`, Code → `JetBrains Mono`
- **Buttons**: Primary actions use `bg-emerald-500 text-black` with a glow shadow. Secondary use `bg-zinc-900 border border-zinc-800`.
- **Icons**: Always use `lucide-react`. No other icon library.
- **Toasts**: Always use `sonner`. Success = emerald, error = red.
- **Icebreaker copy rule**: No hyphens or dashes anywhere in generated icebreaker text (enforced at `llm_service.py:176-202`).

## Key Conventions

- All API routes are prefixed `/api` — the Kubernetes ingress routes `/api/*` to the backend and everything else to the frontend.
- `run_items.row_index` is 1-based and maps directly to the Google Sheet row number for write-back.
- Preview mode limits processing to 3 rows; full mode processes all rows up to `end_row`.
- The `output_mode` field on `field_mappings` controls write-back behavior; only `same_sheet` is implemented (appends new columns for Icebreaker, Status, Error).
- Scraper truncates per-page text to 6000 chars and combined text to 15000 chars before passing to the LLM.
- `website_text` passed to `generate_summary` is capped at 12000 chars in `llm_service.py:94`.
