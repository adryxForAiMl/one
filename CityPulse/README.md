# CityPulse

CityPulse is a hackathon prototype for a glanceable civic pulse dashboard focused on Rajasthan. It combines a real Open-Meteo weather observation when reachable with synthetic transit and 311-style reports. A seeded Jaipur scenario guarantees a visible cross-feed pattern for the demo. Correlations are explicitly presented as possible links, not confirmed causes.

## Requirements

- macOS with Python 3.10+ and Node.js 20.9+
- Network access is optional at runtime; if Open-Meteo is unavailable, CityPulse uses a labelled synthetic weather fallback.

## Run the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8010
```

The API is at `http://localhost:8010`; interactive API docs are at `http://localhost:8010/docs`.

## Run the frontend

In a second terminal from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend defaults to the API at `http://localhost:8010`; set `NEXT_PUBLIC_API_URL` before starting it to use another API origin.

## Demo controls

```bash
curl -X POST http://localhost:8010/api/debug/feed/transit/toggle \
  -H 'Content-Type: application/json' -d '{"down":true}'
```

Revive the feed with `{"down":false}`. Use the dashboard replay control or `GET /api/replay?range=24h` to replay the seeded scenario.

## Data and interpretation

- Weather: Open-Meteo current precipitation, with a clearly labelled local synthetic fallback.
- Transit delays and complaints: generated synthetic events, not reports from a real agency or residents.
- Zones: illustrative city-center markers for Ajmer, Jodhpur, and Jaipur; scenario reports are synthetic, not official city reports.
- The pulse score is a relative activity indicator, not a calibrated risk probability or official alert.
- The API stores its rolling 24-hour window in memory; events reset when the backend restarts.

Run backend checks with `cd backend && .venv/bin/python -m pytest`.