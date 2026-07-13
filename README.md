# ⛓ Bottleneck Agent

A stock-research agent that replicates **Serenity's (@aleabitoreddit)** selection logic:
reverse-engineer the AI-infrastructure and embodied-AI supply chains, find critical
chokepoints the market isn't watching yet, and surface asymmetric candidates — with the
**entire reasoning process visible in the UI**.

> Research/idea-generation tool only. Not financial advice.

## The method (five factors)

Each candidate is scored 0–1 on Serenity's framework, then combined with these weights:

| Factor | Weight | What the agent measures |
|---|---|---|
| Certain demand | 0.15 | Megatrend prior + live demand-confirmation headlines (capex, ramp, buildout) |
| Constrained supply | **0.25** | Structural chokepoint prior + live supply-stress headlines (shortage, lead time, sole supplier) |
| Low attention | **0.25** | Market cap (log), analyst coverage, media mention count, "already ran" penalty |
| Value capture | 0.20 | Gross margin (pricing power) + revenue growth (demand flow-through) |
| Catalyst | 0.15 | Catalyst headlines (contract, design win, guidance raise) + earnings proximity |

Supply and attention dominate on purpose: the edge is the chokepoint **before** institutional rotation.
Selection gates: supply ≥ 0.55 AND attention ≥ 0.35 (crowded or unconstrained names are rejected, with reasons logged).

## Pipeline (all visible in the UI)

1. **Map the supply chain** — 2 megatrends → 10 chokepoint segments → ~34 US-listed candidates (`app/knowledge.py`)
2. **Crawl live news** — Google News RSS per segment keyword + per-ticker headlines (no API key)
3. **Fetch market data** — yfinance: price, momentum, cap, analysts, margins, growth
4. **Score** — five factors, with per-factor evidence strings
5. **Rank & select** — conviction gates, rejects logged with reasons
6. **Write theses** — Claude API if `ANTHROPIC_API_KEY` is set, otherwise template engine

## Run it (Docker — recommended)

The app is containerized and ships with a **PostgreSQL 18.3** service. Run
history is stored in Postgres and persisted in a named Docker volume
(`pgdata`), so every research run is saved and survives restarts.

```bash
cp .env.example .env          # optional: set ANTHROPIC_API_KEY, etc.
docker compose up --build
# open http://localhost:8000  →  click "Run research"
```

The app waits for Postgres to become healthy before serving. History persists
across `docker compose down` / `up`. To wipe it, remove the volume:

```bash
docker compose down -v        # deletes the pgdata volume (history gone)
```

## Run it on Apple Containerization (mocker)

No Docker Desktop required. [`mocker`](https://github.com/us/mocker) is a
Docker-compatible CLI + Compose built on Apple's Containerization framework
(macOS 26+, Apple Silicon) — the same `docker-compose.yml` above runs as-is,
and its named `pgdata` volume persists run history under `~/.mocker/volumes/`.

```bash
brew tap us/tap && brew install mocker   # or build from source

cp .env.example .env                     # optional
mocker compose up -d                     # builds the app image + starts postgres:18.3
# open http://localhost:8000

mocker compose ps                        # status
mocker compose logs -f app               # tail app logs
mocker compose down                      # stop (keeps the pgdata volume → history saved)
```

If your `mocker` build doesn't build from a compose `build:` block, build the
image first and it'll be reused:

```bash
mocker build -t bottleneck-agent-app -f backend/Dockerfile .
```

## Run it (local, without Docker)

Needs a reachable Postgres. Point the app at it with `DATABASE_URL`:

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://bottleneck:bottleneck@localhost:5432/bottleneck
uvicorn app.main:app --port 8000
```

Optional (both run modes):

```bash
ANTHROPIC_API_KEY=sk-ant-...    # Claude writes the final theses (hybrid mode)
THESIS_MODEL=claude-sonnet-4-5  # thesis model override
DEMO_MODE=1                     # force offline sample data
```

If live feeds are unreachable the agent automatically falls back to bundled,
clearly-labeled sample data (`⚠ demo-fallback` badge in the UI; names tagged `[SAMPLE]`).

## API

- `POST /api/runs` — start a research run (background thread), returns `run_id`
- `GET /api/runs` — list runs with progress
- `GET /api/runs/{id}` — full result: stages, events, candidates, picks, theses
- `GET /api/knowledge` — the supply-chain map

## Extending it

- **New chokepoints/tickers** — edit `backend/app/knowledge.py` (themes → segments → tickers, priors, crawler keywords). Everything downstream adapts automatically.
- **Weights/gates** — `FACTOR_WEIGHTS` in `knowledge.py`, gates in `pipeline.py` stage 5.
- **Better data** — swap `market.py` for a paid real-time feed; add SEC EDGAR/earnings-call crawling in `crawler.py`.
- **Scheduling** — call `POST /api/runs` from cron for a daily scan (history accumulates in Postgres).

## Structure

```
backend/
  app/knowledge.py   supply-chain map + factor weights (the "brain"'s priors)
  app/crawler.py     Google News RSS + yfinance news
  app/market.py      market metrics + attention/value scoring
  app/pipeline.py    6-stage pipeline + full reasoning trace
  app/thesis.py      Claude-or-template thesis writer
  app/sampledata.py  labeled offline fallback data
  app/db.py          PostgreSQL run store (persistent history)
  app/main.py        FastAPI server + background run runner
  Dockerfile         backend image (also serves the frontend)
frontend/index.html  React UI (no build step): picks, reasoning pipeline,
                     candidate table, supply-chain map
docker-compose.yml   app + postgres:18.3 with a persistent pgdata volume
                     (runs on Docker or mocker/Apple Containerization)
```
