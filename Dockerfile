FROM ghcr.io/astral-sh/uv:0.13.4 AS uv

FROM python:3.13-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY backend ./backend
COPY frontend ./frontend
COPY hotel ./hotel

RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app
EXPOSE 8080

CMD ["/app/.venv/bin/uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080", "--loop", "backend.app.runtime:new_loop", "--no-access-log"]
