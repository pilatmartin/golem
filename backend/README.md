# GOLEM Backend

## Prerequisites
1. Python 3.13 (not tested on other python versions)
2. [uv](https://docs.astral.sh/uv/) (python package / project manager)

## Installing Dependencies
1. Navigate to the root directory (`backend/`)
2. Install dependencies using `uv` (this will also create `backend/.venv/` directory):
```bash 
$ uv sync
```

## Local Setup
1. Navigate to the root directory (`backend/`)
2. Run the backend using `uv`:
```bash 
$ uv run fastapi dev
```