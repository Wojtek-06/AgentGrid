$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $Root "backend"
if (-not $env:AGENTGRID_API_TOKEN) { $env:AGENTGRID_API_TOKEN = "dev-token" }
if (-not $env:AGENTGRID_USE_REDIS) { $env:AGENTGRID_USE_REDIS = "1" }
if (-not $env:AGENTGRID_REDIS_URL) { $env:AGENTGRID_REDIS_URL = "redis://localhost:6379/0" }
Set-Location $Root
Write-Host ('AgentGrid worker - USE_REDIS={0} redis={1}' -f $env:AGENTGRID_USE_REDIS, $env:AGENTGRID_REDIS_URL)
Write-Host 'Requires Redis + API (scripts\run_api.ps1). Heartbeats appear on GET /api/health.'
python -m agentgrid.workers.coding_worker @args
