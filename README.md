# NeuroCut

Базовая структура проекта с разделением на backend, frontend и docs.

## Структура

- `backend/` — FastAPI (Python)
- `frontend/` — React + TypeScript + Vite
- `docs/` — документация
- `docker-compose.yml` — минимальная конфигурация сервисов

## Быстрый запуск локально

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend будет доступен на `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend будет доступен на `http://localhost:5173`.
