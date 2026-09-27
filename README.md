# Promptarium — Backend

The FastAPI backend powering [Promptarium](https://promptarium.netlify.app/), an AI prompt management dashboard[cite: 1]. Handles authentication with email verification, sliding session management, account deletion, per-user prompt ownership, and profile photo uploads[cite: 1].

🔗 **Live API:** [promptarium-backend.onrender.com](https://promptarium-backend.onrender.com/)[cite: 1]  
🔗 **Interactive API docs:** [promptarium-backend.onrender.com/docs](https://promptarium-backend.onrender.com/docs)[cite: 1]  
🔗 **Frontend repo:** [github.com/Chirag-DATA/promptarium](https://github.com/Chirag-DATA/promptarium)[cite: 1]

#### Overview

This is a REST API built with FastAPI and PostgreSQL (hosted on Neon/Render), designed to serve the Promptarium React frontend[cite: 1, 3]. It was built as a deliberate second phase of the project — the frontend originally ran entirely on browser `localStorage`, and was migrated to this real backend once its architecture was solid enough to swap the data layer without touching UI components[cite: 1].

The API handles:
* User signup and login protected by rate limiters[cite: 1]
* Email verification via 6-digit OTP codes for new registrations
* 7-day session persistence using secure, `httpOnly` refresh token cookies
* Permanent self-service account deletion guarded by email OTP verification
* Per-user profile management, including photo uploads[cite: 1]
* Full CRUD on prompts, strictly scoped so users can only ever access their own data[cite: 1]

#### Tech Stack

| Layer | Technology |
| ------ | ------ |
| Framework | FastAPI[cite: 1] |
| ORM | SQLModel (SQLAlchemy + Pydantic)[cite: 1] |
| Database | PostgreSQL (Neon / Render)[cite: 1, 3] |
| Auth & Sessions | JWT (`python-jose`) + bcrypt password hashing (`passlib`) + `httpOnly` Refresh Cookie[cite: 1] |
| Rate Limiting | In-memory sliding window rate limiter |
| Email Service | Brevo REST API (HTTPS port 443) with Gmail SMTP fallback |
| File uploads | FastAPI's `UploadFile`, served via `StaticFiles`[cite: 1] |
| Server | Uvicorn[cite: 1] |
| Deployment | Render[cite: 1] |

#### Architecture

##### Key design principles
* **Models vs. schemas are deliberately separate.** `User` (the database model) includes `hashed_password` and OTP secrets; `UserRead` (the API response schema) never does[cite: 1]. `response_model` enforces this boundary on every route — no accidental leaking of sensitive fields[cite: 1].
* **Dual-Token Session Persistence.** Access tokens are short-lived (30 minutes) for authorized requests, paired with a long-lived 7-day refresh token stored in an `httpOnly`, cross-origin (`SameSite=None`, `Secure`) cookie[cite: 1].
* **Firewall-Resilient Email Delivery.** Bypasses cloud platform egress blocks on standard SMTP ports (25, 465, 587) on free containers by dispatching transactional OTP emails over HTTPS (port 443) using Brevo’s REST API.
* **Referential Integrity & Cascading Purges.** Foreign keys enforce `ON DELETE CASCADE` across `promptlike` and `prompt`. Account deletion purges user likes, prompt entries, and uploaded avatars cleanly without database integrity errors.
* **Every prompt route requires authentication**, and ownership is checked centrally through one reusable function (`get_owned_prompt_or_404`) rather than duplicated per-route logic[cite: 1].
* **Missing or not-owned resources both return 404, never 403** — deliberately avoiding leaking whether a given resource ID exists at all to an unauthorized requester[cite: 1].
* **Passwords are never stored or logged in plain text** — hashed via bcrypt at signup, verified by re-hashing and comparison at login[cite: 1].
* **JWTs carry only a minimal, immutable claim** (the user's ID), and every protected request re-validates the user still exists in the database rather than trusting the token's claims blindly[cite: 1].
* **File uploads are validated before ever touching disk** — extension and size checks reject bad input early, and files are saved under server-generated UUID names, never trusting client-supplied filenames[cite: 1]. The upload directory is initialized synchronously at startup to prevent static mount failures.

#### API Endpoints

| Method | Endpoint | Description | Auth required |
| ------ | ------ | ------ | ------ |
| POST | `/auth/signup` | Create unverified account & dispatch 6-digit OTP | No (Rate-limited) |
| POST | `/auth/verify-otp` | Verify registration OTP & issue initial tokens | No |
| POST | `/auth/resend-otp` | Resend registration OTP | No |
| POST | `/auth/login` | Authenticate credentials; returns access token + refresh cookie | No (Rate-limited)[cite: 1] |
| POST | `/auth/refresh` | Silently rotate access token using `httpOnly` cookie | Cookie required |
| POST | `/auth/logout` | Clear and invalidate the `httpOnly` refresh cookie | No |
| GET | `/auth/me` | Get current user's profile | Yes[cite: 1] |
| PATCH | `/auth/me` | Update username | Yes[cite: 1] |
| POST | `/auth/me/photo` | Upload a profile photo | Yes[cite: 1] |
| POST | `/auth/delete-account/request-otp` | Request 6-digit deletion challenge code via email | Yes (Rate-limited) |
| POST | `/auth/delete-account/confirm` | Verify deletion OTP and permanently delete account & data | Yes |
| GET | `/prompts/` | List current user's prompts | Yes[cite: 1] |
| POST | `/prompts/` | Create a prompt | Yes[cite: 1] |
| GET | `/prompts/{id}` | Get a single prompt | Yes[cite: 1] |
| PATCH | `/prompts/{id}` | Partially update a prompt | Yes[cite: 1] |
| DELETE | `/prompts/{id}` | Delete a prompt | Yes[cite: 1] |
| GET | `/prompts/public` | List public explore prompts (community feed) | No |
| POST | `/prompts/{id}/like` | Toggle like status on a prompt | Yes |

Full interactive documentation (request/response schemas, live testing) is available at `/docs` on any running instance[cite: 1].

#### Getting Started Locally

##### Prerequisites
* Python 3.11+[cite: 1]
* PostgreSQL installed and running locally (or a remote Neon database instance)[cite: 1]

##### Installation

```bash
git clone [https://github.com/Chirag-DATA/Promptarium-Backend.git](https://github.com/Chirag-DATA/Promptarium-Backend.git)
cd Promptarium-Backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

##### Environment configuration
Create a `.env` file at the project root[cite: 1]:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/promptarium
SECRET_KEY=generate_a_random_32_byte_hex_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development

# Transactional Email (Brevo HTTPS API - Recommended)
BREVO_API_KEY=your_brevo_api_key
SENDER_EMAIL=your_email@gmail.com

# Local SMTP Fallback (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_google_app_password
```

Generate a real `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

##### Run it
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
* API: `http://127.0.0.1:8000`[cite: 1]
* Interactive docs: `http://127.0.0.1:8000/docs`[cite: 1]

Tables are created automatically on startup via SQLModel's metadata — no manual migration step needed for a fresh database[cite: 1].

#### Deployment

Deployed on [Render](https://render.com/), connected to a managed [Neon](https://neon.tech/) PostgreSQL instance[cite: 1].

**Build command:** `pip install -r requirements.txt`  
**Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

##### Required Production Environment Variables
* `ENVIRONMENT`: `production` (enforces `Secure=True` and `SameSite=None` on refresh cookies)
* `DATABASE_URL`: Connection string to your PostgreSQL instance (Neon / Render)
* `SECRET_KEY`: Random 32+ byte string
* `BREVO_API_KEY`: API key from Brevo dashboard
* `SENDER_EMAIL`: Verified sender email address

##### Known limitation: ephemeral file storage
Uploaded profile photos are currently stored on the server's local filesystem[cite: 1]. Render's free tier does not guarantee persistent disk storage across redeploys or restarts — uploaded photos may be lost when the service redeploys[cite: 1]. Migrating to a persistent object storage service (e.g., Cloudinary, S3) would resolve this and is a natural next step[cite: 1].

#### Roadmap
[-] Alembic migrations, replacing manual schema changes[cite: 1]  
[-] Persistent cloud storage for profile photos[cite: 1]  
[x] Refresh tokens / longer-lived sessions[cite: 1]  
[x] Rate limiting on auth endpoints[cite: 1]  
[x] Email OTP verification for registrations & account deletion  
[x] Cascading foreign key deletes (`ON DELETE CASCADE`)

#### Related Repository
The frontend — React, Vite, Tailwind — lives in a separate repository: [promptarium](https://github.com/Chirag-DATA/promptarium)[cite: 1].

#### Author
**Chirag Mittal**[cite: 1]
* GitHub: [@Chirag-DATA](https://github.com/Chirag-DATA)[cite: 1]
* LinkedIn: [mittal-chirag](https://linkedin.com/in/mittal-chirag)[cite: 1]

#### License
This project is open source and available under the [MIT License](https://github.com/Chirag-DATA/Promptarium-Backend/blob/main/LICENSE)[cite: 1].
