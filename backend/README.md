# Backend — Document Copilot

API en **FastAPI** para el copiloto de documentos.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Archivo `.env` (copia `.env.example` y completa los valores)

## Instalación

```bash
cd backend
uv sync
```

## Ejecutar la app

```bash
uv run uvicorn app.main:app --reload
```

Alternativa:

```bash
uv run python app/main.py
```

La API queda en `http://127.0.0.1:8000`. Comprueba que responde:

```bash
curl http://127.0.0.1:8000/health
```

## Configuración

Las variables de entorno se leen desde `app/config.py` (fuente única). No uses `os.getenv` en el código de la app.

## Migraciones (Alembic)

```bash
uv run alembic upgrade head
```



## Tests y lint

```bash
uv run pytest
uv run ruff check .
```

