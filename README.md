# Neighborly-API

FastAPI backend for the Neighborly project.

## Quickstart

1. Create a virtual environment and activate it:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

2. Install dependencies (if you have a `requirements.txt`):

```powershell
pip install -r requirements.txt
```

3. Run the app with Uvicorn:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Repository

- API entry: `main.py`
- Routers: `routers.py`
- Database: `database.py`, `database_models.py`
- Schemas: `schemas.py`

## CI
A basic CI workflow runs syntax checks on Python files via GitHub Actions (see `.github/workflows/ci.yml`).

## License
MIT — see `LICENSE`.
