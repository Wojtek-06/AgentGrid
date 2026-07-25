$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $Root "backend"
if (-not $env:AGENTGRID_API_TOKEN) { $env:AGENTGRID_API_TOKEN = "dev-token" }
# Separate worker process needs a shared Redis queue (docker compose up -d redis).
if (-not $env:AGENTGRID_USE_REDIS) { $env:AGENTGRID_USE_REDIS = "1" }
if (-not $env:AGENTGRID_REDIS_URL) { $env:AGENTGRID_REDIS_URL = "redis://localhost:6379/0" }
Set-Location $Root
Write-Host "AgentGrid API — token=$($env:AGENTGRID_API_TOKEN) USE_REDIS=$($env:AGENTGRID_USE_REDIS)"
Write-Host "If enqueue stalls: docker compose up -d redis   then start scripts\run_worker.ps1"
python -m uvicorn agentgrid.main:app --reload --host 127.0.0.1 --port 8000
