# Promptarium — Backend

The FastAPI backend powering [Promptarium](https://promptarium.netlify.app), an AI prompt management dashboard. Handles authentication, per-user data ownership, prompt storage, and profile photo uploads.

🔗 **Live API:** [promptarium-backend.onrender.com](https://promptarium-backend.onrender.com)
🔗 **Interactive API docs:** [promptarium-backend.onrender.com/docs](https://promptarium-backend.onrender.com/docs)
🔗 **Frontend repo:** [github.com/Chirag-DATA/promptarium](https://github.com/Chirag-DATA/promptarium)

---

## Overview

This is a REST API built with FastAPI and PostgreSQL, designed to serve the Promptarium React frontend. It was built as a deliberate second phase of the project — the frontend originally ran entirely on browser `localStorage`, and was migrated to this real backend once its architecture was solid enough to swap the data layer without touching UI components.

The API handles:
- User signup and login via JWT
- Per-user profile management, including photo uploads
- Full CRUD on prompts, strictly scoped so users can only ever access their own data

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL |
| Auth | JWT (python-jose) + bcrypt password hashing (passlib) |
| File uploads | FastAPI's `UploadFile`, served via `StaticFiles` |
| Server | Uvicorn |
| Deployment | Render |

---

## Architecture

```
app/
├── main.py           → App instance, CORS config, static file mount, router registration
├── database.py         → Engine/session setup
├── models/               → SQLModel table definitions (User, Prompt)
├── schemas/                → Pydantic request/response shapes — deliberately separate from models
├── routers/                  → Route handlers, grouped by resource (auth.py, prompts.py)
├── auth/                       → Password hashing, JWT creation/verification, get_current_user dependency
└── static/uploads/               → Uploaded profile photos (gitignored; ephemeral on free-tier hosting)
```

### Key design principles

- **Models vs. schemas are deliberately separate.** `User` (the database model) includes `hashed_password`; `UserRead` (the API response schema) never does. `response_model` enforces this boundary on every route — no accidental leaking of sensitive fields.
- **Every prompt route requires authentication**, and ownership is checked centrally through one reusable function (`get_owned_prompt_or_404`) rather than duplicated per-route logic.
- **Missing or not-owned resources both return `404`, never `403`** — deliberately avoiding leaking whether a given resource ID exists at all to an unauthorized requester.
- **Passwords are never stored or logged in plain text** — hashed via bcrypt at signup, verified by re-hashing and comparison at login.
- **JWTs carry only a minimal, immutable claim** (the user's ID), and every protected request re-validates the user still exists in the database rather than trusting the token's claims blindly.
- **File uploads are validated before ever touching disk** — extension and size checks reject bad input early, and files are saved under server-generated UUID names, never trusting client-supplied filenames.

---

## API Endpoints

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/auth/signup` | Create a new account | No |
| POST | `/auth/login` | Log in, returns a JWT | No |
| GET | `/auth/me` | Get current user's profile | Yes |
| PATCH | `/auth/me` | Update username | Yes |
| POST | `/auth/me/photo` | Upload a profile photo | Yes |
| GET | `/prompts/` | List current user's prompts | Yes |
| POST | `/prompts/` | Create a prompt | Yes |
| GET | `/prompts/{id}` | Get a single prompt | Yes |
| PATCH | `/prompts/{id}` | Partially update a prompt | Yes |
| DELETE | `/prompts/{id}` | Delete a prompt | Yes |

Full interactive documentation (request/response schemas, live testing) is available at `/docs` on any running instance.

---

## Getting Started Locally

### Prerequisites
- Python 3.11+
- PostgreSQL installed and running locally

### Installation

```bash
git clone https://github.com/Chirag-DATA/promptarium-backend.git
cd promptarium-backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### Database setup

```sql
CREATE DATABASE promptarium;
```

### Environment configuration

Create a `.env` file at the project root:

```
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=promptarium
SECRET_KEY=generate_a_real_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Generate a real `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Run it

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

Tables are created automatically on startup via SQLModel's metadata — no manual migration step needed for a fresh database.

---

## Deployment

Deployed on [Render](https://render.com), with a Render-managed PostgreSQL instance.

**Build command:**
```
pip install -r requirements.txt
```

**Start command:**
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`) are configured directly in Render's dashboard, sourced from the connected PostgreSQL instance's connection details.

### Known limitation: ephemeral file storage

Uploaded profile photos are currently stored on the server's local filesystem. Render's free tier does not guarantee persistent disk storage across redeploys or restarts — uploaded photos may be lost when the service redeploys. Migrating to a persistent object storage service (e.g., Cloudinary, S3) would resolve this and is a natural next step.

---

## Roadmap

- [ ] Alembic migrations, replacing manual schema changes
- [ ] Persistent cloud storage for profile photos
- [ ] Refresh tokens / longer-lived sessions
- [ ] Rate limiting on auth endpoints

---

## Related Repository

The frontend — React, Vite, Tailwind — lives in a separate repository: [promptarium](https://github.com/Chirag-DATA/promptarium).

---

## Author

**Chirag Mittal**
- GitHub: [@Chirag-DATA](https://github.com/Chirag-DATA)
- LinkedIn: [mittal-chirag](https://linkedin.com/in/mittal-chirag)

---

## License

This project is open source and available under the [MIT License](LICENSE).
