# AI Coding Mentor Agent

An AI-powered coding mentor. Paste in source code, and it detects the
language, finds bugs (syntax, runtime, logic, edge cases, performance,
security, quality), explains *why* each one is a problem, generates a
corrected version, writes tests, and teaches the underlying concept you
should learn next — like a patient senior engineer reviewing your PR.

It runs entirely on the **free tier of the Google Gemini Developer API**.
No Claude API, no OpenAI API, no paid API of any kind, no credit card.

---

## 1. Project Overview

The app is a single request/response mentoring tool:

1. You paste code into a Monaco editor, pick a language and difficulty.
2. The backend runs **deterministic static analysis** first (for Python:
   real AST parsing + compile checks — no guessing).
3. The backend then asks **Gemini** to reason about logic bugs, generate a
   fix, write tests, and produce mentoring feedback.
4. Everything Gemini returns is validated against a strict Pydantic schema
   before it's ever shown to you. Findings confirmed by static analysis are
   clearly marked "Statically verified"; everything else is marked
   "AI-suggested" so you always know which is which.

## 2. Features

- Bug detection across 7 categories: syntax, runtime, logic, edge case,
  performance, security, quality.
- Severity levels (LOW/MEDIUM/HIGH/CRITICAL) and real line numbers — never
  invented; `null` when the line can't be confidently determined.
- Corrected code + an explanation of every change.
- Auto-generated tests (pytest for Python) with per-test explanations.
- Edge-case callouts (empty input, None, negative numbers, boundaries…).
- Code quality score (0–100), explicitly labeled as an AI-assisted estimate.
- Mentoring feedback: strengths, concepts to learn, and a next exercise.
- Optional "Give Me a Hint" mode that nudges without revealing the fix.
- Difficulty-aware explanations (beginner / intermediate / advanced).
- Clean, modern developer-tool UI built around the Monaco editor.

## 3. Architecture

```
USER
  ↓
CODE EDITOR (React + Monaco)
  ↓
FASTAPI (/api/analyze)
  ↓
LANGUAGE DETECTION / VALIDATION (Pydantic)
  ↓
STATIC CODE ANALYSIS (Python AST/compile — deterministic, no AI)
  ↓
GEMINI AI ANALYSIS (bugs, fixes, tests, mentoring — structured JSON)
  ↓
SCHEMA VALIDATION + VERIFIED/AI-SUGGESTED RECONCILIATION
  ↓
STRUCTURED RESPONSE
  ↓
REACT UI (score, bug cards, fixed code, tests, learning points)
```

Deterministic analysis and AI analysis are deliberately kept separate:
`app/analyzers/python_analyzer.py` never calls Gemini, and
`app/ai/mentor_agent.py` never trusts its own AI output without validating
it against `MentorAnalysis` (Pydantic). If Gemini's JSON fails validation,
one retry is attempted with a clarifying instruction; if it still fails,
the API returns the static-analysis results with `analysis_status:
"partial"` rather than silently returning corrupted data.

## 4. How the AI Agent Works

- `app/ai/prompts.py` — a dedicated system prompt (mentor persona, rules
  about never inventing bugs/line numbers, and how to phrase things per
  skill level) plus a schema-description prompt builder. Kept out of the
  FastAPI routes entirely.
- `app/ai/gemini_client.py` — the only module that imports the Gemini SDK.
  Enforces a timeout, retries rate limits (`429`) and transient `5xx`
  errors with bounded exponential backoff, and converts SDK exceptions
  into three well-defined exception types the rest of the app understands.
- `app/ai/mentor_agent.py` — builds the prompt, calls the client, strips
  stray markdown fences defensively, parses JSON, validates it against
  `MentorAnalysis`, retries once on failure, and reconciles each bug's
  `verified` flag against the deterministic static-analysis line numbers
  (the AI is never trusted to self-report verification).

## 5. Tech Stack

**Backend:** Python 3.11+, FastAPI, Pydantic v2, Uvicorn, the official
`google-generativeai` SDK, pytest.

**Frontend:** React 18, TypeScript, Vite, Monaco Editor (`@monaco-editor/react`), Axios.

**Code analysis:** Python `ast` / `compile` for deterministic checks;
Gemini for logic reasoning, explanations, fixes, and test generation.

**Optional:** Docker, Docker Compose.

## 6. Project Structure

```
ai-coding-mentor/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app, CORS, middleware
│   │   ├── config.py               # All settings from env vars
│   │   ├── api/routes.py           # /api/health, /analyze, /hint
│   │   ├── ai/
│   │   │   ├── gemini_client.py    # Only module that calls Gemini
│   │   │   ├── prompts.py          # System + user prompt builders
│   │   │   └── mentor_agent.py     # Orchestration + validation
│   │   ├── analyzers/
│   │   │   └── python_analyzer.py  # AST/compile-based static analysis
│   │   ├── models/
│   │   │   ├── request_models.py
│   │   │   └── response_models.py
│   │   ├── services/
│   │   │   ├── analysis_service.py # Pipeline orchestration
│   │   │   └── test_service.py     # Optional sandboxed test execution
│   │   └── utils/logging_config.py
│   ├── tests/                      # 23 pytest tests, Gemini fully mocked
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/             # CodeEditor, BugCard, ScoreGauge, …
│   │   ├── pages/Home.tsx
│   │   ├── services/api.ts         # Axios client (no API key here)
│   │   ├── types/index.ts
│   │   ├── hooks/useAnalyze.ts
│   │   ├── App.tsx / main.tsx / index.css
│   ├── package.json / tsconfig*.json / vite.config.ts / index.html
│   └── .env.example
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── docker-compose.yml
├── .gitignore
├── README.md
└── .env.example
```

## 7. Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A free Google account (for the Gemini API key)
- (Optional) Docker + Docker Compose

## 8. How to Create a Free Gemini API Key

1. Go to **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
2. Sign in with any Google account.
3. Click **"Create API key"**.
4. Choose "Create key in new project" if you don't already have one.
5. Copy the key — you will paste it into `.env` in the next section.
6. No credit card is required for the free tier. Google's free tier has
   request-per-minute and request-per-day limits that change over time —
   check the current limits on the AI Studio pricing page before assuming
   how much traffic you can send.

## 9. Environment Configuration

Copy the example files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env`:

```
GEMINI_API_KEY=paste_your_real_key_here
GEMINI_MODEL=gemini-1.5-flash
```

`GEMINI_MODEL` can be changed to any current free-tier Gemini model name
(e.g. `gemini-1.5-flash-8b`, `gemini-2.0-flash`) without touching any code —
just edit the `.env` file and restart the backend.

`frontend/.env` only needs `VITE_API_URL` — it never contains the Gemini key.

## 10. Backend Installation

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 11. Frontend Installation

```bash
cd frontend
npm install
```

## 12. Running the Application

**Backend** (from `backend/`, with your virtualenv active):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs.

**Frontend** (from `frontend/`, in a second terminal):

```bash
npm run dev
```

Visit `http://localhost:5173`.

## 13. Running Tests

```bash
cd backend
pytest -q
```

All 23 tests run with the Gemini service **mocked** — no API key or network
access is required to run the test suite. Tests cover: health endpoint,
empty/invalid requests, unsupported languages, Python syntax errors, the
static analyzer, Pydantic validation, rate-limit handling, and graceful
fallback when the AI response fails validation.

**Manual integration test against the real Gemini API** (optional, uses
your quota):

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"code":"def calculate_average(numbers):\n    return sum(numbers) / len(numbers)\n","language":"python","difficulty":"beginner"}'
```

## 14. Docker Setup

```bash
cp .env.example .env   # fill in GEMINI_API_KEY
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

The Gemini key is passed through environment variables at container
runtime — it is never written into any Dockerfile or image layer.

## 15. Example Usage

Paste this buggy Python function:

```python
def calculate_average(numbers):
    return sum(numbers) / len(numbers)
```

Expected response shape (abbreviated):

```json
{
  "static_analysis": {
    "language": "python",
    "syntax_valid": true,
    "findings": [
      { "title": "Possible division by zero on empty input", "severity": "HIGH", "line": 2, "message": "..." }
    ],
    "fully_supported": true
  },
  "mentor": {
    "code_quality_score": 70,
    "bugs": [
      { "title": "Division by zero on empty input", "type": "runtime", "severity": "HIGH", "line": 2, "verified": true, "problem": "...", "explanation": "...", "suggested_fix": "..." }
    ],
    "fixed_code": "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)\n",
    "tests": "def test_normal(): ...\ndef test_empty(): ...",
    "learning_points": ["Always validate input before dividing"],
    "next_exercise": "Modify the function to also handle a list containing non-numeric values."
  }
}
```

Because the static analyzer also independently flagged line 2, that bug is
marked `"verified": true` — a real, non-AI-guessed confirmation.

## 16. API Documentation

- `GET /api/health` — service + Gemini configuration status.
- `POST /api/analyze` — full analysis. Body: `{ code, language, difficulty, question? }`.
- `POST /api/analyze/python` — convenience alias, rejects non-Python requests.
- `POST /api/hint` — a single short hint without revealing the fix. Body: `{ code, language, difficulty }`.

Full interactive schema available at `/docs` (Swagger UI) once the backend is running.

## 17. Security Limitations

- **User-submitted code is never executed** inside the FastAPI process.
- Optional AI-generated test execution (`app/services/test_service.py`) is
  **disabled by default** (`ENABLE_CODE_EXECUTION=false`). If you enable it,
  it runs in a subprocess with a 10-second timeout, a fresh temp directory,
  and a stripped environment (no inherited secrets) — but this still does
  **not** provide OS-level sandboxing (no seccomp, no network isolation, no
  resource limits beyond the timeout). Only enable it inside a container
  you have locked down yourself; do not enable it on a shared or
  internet-facing host.
- The Gemini API key lives only in backend environment variables. It is
  never sent to, or readable from, the frontend, and is never logged.
- CORS is restricted to `FRONTEND_URL`. Request and code size are capped
  (`MAX_REQUEST_SIZE`, `MAX_CODE_SIZE`) and oversized requests are rejected
  with `413`.
- Error responses never leak stack traces, environment variables, or the
  API key.

## 18. Gemini Free-Tier Limitations

The free tier of the Gemini Developer API is **not unlimited**. Google
enforces requests-per-minute and requests-per-day caps that vary by model
and change over time — check the current limits on the AI Studio pricing
page. When you hit a limit, the app returns HTTP `429` with the message
"Free AI API limit reached. Please wait and try again." after a small
bounded number of automatic retries with exponential backoff (no
indefinite retry loops).

## 19. Troubleshooting

| Problem | Fix |
|---|---|
| `503` from `/api/analyze` | `GEMINI_API_KEY` is missing/empty in `backend/.env`. Restart the backend after setting it. |
| `429` responses | You've hit the free-tier rate limit. Wait a minute and retry. |
| Frontend can't reach backend | Check `VITE_API_URL` in `frontend/.env` matches where uvicorn is running, and that `FRONTEND_URL` in `backend/.env` matches the Vite dev server URL (CORS). |
| `ModuleNotFoundError: google.generativeai` | Run `pip install -r requirements.txt` inside your activated virtualenv. |
| Tests fail with import errors | Run `pytest` from inside `backend/` (it uses `pytest.ini`'s `pythonpath = .`). |
| Monaco editor doesn't load | Run `npm install` again in `frontend/`; check the browser console for a blocked CDN/network error. |
| "AI response could not be validated" (`analysis_status: partial`) | Rare — the model returned malformed JSON even after one retry. Click Analyze again. |

## 20. Future Improvements

- Real static analyzers for JavaScript/TypeScript/Java/C/C++ (currently AI-only for these).
- Streaming responses so bug-by-bug results appear as they're generated.
- Optional Dockerized, network-isolated sandbox for full test execution.
- User accounts and analysis history.
- Side-by-side diff view instead of a separate "fixed code" panel.
- Support for multi-file projects instead of a single code block.

---

**This is not a tutorial or partial scaffold** — every file listed in the
project structure above contains complete, runnable code. The backend's
23 tests pass with `pytest -q`, and the frontend builds cleanly with
`npm run build`.
