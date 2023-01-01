# Django Project (Supabase-ready)

A Django 6 project scaffolded with environment-based configuration and ready to connect to Supabase Postgres.

## Prerequisites

- Python 3.13 (already used to create `.venv`)
- pip (managed inside `.venv`)
- A Supabase project (for later, to get the Postgres connection string)

## Setup

1) Create/activate the virtual environment (already created):
   - macOS/Linux:
     - `source .venv/bin/activate`
   - If you prefer not to activate globally, use the full paths shown below in commands.

2) Install dependencies (already installed for you):
   - Django
   - dj-database-url
   - python-dotenv
   - psycopg[binary] (Postgres driver)

3) Environment variables:
   - Edit `.env` in the project root:
     - `SECRET_KEY` — set a strong random value for production
     - `DEBUG` — `True` for local, `False` for prod
     - `ALLOWED_HOSTS` — comma-separated list, e.g. `localhost,127.0.0.1`
     - `CSRF_TRUSTED_ORIGINS` — comma-separated origins (e.g. `http://localhost:8000`)
     - `TIME_ZONE` — e.g. `Asia/Dubai`
     - `DATABASE_URL` — leave blank to use local SQLite by default. Set this to your Supabase Postgres URI to use Supabase.
     - `DB_SSL_REQUIRE` — `True` recommended for Supabase

## Running locally (SQLite default)

- Apply migrations:
  - `.venv/bin/python manage.py migrate`
- Run dev server:
  - `.venv/bin/python manage.py runserver`
- Access:
  - `http://localhost:8000`

## Using Supabase Postgres

1) Get the connection string from Supabase:
   - Supabase Dashboard → Project Settings → Database → Connection string
   - Choose the URI format; it typically looks like:
     ```
     postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres
     ```
   - Supabase often suggests `?sslmode=require`. Either:
     - Include `?sslmode=require` in the URL, OR
     - Set `DB_SSL_REQUIRE=True` in `.env` (recommended). The settings will enforce SSL when a DATABASE_URL is present.

2) Set `.env`:
   - `DATABASE_URL=postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres`
   - `DB_SSL_REQUIRE=True`

3) Install the driver (already done):
   - `.venv/bin/pip install "psycopg[binary]"`

4) Migrate and run:
   - `.venv/bin/python manage.py migrate`
   - `.venv/bin/python manage.py runserver`

## Admin setup (optional)

- Create a superuser:
  - `.venv/bin/python manage.py createsuperuser`
- Visit admin:
  - `http://localhost:8000/admin`

## Notes

- Settings file uses:
  - `python-dotenv` to load `.env`
  - `dj-database-url.parse` to handle `DATABASE_URL` or fallback to SQLite
  - SSL enforcement via `DB_SSL_REQUIRE` only when `DATABASE_URL` is set
- `.gitignore` excludes `.venv` and `.env` to avoid committing secrets.

## Common tweaks

- `ALLOWED_HOSTS` — set appropriately for your deployment hostnames.
- `CSRF_TRUSTED_ORIGINS` — include your site origins for forms and sessions.
- Timezone — set `TIME_ZONE` in `.env` to your locale.

## Next steps

- Add apps as needed:
  - `.venv/bin/python manage.py startapp <app_name>`
- Integrate Supabase services (auth/storage/etc.) via their SDKs if needed (typically in a separate service layer or custom integrations).