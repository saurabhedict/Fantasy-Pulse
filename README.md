# Fantasy Pulse

Watch what's happening to *your* fantasy cricket team, over by over, and why.
**Python computes every number; the LLM only explains them.**

```
Streamlit UI  --HTTP-->  FastAPI  -->  services  -->  domain  (pure Python: scoring, timeline, status)
 (frontend/)             (api/)                  -->  ai      (LangGraph pipeline + LangGraph chat agent)
                                                 -->  repositories (Cricsheet JSON)
```
Dependencies only point downward. `domain/` imports no framework, so it is tested in milliseconds.

## Project layout
```
backend/
  app/
    main.py              FastAPI app, CORS, error handler
    core/                config.py (env settings), errors.py
    api/                 deps.py (wiring), routes/{health,matches,pulse,chat}.py   <- thin, no logic
    schemas/             Pydantic request/response models + validation
    services/            match / pulse / chat orchestration
    domain/              timeline.py, scoring.py, status.py, context.py            <- no frameworks
    ai/                  llm.py, prompts.py, fallback.py, explain.py,
                         graphs/pulse_graph.py   (LangGraph pipeline)
                         agents/{chat_agent,tools}.py   (LangGraph ReAct agent)
    repositories/        match_repo.py (loads + caches Cricsheet JSON)
    data/matches/        match JSON files (sample_match.json is synthetic)
  tests/                 domain + API tests (17)
frontend/                app.py (Streamlit), api_client.py (httpx)
scripts/                 make_sample_match.py
```

## Run locally (two terminals)
```bash
# 1) backend
cd backend
pip install -r requirements-dev.txt
cp .env.example .env            # put GROQ_API_KEY or GOOGLE_API_KEY in it (optional)
uvicorn app.main:app --reload   # http://localhost:8000/docs  <- interactive API docs

# 2) frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py            # http://localhost:8501
```
Without an LLM key everything works except chat; explanations use a template fallback.
Run tests: `cd backend && pytest`.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + whether an LLM is configured |
| GET | `/matches` | list matches |
| GET | `/matches/{id}` | players, total steps, step labels |
| GET | `/matches/{id}/sample-team` | demo XI + captain + vice-captain |
| POST | `/pulse` | team + `step` -> score, fan points, change, explanation, chart history |
| POST | `/chat` | team + `step` + `messages` -> agent reply (503 if no LLM key) |

The API is stateless: the UI sends the team and step on every call.
```bash
curl -s localhost:8000/matches/sample_match/sample-team       # grab a valid team, then:
curl -s -X POST localhost:8000/pulse -H 'content-type: application/json' \
  -d '{"match_id":"sample_match","xi":[...11 names...],"captain":"..","vc":"..","step":16}'
```

## Use a real match
Download a T20 JSON from https://cricsheet.org/downloads/ into `backend/app/data/matches/`
(the filename, without `.json`, is the match id). Matches with super overs are supported: the super over is skipped.

## Deploy
1. **Backend** (Render / Railway / Hugging Face Spaces / any Docker host): root dir `backend`,
   start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, env vars `GROQ_API_KEY` (or
   `GOOGLE_API_KEY`) and `CORS_ORIGINS=<your streamlit url>`. A `Dockerfile` is included (not tested here).
2. **Frontend** (Streamlit Community Cloud): main file `frontend/app.py`, secret `API_URL = "https://<your-backend>"`.
3. Pin dependency versions once it works. Free hosts sleep when idle: open `/health` before a demo to wake the backend.

## Notes
- Scoring is **simplified** (runs, 4s/6s, 30/50/100 bonuses, wickets, fielding, ducks; C 2x, VC 1.5x). Say so in the submission note.
- `create_react_agent` shows a deprecation warning on LangGraph 1.x (it moved to `langchain.agents.create_agent`). It still works.
