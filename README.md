# Property Transactions Mini-Pipeline

A small script that cleans a messy property-transactions dataset, plus a tiny HTTP
API that serves summaries and a thin dashboard. One Docker command runs UI + API
together on a single port.

> **Synthetic data.** `condo_transactions_raw.csv` is generated in-repo
> (`generate_raw.py`, deterministic seed 42) and is deliberately messy: it is
> built to exercise every documented messiness rule below. It is not real
> transaction data, and any reference `summary.json` will not match.

## Quick start (Docker — the only command you need)

```bash
docker compose up --build
```

Then:

```bash
open http://localhost:8000            # the dashboard
curl http://127.0.0.1:8000/health     # {"status":"ok"}
curl http://127.0.0.1:8000/projects   # project list
```

The image builds the Next.js UI as a static export and serves it from the same
FastAPI process, so the browser hits `/projects`, `/estimate`, etc. on the same
origin — no CORS needed in Docker.

## Fallback (no Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Optional local frontend dev (uses `http://localhost:3000`; the API enables CORS
for that origin only):

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## API

| Path | Description |
|---|---|
| `GET /projects` | `{project_name, district, transaction_count, median_psf}[]`, sorted by name |
| `GET /projects/{name}` | Full project object. `?year=2025` overrides `transaction_count`, `median_psf`, `median_price` for that year; other fields stay full-history. Lookup is casefold + trimmed + whitespace-collapsed; unknown → 404 `{"error":"unknown_project",...}` |
| `GET /estimate?project=&area_sqft=` | Estimated price = median psf × area, over the trailing 12 months relative to the latest sale date. Returns `estimated_price`, `psf_used`, `n_transactions`, and the window |
| `GET /health` | `{"status":"ok"}` |

## Cleaning rules (in spec order)

1. Deduplicate on `transaction_id` — keep the **first** occurrence.
2. `project_name`: trim, collapse internal whitespace, Title Case.
3. `district` → `D` + two digits (`5` → `D05`, `D19` → `D19`).
4. `price` → integer dollars; unparseable → exclude `invalid_price`.
5. `area` → `area_sqft` (`1 sqm = 10.7639 sqft`); blank → exclude `missing_area`.
6. `psf = price / area_sqft`; outside 500–6000 → exclude `outlier_psf`.
7. `sale_date` → ISO `YYYY-MM-DD` (`%Y-%m-%d`, `%d/%m/%Y`, `%d %b %Y`).
8. `sale_type` → Title Case (`Resale`, `New Sale`, `Sub Sale`).

Each excluded row gets **exactly one** reason, applied price → area → psf.

```bash
python clean.py        # regenerates clean_transactions.csv + summary.json
python generate_raw.py # regenerates the raw CSV (already committed; not needed by reviewers)
```

## Assumptions / judgement calls

- **First duplicate wins**; later duplicates are dropped before any other rule.
- **Title case** uses `str.title()` after whitespace collapse (matches the
  `the orchid residences` → `The Orchid Residences` example).
- **Price parsing**: strip `S$` / `$` / commas / spaces; accept whole-dollar
  numbers; reject leftover junk (e.g. `TBC`, `n/a`, `1.5M`).
- **Area parsing**: regex matches `sqft` / `sq ft` / `sqm` / `sq m` (with `.`
  variants); unlabelled bare numbers are assumed sqft.
- **Unparseable dates are not an official exclude reason** — the generator only
  emits the three formats, so the cleaner logs/skips only if that ever happens.
- **Medians** use Python's `statistics.median`; even counts average the two
  middle values. All medians round to 2 decimals.
- **Years** (year filter and top-5) use the calendar year of `sale_date`.
- **`top5_projects_by_median_psf_2025`** is highest-first using each project's
  2025 by-year median; projects with no 2025 sales are skipped.

## About the estimate

`/estimate` is intentionally **naive**: it multiplies area by the project's median
PSF over the trailing 12 months. It ignores bedrooms, floor level, time decay,
renovation state, and comparables, and it uses a simple calendar-12-month window.
Good enough for a demo, not for pricing advice.

## Scaling note (5M rows / nightly crawler)

This reads the full CSV into memory at startup — right for a 1,900-row demo, wrong
for a 5M-row nightly crawl. The first change would be to **stop rewriting full
files**: incremental load with `?after={id}` markers, stored aggregates that get
updated per batch instead of recomputed from scratch, and a real warehouse/DB as
the source of truth instead of re-parsing a flat file. The cleaning rules and
aggregation math here would stay, but they would operate on deltas, not full
dumps.

## Development

- Tests: `pytest` (68 tests — cleaning, summary, API).
- Do **not** commit `.venv/` or `frontend/node_modules/` (gitignored). The
  Docker build installs both inside the image.
- `app/cleaning.py` is pure and unit-tested; `app/summary.py` holds the
  aggregations; `app/main.py` loads the clean CSV at startup and mounts the UI.

## Repo layout

```
clean.py                       CLI: raw CSV -> clean CSV + summary.json
generate_raw.py                one-shot generator (output is committed)
app/cleaning.py                pure parse/normalize/exclude functions
app/summary.py                 aggregations + rounding
app/main.py                    FastAPI app (load CSV at startup, mount UI)
app/api/projects.py            /projects, /projects/{name}, /estimate, /health
app/store.py                   in-memory dataset + summary
frontend/                      Next.js viewer (output: 'export')
tests/                         cleaning + summary + API tests
Dockerfile, docker-compose.yml one-container build
condo_transactions_raw.csv     committed synthetic messy data (1,910 rows)
clean_transactions.csv         committed cleaned output
summary.json                   committed aggregations
```