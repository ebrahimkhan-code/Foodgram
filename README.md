# Foodgram 🍽️

An AI‑powered food discovery app for Lahore restaurants. Foodgram learns your taste
through a quick "this‑or‑that" photo game, ranks dishes for you with a machine‑learning
recommender, and can explain *why* each dish was picked and answer free‑text food
questions — all grounded in a real menu dataset scraped from local restaurants.

The system fuses two teammate components behind one Node backend:

- **Member 1 — the recommender (WHAT to eat).** A Flask service wrapping a logistic‑regression
  model that ranks dishes against your Taste DNA.
- **Member 2 — the RAG/LLM layer (WHY & Q&A).** A FastAPI service using ChromaDB + sentence
  embeddings + an LLM to produce grounded explanations and answer natural‑language questions.

When either Python service is offline, the backend transparently falls back to a
dependency‑free Node recommender/search over the same enriched menu CSV, so the core
experience (recommendations, search, "Ask Foodgram") keeps working with real dish images.

---

## Architecture

```
                          ┌─────────────────────────────────────────────┐
  React CRA frontend      │              Node / Express backend          │
  (dev :3000)             │                    (:5000)                   │
        │  /api/* ───────►│  PostgreSQL (:5432)  ·  auth (JWT + bcrypt)   │
        │  (CRA proxy)    │                                              │
        │                 │   ┌── primary ──►  Member 1 Flask  (:8000)   │
        │                 │   │                (ranking / Taste DNA)      │
        │                 │   ├── primary ──►  Member 2 FastAPI (:8001)  │
        │                 │   │                (explanations / RAG / Q&A) │
        │                 │   └── fallback ─►  catalogRecommender.js      │
        │                 │                    (Node, reads enriched CSV) │
        └─────────────────┴─────────────────────────────────────────────┘
```

- The frontend only ever talks to the Node backend (`/api/*`), proxied to `:5000` in dev.
- The backend calls Member 1 and Member 2 over HTTP. Both live in their own directories
  and are optional — if unreachable/disabled, the backend degrades gracefully (see below).

---

## Repository layout

```
Foodgram/
├── frontend/                     React (Create React App) client
│   ├── src/pages/                Home (photo game), Recommendations, FoodDetail, ...
│   └── package.json              "proxy": "http://localhost:5000"
├── backend/                      Node / Express API (the hub)
│   ├── server.js                 Main server — all /api/* routes live here
│   ├── src/services/
│   │   ├── member1Service.js     HTTP client → Member 1 Flask
│   │   ├── member2Service.js     HTTP client → Member 2 FastAPI
│   │   └── catalogRecommender.js Dependency‑free CSV recommender/search (fallback)
│   ├── python-service/           Member 1 Flask wrapper
│   │   ├── app.py                Flask app (:8000) around the recommender library
│   │   ├── requirements.txt      flask, pandas, scikit‑learn, ...
│   │   └── venv/                 (create locally)
│   ├── member1-recommender/      Recommender library + assets
│   │   ├── models/logistic_regression.pkl
│   │   └── data/menu_dataset_enriched_claude_FINAL.csv   ← shared enriched menu
│   ├── .env                      backend config (not committed)
│   └── package.json
└── member2_data_rag_llm/         Member 2 FastAPI RAG/LLM service
    ├── api_server.py             FastAPI app (:8001)
    ├── rag_pipeline.py           ChromaDB + embeddings + LLM
    ├── chroma_db/                prebuilt vector store (collections: foods, food_knowledge)
    ├── food_knowledge_base.csv
    ├── requirements.txt          fastapi, chromadb, sentence-transformers, openai, ...
    └── .env                      Member 2 config (not committed)
```

> Note: `frontend/` also contains Vite scaffolding (`vite.config.js`, `main.jsx`), but the
> app is run with **Create React App** (`react-scripts`). The CRA dev server proxies to the
> backend on `:5000`; the Vite config has no such proxy, so prefer `npm start` (CRA).

---

## Prerequisites

- **Node.js 18+** (the backend uses the global `fetch`, available from Node 18).
- **Python 3.10+** (for Member 1 and Member 2).
- **PostgreSQL 13+** running locally.
- A **PostgreSQL database** the backend can connect to (created via the setup script below).
- For Member 2's full LLM answers: a valid **OpenRouter API key**.

---

## Setup

Clone the repo, then set up each component.

### 1. Backend (Node/Express + PostgreSQL)

```bash
cd backend
npm install
# create the schema and (optionally) seed data:
npm run db:setup      # = create-db + seed
```

Create `backend/.env` (see **Environment variables** below).

### 2. Member 1 — Flask recommender

```bash
cd backend/python-service
python -m venv venv
# Windows:  venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
```

### 3. Member 2 — FastAPI RAG/LLM

```bash
cd member2_data_rag_llm
python -m venv venv
# activate it (see above), then:
pip install -r requirements.txt
```

Create `member2_data_rag_llm/.env` with your LLM key (see below). The ChromaDB vector
store under `chroma_db/` is prebuilt, so no embedding step is required to start.

### 4. Frontend (React CRA)

```bash
cd frontend
npm install
```

---

## Environment variables

Values are omitted here on purpose — set them in the appropriate `.env` file. **Never commit
`.env` files or share secret values.**

### `backend/.env`

| Variable | Purpose |
|---|---|
| `DB_USER`, `DB_HOST`, `DB_NAME`, `DB_PORT` | PostgreSQL connection |
| `DB_PASSWORD` | PostgreSQL password (secret) |
| `PORT` | Backend port (default `5000`) |
| `JWT_SECRET` | Secret used to sign auth tokens (secret) |
| `MEMBER1_API_URL` | Base URL of the Member 1 Flask service (e.g. `http://localhost:8000`) |
| `MEMBER1_TIMEOUT` | Member 1 request timeout (ms) |
| `MEMBER2_API_URL` | Base URL of the Member 2 FastAPI service (e.g. `http://localhost:8001`) |
| `MEMBER2_TIMEOUT` | Member 2 request timeout (ms) |
| `MEMBER2_EXPLAIN_TIMEOUT` | Per‑dish explanation timeout (ms) |
| `MEMBER2_ENABLED` | `true`/`false` — set `false` to fully bypass Member 2 (recs still work) |
| `MEMBER2_EXPLAIN_MAX` | Max "For You" cards to enrich with LLM explanations |
| `MEMBER2_EXPLAIN_EXPLORE_MAX` | Max "Discover" cards to enrich with LLM explanations |

### `member2_data_rag_llm/.env`

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | OpenRouter key for the LLM (secret). **Required** for Member 2 to boot — the RAG pipeline raises on startup if it's missing. |
| `GEMINI_API_KEY` | Optional alternate LLM provider key (secret) |
| `MEMBER2_PORT` | Member 2 port (default `8001`) |

### Member 1 (Flask)

Start it with `MEMBER1_PORT=8000` so it doesn't collide with the backend on `:5000`
(see the run commands below).

---

## Running the app

Start the services in separate terminals. The two Python services are **optional** —
the backend falls back to the local CSV recommender if they're down — but you'll want
them for real ML ranking and full LLM explanations.

```bash
# 1) PostgreSQL — make sure it's running and the DB from db:setup exists

# 2) Member 1 (Flask recommender) — from backend/python-service (venv active)
MEMBER1_PORT=8000 python app.py            # → http://localhost:8000

# 3) Member 2 (FastAPI RAG/LLM) — from member2_data_rag_llm (venv active)
MEMBER2_PORT=8001 python api_server.py     # → http://localhost:8001

# 4) Backend (Node/Express) — from backend/
npm run dev        # nodemon, or:  npm start        # → http://localhost:5000

# 5) Frontend (React CRA) — from frontend/
npm start                                   # → http://localhost:3000
```

Then open **http://localhost:3000**, play the photo taste game, and view your
recommendations. On Windows, set the port env vars with `set MEMBER1_PORT=8000` (cmd)
or `$env:MEMBER1_PORT="8000"` (PowerShell) before the `python` command.

---

## Key API endpoints (backend, `:5000`)

All routes are served by `backend/server.js` and prefixed with `/api`.

**Taste game & recommendations**

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/game/questions` | Attribute/value question set for the classic quiz |
| `GET` | `/api/game/photo-rounds` | "This‑or‑that" photo rounds (real dish images) |
| `POST` | `/api/game/responses` | Submit game answers → Taste DNA + ranked recommendations |
| `GET` | `/api/recommendations` | Recommendations for a stored/derived Taste DNA |

Recommendations come back split into **For You** (`exploitation`) and **Discover**
(`exploration`) buckets — up to **12 + 12** cards, each with image, price, rating and a reason.

**Member 2 — explanations, search & Q&A**

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/ask` | Natural‑language food question → grounded answer + source dishes |
| `GET` | `/api/search` | Semantic/keyword dish search |
| `GET` | `/api/food/:foodId/explain` | "Ask about this dish" — explanation for one dish |
| `GET` | `/api/member2/health` | Member 2 availability probe |

**Accounts, favorites, orders**

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/auth/signup`, `/api/auth/login` | Register / sign in (JWT) |
| `GET` | `/api/auth/session-status` | Current session info |
| `GET` / `PUT` | `/api/users/me` | Read / update the signed‑in user |
| `GET` / `POST` / `DELETE` | `/api/favorites`[`/:foodId`] | Manage saved dishes |
| `GET` / `POST` | `/api/orders` | List / place orders |
| `POST` | `/api/checkout` | Checkout |
| `POST` | `/api/feedback` | Record like/dislike feedback on a dish |
| `GET` | `/api/foods`, `/api/foods/:id` | Browse the seeded catalog |
| `GET` | `/api/health` | Backend health check |

---

## Graceful degradation (CSV fallback)

The Member‑2‑dependent routes (`/api/ask`, `/api/search`, `/api/food/:id/explain`) and the
recommendation routes are designed to **never hard‑fail** when a Python service is offline:

- If **Member 1** (Flask) is unreachable, recommendations are produced by
  `catalogRecommender.js`, which ranks the enriched menu CSV against your taste profile —
  so cards still have real images, price and rating.
- If **Member 2** is disabled (`MEMBER2_ENABLED=false`) or unreachable, `/api/ask` and
  `/api/search` fall back to keyword/intent search over the same CSV (understands veg/non‑veg,
  spicy, sweet/dessert and price limits like "under Rs. 800"), and `/api/food/:id/explain`
  returns the dish description. These responses come back as `available: true` with real
  results instead of an "offline" message.
- Member 1 and Member 2 remain the **primary** path whenever they're reachable; the CSV is
  only a safety net.

This means you can demo and use the core app (game → recommendations → search → ask) with
**Node + PostgreSQL only**. The Python services add the real ML ranking and richer,
LLM‑grounded explanations.

---

## Notes & gotchas

- **Restart the backend after changing `server.js`** — Node doesn't hot‑reload it unless you
  run `npm run dev` (nodemon).
- **Recommendations are cached in the browser.** The Recommendations page reads
  `localStorage` first, so if you played the game before a change, you may keep seeing an
  old, smaller result set. Retake the quiz (the 🔄 button) or clear site data to refresh.
- **Ports must not collide.** Backend `:5000`, Member 1 `:8000`, Member 2 `:8001`, Postgres
  `:5432`, frontend dev `:3000`. Start Member 1 with `MEMBER1_PORT=8000` (its default would
  otherwise clash with the Node backend).
- **Member 2 needs `OPENROUTER_API_KEY` to boot.** Without a valid key the FastAPI service
  fails on startup, which the backend treats as "offline" (and falls back to the CSV).
- Member 1 and Member 2 share the same `food_id` scheme (e.g. `x8l5__beef-gyro`) and the same
  underlying Lahore menu data, so Member 2 can explain the exact dishes Member 1 ranks.

---

## Tech stack

**Frontend:** React 18 (Create React App), React Router 6, framer‑motion, axios, react‑icons.
**Backend:** Node/Express, PostgreSQL (`pg`), JWT + bcrypt, dotenv.
**Member 1:** Python, Flask, scikit‑learn (logistic regression), pandas.
**Member 2:** Python, FastAPI, ChromaDB, sentence‑transformers (`all‑MiniLM‑L6‑v2`), OpenRouter LLM.



