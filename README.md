# NeuroCut

Базовая структура проекта с разделением на backend, frontend и docs.

## Структура

- `backend/` — FastAPI (Python) + SQLAlchemy + Alembic
- `frontend/` — React + TypeScript + Vite
- `docs/` — документация
- `docker-compose.yml` — конфигурация запуска сервисов в Docker

## Быстрый запуск через Docker Compose (с PostgreSQL)

```bash
docker compose up --build
```

`docker compose` использует сетевые настройки из `docker-compose.yml` (backend подключается к БД по хосту `postgres`).

После запуска:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5432`

Проверка health-эндпоинтов:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/db-health
```

Ожидаемые ответы:

- `/health` → `{"status":"ok"}`
- `/db-health` → `{"status":"ok"}` (если подключение к PostgreSQL доступно)

## Настройки backend окружения

Пример переменных находится в `backend/.env.example`:

- `DATABASE_URL` — строка подключения SQLAlchemy к PostgreSQL
- `APP_ENV` — окружение приложения (`development`, `staging`, `production`)

## Alembic

Alembic настроен в `backend/alembic/` и `backend/alembic.ini`.
На этом этапе бизнес-таблицы не создаются.

Примеры команд:

```bash
cd backend
alembic upgrade head
```

## Быстрый запуск локально (без Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# для локального запуска используйте localhost в DATABASE_URL из .env.example
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
