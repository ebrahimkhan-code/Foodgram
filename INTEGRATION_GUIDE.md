# Foodgram — Full-Stack Run & Member 2 (RAG/LLM) Integration Guide

Foodgram recommends dishes from a real Lahore restaurant menu dataset. It now
fuses two engines:

- **Member 1** — the recommendation engine. Decides **WHAT** to recommend
  (Taste DNA from the "this-or-that" game → ranked dishes). Python/Flask on
  port **8000**, with a dependency-free Node CSV fallback so cards always render.
- **Member 2** — the Data/RAG/LLM layer. Explains **WHY** each dish fits, in
  grounded natural language, and powers semantic search / food Q&A. FastAPI on
  port **8001** (ChromaDB + sentence-transformers + an OpenRouter LLM).

The Node/Express backend (port **5000**) orchestrates both and serves the React
frontend. The frontend only ever talks to the backend (single origin).

```
                         ┌─────────────────────────────┐
   React frontend  ──▶   │  Node/Express backend :5000 │
   (CRA, proxy→5000)     │                             │
                         │  • ranks via Member 1       │──▶ Member 1 Flask :8000
                         │  • enriches reasons +       │──▶ Member 2 FastAPI :8001
                         │    /ask /search via Member 2│      (RAG + OpenRouter LLM)
                         │  • Postgres (users/fav/ord) │──▶ PostgreSQL :5432
                         └─────────────────────────────┘
```

If Member 2 is offline, recommendations still work — cards fall back to the
generic reason and the "Ask Foodgram" box shows a soft "assistant offline" note.
If Member 1's Flask is offline, the Node CSV fallback still ranks dishes.

---

## Prerequisites

- **Node.js 18+** (backend uses global `fetch`)
- **Python 3.10+** for both Member 1 and Member 2
- **PostgreSQL** running locally (DB `foodgram`; the backend auto-creates its tables on boot)
- An **OpenRouter API key** for Member 2's LLM explanations (free models available at openrouter.ai/models)

---

## One-time setup

### 1. Backend (Node)

```bash
cd backend
npm install
# backend/.env already holds DB creds + MEMBER1_API_URL + MEMBER2_API_URL.
```

### 2. Member 1 (Flask recommender)

```bash
cd backend/python-service
python -m venv venv
venv\Scripts\activate        # Windows   (source venv/bin/activate on mac/linux)
pip install -r requirements.txt
```

### 3. Member 2 (RAG/LLM FastAPI)

```bash
cd member2_data_rag_llm
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Then set the LLM key in `member2_data_rag_llm/.env`:

```
OPENROUTER_API_KEY=sk-or-...your key...
```

(The server auto-loads this `.env` on startup via python-dotenv. Without a valid
key, Member 2 still boots for `/search` but explanation/Q&A LLM calls fail and
the app cleanly falls back.)

### 4. Frontend (React / CRA)

```bash
cd frontend
npm install
```

---

## Start everything (4 terminals)

| # | Service | Command | Port |
|---|---------|---------|------|
| 1 | PostgreSQL | (your local Postgres service) | 5432 |
| 2 | Member 1 Flask | `cd backend/python-service && MEMBER1_PORT=8000 python app.py` | 8000 |
| 3 | Member 2 FastAPI | `cd member2_data_rag_llm && python api_server.py` | 8001 |
| 4 | Node backend | `cd backend && npm start` | 5000 |
| 5 | Frontend | `cd frontend && npm start` | 3000 |

> On Windows PowerShell, set env vars with `$env:MEMBER1_PORT=8000` before the
> command, or just run `python app.py` (Member 1 defaults to 8000, Member 2 to 8001).

Open http://localhost:3000. Play the taste game → land on **Discover**. Each
"For You" card's reason line is now written by Member 2's LLM, grounded in the
dish's knowledge document. Use the **Ask Foodgram** box to search in plain
English ("a spicy vegetarian dish under Rs. 800").

---

## What was integrated (code map)

- `member2_data_rag_llm/api_server.py` — fixed bind host (`128.0.0.1`→`127.0.0.1`),
  moved to configurable port (default **8001**, no longer clashes with Member 1),
  added `load_dotenv()` and permissive dev CORS.
- `backend/src/services/member2Service.js` — Node HTTP client for Member 2
  (`explainRecommendation`, `search`, `ask`, `askSpecific`, `healthCheck`),
  global `fetch` + `AbortController` timeouts, feature-flagged via `MEMBER2_ENABLED`.
- `backend/server.js`:
  - `enrichRecommendations()` — after Member 1 ranks, the top cards are enriched
    with Member 2 explanations **in parallel** (`Promise.allSettled`) under a
    tight timeout; failures keep the generic reason. Wired into both
    `POST /api/game/responses` and `GET /api/recommendations`.
  - New proxy routes: `POST /api/ask`, `GET /api/search`,
    `GET /api/food/:foodId/explain`, `GET /api/member2/health`.
- `backend/.env` — `MEMBER2_API_URL`, `MEMBER2_TIMEOUT`, `MEMBER2_ENABLED`, and
  explanation caps.
- `frontend/src/pages/Recommendations.jsx` + `App.css` — the "Ask Foodgram"
  natural-language search/Q&A bar.

### Why food_ids line up
Member 1 and Member 2 were built from the same scrape, so both use the same
`food_id` scheme (e.g. `x8l5__beef-gyro`). That's what lets Member 2 explain a
dish that Member 1 picked — no ID translation needed.

---

## Endpoint reference (Member 2 via backend)

| Backend route | Proxies Member 2 | Purpose |
|---------------|------------------|---------|
| `POST /api/ask` | `POST /ask` | Open-ended RAG food Q&A → `{answer, sources}` |
| `GET /api/search?query=…` | `GET /search` | Semantic search + filters → `{results}` |
| `GET /api/food/:id/explain?query=…` | `POST /ask-specific` | Ask about one dish |
| `GET /api/member2/health` | `GET /health` | Is the RAG service reachable? |

All are public (menu data isn't sensitive) and return `available: false` (never
an error) when Member 2 is down, so the UI degrades gracefully.

---

## Troubleshooting

- **Cards show generic reasons, no LLM text** → Member 2 not running, or
  `OPENROUTER_API_KEY` missing/invalid. Check `GET http://localhost:5000/api/member2/health`.
- **Port 8000 conflict** → Member 1 Flask and Member 2 must not share a port;
  Member 2 defaults to 8001 now.
- **`Set OPENROUTER_API_KEY` on Member 2 startup** → put the key in
  `member2_data_rag_llm/.env` (auto-loaded) or export it in the shell.
- **First Member 2 request is slow** → sentence-transformers loads the embedding
  model on first use; subsequent calls are fast.

