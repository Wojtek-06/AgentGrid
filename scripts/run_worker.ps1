$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $Root "backend"
Set-Location $Root
python -m agentgrid.workers.coding_worker @args
