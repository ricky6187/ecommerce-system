# Minimalist Ecommerce Mall

A ecommerce system with a **FastAPI + PostgreSQL** backend and a **Streamlit** shopping frontend. Users register, log in, browse products and place orders; admins upload products with photos. Orders use pessimistic row locking so stock is never oversold. Deployed with a full CI/CD pipeline: tests run on every push, and the backend auto-deploys to Render.

## Deployment

- **Backend:** [Render](https://ecommerce-system-4od2.onrender.com) — FastAPI service with environment variables set in the dashboard
- **Frontend:** [Streamlit Community Cloud](https://ecommerce-system.streamlit.app) — You can visit the website here!
For convenience, you can use the account to test below:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123456` |
| **Customer** | `user` | `user123456` |
* these passwords are encrypted in database.

> **Note on Free Hosting:** Hosted on Render's free tier. If the app has been inactive, the initial request may take 30–50 seconds while the backend container wakes up.

## Features

- **User auth** — register / login / logout with JWT tokens (30-min expiry)
- **Role-based access** — `user` can browse & order; `admin` can add products
- **Stock-safe ordering** — `SELECT ... FOR UPDATE` row locking prevents overselling under concurrency
- **Cloud image uploads** — product photos go straight to Cloudinary (no local disk storage)
- **Token blacklist** — logged-out tokens are rejected immediately
- **Streamlit UI** — login/register forms, 2-column product grid, admin upload panel
- **CI/CD** — GitHub Actions runs the test suite on every push to `main`, then triggers a Render deploy

## Tech Stack

| Layer        | Technology                                          |
|--------------|-----------------------------------------------------|
| Backend      | FastAPI, Uvicorn                                    |
| ORM          | SQLAlchemy                                          |
| Database     | PostgreSQL (Neon, SSL required)                     |
| Auth         | JWT (PyJWT), password hashing                       |
| Image storage| Cloudinary                                          |
| Frontend     | Streamlit + `requests`                              |
| Testing      | pytest, httpx, TestClient                           |
| CI/CD        | GitHub Actions → Render, Streamlit Community Cloud  |

## Project Structure

```
ecommerce-project/
├── app/                      # FastAPI backend
│   ├── main.py               # API routes: products, orders, register, login, logout
│   ├── database.py           # engine, session factory, get_db dependency
│   ├── models.py             # SQLAlchemy models: Product, Order, User
│   ├── auth_service.py       # password hashing, JWT create/verify, token blacklist
│   └── user_service.py       # register & authenticate business logic
├── frontend/
│   └── app.py                # Streamlit UI (login, register, shop, admin panel)
├── scripts/
│   └── init_db.py            # one-off script to create tables
├── tests/
│   ├── conftest.py           # pytest fixtures (test database session)
│   └── test_main.py          # API tests with mocked Cloudinary
├── .github/workflows/
│   └── cicd.yml              # CI/CD pipeline
├── .env_example              # template for required environment variables
└── requirements.txt
```

## Getting Started

### 1. Clone & set up the environment

```bash
git clone <your-repo-url>
cd ecommerce-project
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env_example` to `.env` and fill in the values:

| Variable                 | Description                                        |
|--------------------------|----------------------------------------------------|
| `DATABASE_URL`           | PostgreSQL connection string (e.g. Neon)           |
| `JWT_SECRET_KEY`         | Secret key for signing JWT tokens                  |
| `CLOUDINARY_CLOUD_NAME`  | Cloudinary cloud name                              |
| `CLOUDINARY_API_KEY`     | Cloudinary API key                                 |
| `CLOUDINARY_API_SECRET`  | Cloudinary API secret                              |

> If `sslmode` is missing from the database URL, the app appends `sslmode=require` automatically for secure cloud connections.

### 3. Create the database tables

```bash
python scripts/init_db.py
```

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

Interactive API docs (Swagger UI): http://127.0.0.1:8000/docs

### 5. Run the frontend (in a second terminal)

```bash
streamlit run frontend/app.py
```

Open http://localhost:8501 and create an account to start shopping.

## Testing

The test suite covers auth enforcement, 404 handling, order stock deduction, and admin product creation (with Cloudinary mocked). Tests run against a separate test database.

```bash
python -m pytest
```

> Use `python -m pytest` (not bare `pytest`) so the project root lands on `sys.path` and the `app` package is importable.

## API Endpoints

| Method | Endpoint        | Auth        | Description                          |
|--------|-----------------|-------------|--------------------------------------|
| POST   | `/api/register` | none        | Create a new user account            |
| POST   | `/api/login`    | none        | Get a JWT access token               |
| POST   | `/api/logout`   | Bearer JWT  | Blacklist the current token          |
| GET    | `/api/products` | Bearer JWT  | List all products                    |
| POST   | `/api/products` | admin only  | Create a product (multipart + photo) |
| POST   | `/api/orders`   | Bearer JWT  | Place an order for a product         |

## Roles & Auth Flow

1. Client sends `Authorization: Bearer <token>` with each request
2. The backend verifies the JWT signature and expiry, and checks the blacklist
3. The `admin` role is required for product creation (`403` otherwise)

## CI/CD

On every push to `main`, GitHub Actions:

1. Checks out the code and installs dependencies
2. Creates tables in the test database (`TEST_DATABASE_URL` secret)
3. Runs the pytest suite
4. On success, triggers a Render deploy via a deploy hook


## Known Limitations / Roadmap

- Password hashing uses SHA-256 without salt — moving to bcrypt is planned
- Token blacklist is in-memory — resets on server restart (Redis-backed is the next step)
- No rate limiting on login/register endpoints
- No password strength policy yet
