# Vincendum

Vincendum is a credit risk and concentration risk engine built with:

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- React / Vite
- Auth0
- AWS S3
- TrueLayer / Open Banking

## Prerequisites

Install:

- Git
- Docker Desktop

You do not need to install PostgreSQL, Redis, Python, or Node.js locally if you are using the Docker development setup.

## Getting Started

### 1. Clone the repository

'bash
git clone <REPOSITORY_URL>
cd <REPOSITORY_NAME>

2. Create the environment file

Copy .env.example to .env.

Windows PowerShell:

Copy-Item .env.example .env

macOS / Linux:

cp .env.example .env

Fill in the required environment variables.

Do not commit .env to Git.

Environment Variables
PostgreSQL
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

These values are used by the PostgreSQL Docker container.

Database
DATABASE_URL=

The backend uses this to connect to PostgreSQL.

Auth0

Backend:

AUTH0_DOMAIN=
AUTH0_AUDIENCE=
AUTH0_ISSUER=

Frontend:

VITE_AUTH0_DOMAIN=
VITE_AUTH0_CLIENT_ID=
AWS S3

Required for document storage:

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
AWS_S3_BUCKET=

Do not commit AWS credentials.

TrueLayer / Open Banking
TRUELAYER_ENVIRONMENT=
TRUELAYER_CLIENT_ID=
TRUELAYER_CLIENT_SECRET=
TRUELAYER_REDIRECT_URI=
OPEN_BANKING_FRONTEND_CALLBACK_URL=
Run the Application

Start the development environment:

docker compose -f docker-compose.dev.yml up --build

This starts:

PostgreSQL
Redis
FastAPI backend
React frontend

The backend automatically runs:

alembic upgrade head

when the backend container starts.

Backend

The API is available at:

http://localhost:8000

FastAPI documentation:

http://localhost:8000/docs
Frontend

The frontend is available at:

http://localhost:5173
Stopping the Application

Press Ctrl+C, or run:

docker compose -f docker-compose.dev.yml down

To remove the PostgreSQL development volume as well:

docker compose -f docker-compose.dev.yml down -v

Warning: down -v deletes the local PostgreSQL Docker volume and therefore removes the local database data.

Running Tests

Backend tests can be run inside the backend environment.

docker compose -f docker-compose.dev.yml exec backend pytest
Development

The repository contains separate Dockerfiles for development:

Dockerfile.dev.backend
Dockerfile.dev.frontend

Database migrations are managed with Alembic.

To create a new migration:

alembic revision --autogenerate -m "describe migration"

To apply migrations:

alembic upgrade head
Important

Never commit:

.env
API keys
Auth0 secrets
AWS credentials
TrueLayer client secrets
Database passwords

Use .env.example to document required environment variables without including secret values.


### But there's one more thing I'd change

Your `.env.example` currently has **duplicate PostgreSQL variables**:

```env
POSTGRES_USER=credit_user
POSTGRES_PASSWORD=replace_me
POSTGRES_DB=credit_risk_db

DATABASE_URL=

...

POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

Don't do that. Keep one set.

And because your Compose file currently has a mismatch between:

POSTGRES_DB=credit_risk_db

and:

DATABASE_URL: .../credit_risk_engine

I'd fix that before anyone else clones the project.

What your friend actually needs

Once you fix those pieces, the onboarding becomes beautifully simple:

GitHub access
      ↓
git clone
      ↓
copy .env.example → .env
      ↓
fill in credentials
      ↓
docker compose -f docker-compose.dev.yml up --build
      ↓
Alembic creates/updates DB
      ↓
backend :8000
frontend :5173
Postgres + Redis running in Docker

