# GOLEM Backend

## Prerequisites

1. Python 3.13 (not tested on other python versions)
2. [uv](https://docs.astral.sh/uv/) (python package / project manager)
3. [docker](https://www.docker.com/)

## Installing Dependencies

1. Navigate to the root directory (`backend/`)
2. Install dependencies using `uv` (this will also create `backend/.venv/` directory):

```bash 
$ uv sync
```

## Startup

We firstly need to start the database. Easiest way is by using an official PostgreSQL docker image. The connection
string is located in the `.env` file.

```bash
$ docker run -it --rm -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:17-alpine
```

After having started the database, navigate to the `app` directory:

```bash
$ cd app
```

Rename or copy the `.env.template` file to `.env` (this is to avoid committing sensitive data):

```bash
$ cp .env.template .env
```

Now we can run the database migrations:

```bash
$ uv run alembic upgrade head
```

Finally, we can run the backend using:

```bash 
$ uv run fastapi dev
```