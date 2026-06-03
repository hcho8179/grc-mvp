# Routes

| Module | Mounted | Purpose |
|--------|---------|---------|
| `auth.py` | Yes (`/api/auth/*`) | Register, login, JWT + CSRF cookies |
| `api.py` | Yes (`/api/*`) | JSON API for the React frontend |
| `admin.py` | Yes (`/admin/*`) | Operator admin endpoints |

Legacy HTMX route modules (`questionnaires.py`, `knowledge.py`, `dashboard.py`, `answers.py`) were removed — all product routes live in `api.py`.
