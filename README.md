# Cortexia — School HelpDesk Chatbot

Python-only build for competition submission:
- FastAPI backend (`backend/`) for auth, access-control, chat, and data fetching
- CustomTkinter desktop client (`client/`) for the full user-facing experience

## 1) Supabase setup
1. Create a Supabase project.
2. Run the SQL in [`supabase/schema.sql`](supabase/schema.sql) using the Supabase SQL editor.
3. Insert at least one school row in `public.schools`, and create some:
   - `public.users` rows for **student** and **staff** credentials
   - `public.knowledge_items` rows for visitor/student/staff info (fees, timings, policies, etc.)

## 2) Environment variables
Copy `.env.example` to `.env` and fill:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (**server-only**; never expose to browser)
- **LLM keys (recommended: both for free-tier failover):**
  - `OPENAI_API_KEY` — used **first** for intent parsing and answer generation
  - `GEMINI_API_KEY` — used if OpenAI errors, rate-limits, or returns an empty answer
  - If **neither** is set, the bot still runs using heuristics + raw facts from Supabase
- `SESSION_SECRET`
- Optional desktop controls:
  - `SERVE_FRONTEND=false` (recommended for Python-only submission narrative)
  - `FORMSPREE_ENDPOINT=https://formspree.io/f/YOUR_FORM_ID`

## 3) Run backend (Windows / PowerShell)
From the repo root:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
uvicorn app.main:app --reload --app-dir .\backend
```

## 4) Run desktop client (new terminal)
From the repo root:

```bash
.\.venv\Scripts\Activate.ps1
pip install -r .\client\requirements.txt
python -m client.main
```

## 5) Video demo flow
1. Start backend.
2. Start desktop client.
3. Record: splash -> school resolve -> role login -> dashboard chat.
4. Include one restricted query to show access denial behavior.
5. (Optional) Temporarily break OpenAI to show **Gemini fallback**, or vice versa.
6. Submit one feedback form from the in-app feedback modal.

## 6) Competition packaging notes
- Active submission path is Python-only (`backend/`, `client/`, `supabase/`).
- `frontend/` can be kept for personal archive, but exclude it from competition zip if strict interpretation is required.
