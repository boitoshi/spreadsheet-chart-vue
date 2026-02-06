# Repository Guidelines

## Project Structure & Modules
- `web-app/frontend/`: Vue 3 + Vite app (`src/components`, `views`, `router`, `composables`).
- `web-app/backend/`: Django REST backend (`sheets/`, `portfolio/`, `reports/`, `templates/`).
- `scripts/`: API health checks (`api_health_check.py`, `api_health_check.sh`).
- `data-collector/`: Python utilities (uv workspace member).
- `docs/`: Report templates and documentation.

## Build, Test, and Dev Commands
Frontend (Vite on 3000):
```bash
cd web-app/frontend
npm install
npm run dev       # local dev
npm run build     # production build
npm run preview   # serve build
npm run type-check
```
Backend (Django on 8000):
```bash
cd web-app/backend
pip install -e .[dev]  # or: pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# Health check (set BASE_URL if not localhost:8000)
python ../../scripts/api_health_check.py
```

## Coding Style & Naming
- Python: ruff + mypy (Py3.12), max line length 88, import sorting enabled. Prefer type hints and small, focused functions.
- Django: app modules under `sheets/`, `portfolio/`, `reports/`; API paths under `/api/v1/…`.
- Vue/TS: 2‑space indent; `.vue` components PascalCase (e.g., `PortfolioDashboard.vue`); composables `useXxx.ts`; utilities in `src/utils/`.
- Env: never commit secrets; use `.env` files like `web-app/backend/.env` and `VITE_*` vars for frontend.

## Testing Guidelines
- Backend: pytest + pytest‑django configured. Run:
```bash
cd web-app/backend
pytest -q
```
- Frontend: no test runner configured; keep logic in composables and add unit tests if introducing complex code.
- CI smoke: `scripts/api_health_check.*` validates key endpoints.

## Commit & Pull Requests
- Commits: prefer Conventional Commits (e.g., `feat: add monthly report API`, `fix: handle missing ticker`); present tense, concise scope.
- PRs must include:
  - Purpose and context; link related Issues.
  - Screenshots or curl output for API/UI changes.
  - Steps to test locally (frontend/backend), and any migration notes.
  - Checklist: type-check passes, `ruff` clean, backend `pytest` green, health check OK.

## Security & Config Tips
- Required vars: `SPREADSHEET_ID`, `GOOGLE_APPLICATION_CREDENTIALS` (backend), `VITE_API_BASE_URL` (frontend).
- Keep service account JSON out of VCS; reference via absolute path in `.env`.
- Sanitize logs; avoid printing sensitive portfolio data in debug output.

