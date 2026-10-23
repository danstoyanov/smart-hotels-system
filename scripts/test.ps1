$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot -Parent)
$previousTestUrl = $env:TEST_DATABASE_URL
try {
    docker compose --profile test up -d --wait test-db
    if ($LASTEXITCODE -ne 0) { throw "Test database did not start." }
    $env:TEST_DATABASE_URL = "postgresql://smart_hotels:local_test_only@127.0.0.1:55433/smart_hotels_test"
    & "$PSScriptRoot/check.ps1"
} finally {
    $env:TEST_DATABASE_URL = $previousTestUrl
    docker compose --profile test rm -s -f test-db
    Pop-Location
}
