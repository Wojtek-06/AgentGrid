$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $Root "backend"
Set-Location $Root
python -m uvicorn agentgrid.main:app --reload --host 127.0.0.1 --port 8000
