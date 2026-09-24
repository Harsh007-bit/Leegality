# Network Route Optimization API

FastAPI service to add network nodes/edges, find the lowest-latency path, and keep query history.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Endpoints

| Method | Path | Expected |
|---|---|---|
| `POST` | `/nodes` | `201` `{"id": 1, "name": "ServerA"}` |
| `POST` | `/edges` | `201` edge with `source`, `destination`, `latency` |
| `POST` | `/routes/shortest` | `200` `{"total_latency": 23.4, "path": [...]}` |
| `GET` | `/routes/history` | `200` recent successful queries |
| `GET` | `/nodes`, `/edges` | `200` list all |
| `DELETE` | `/nodes/{id}`, `/edges/{id}` | `204` |

Common errors: `400` invalid/missing/duplicate input, `404` no path or missing id.

## Example

```bash
curl -X POST http://127.0.0.1:8000/nodes -H "Content-Type: application/json" -d '{"name": "ServerA"}'
curl -X POST http://127.0.0.1:8000/nodes -H "Content-Type: application/json" -d '{"name": "ServerB"}'
curl -X POST http://127.0.0.1:8000/edges -H "Content-Type: application/json" \
  -d '{"source": "ServerA", "destination": "ServerB", "latency": 12.5}'
curl -X POST http://127.0.0.1:8000/routes/shortest -H "Content-Type: application/json" \
  -d '{"source": "ServerA", "destination": "ServerB"}'
```

## Tests

```bash
pytest
```

31 tests covering nodes, edges, shortest path, and history filters.
