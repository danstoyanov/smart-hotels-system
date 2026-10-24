$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    uv run --locked python -m backend.app.db
    if ($LASTEXITCODE -ne 0) { throw "Migration failed. Start PostgreSQL and check .env." }
    uv run --locked python -m backend.app.inventory
    if ($LASTEXITCODE -ne 0) { throw "Demo inventory load failed." }
    uv run --locked uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --loop backend.app.runtime:new_loop --reload
    if ($LASTEXITCODE -ne 0) { throw "The server stopped with an error." }
} finally { Pop-Location }
