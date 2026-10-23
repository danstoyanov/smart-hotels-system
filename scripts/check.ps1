$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    uv run --locked ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Lint failed." }
    uv run --locked ruff format --check .
    if ($LASTEXITCODE -ne 0) { throw "Format check failed." }
    node --check frontend/assets/site.js
    if ($LASTEXITCODE -ne 0) { throw "JavaScript check failed." }
    node --check frontend/assets/chat.js
    if ($LASTEXITCODE -ne 0) { throw "Chat JavaScript check failed." }
    node --test frontend/tests/sse.test.mjs
    if ($LASTEXITCODE -ne 0) { throw "SSE browser-module tests failed." }
    uv run --locked python -m backend.app.hotel
    if ($LASTEXITCODE -ne 0) { throw "Hotel data validation failed." }
    uv run --locked pytest
    if ($LASTEXITCODE -ne 0) { throw "Tests failed." }
} finally { Pop-Location }
