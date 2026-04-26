# NeuroCut

Базовая структура проекта с разделением на backend, frontend и docs.

## Структура

- `backend/` — FastAPI (Python)
- `frontend/` — React + TypeScript + Vite
- `docs/` — документация
- `docker-compose.yml` — конфигурация запуска сервисов в Docker

## Быстрый запуск через Docker

```bash
docker compose up --build
```

После запуска:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Быстрый запуск локально (без Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
