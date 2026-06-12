# TerraForge local dev launcher
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = $Root.Path

Write-Host "Checking API health..."
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
    Write-Host "API already running: $($health.version)"
} catch {
    Write-Host "Starting API on http://127.0.0.1:8000"
    Start-Process python -ArgumentList @(
        "-m", "uvicorn", "backend.api.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--reload"
    ) -WorkingDirectory $Root -WindowStyle Hidden
    Start-Sleep -Seconds 4
}

$WebDir = Join-Path $Root "apps\web"
if (Test-Path $WebDir) {
    Write-Host "Starting Vite web on http://127.0.0.1:5173"
    Start-Process npm -ArgumentList @("run", "dev") -WorkingDirectory $WebDir -WindowStyle Hidden
}

Write-Host "TerraForge dev environment starting."
Write-Host "API:  http://127.0.0.1:8000/health"
Write-Host "Web:  http://127.0.0.1:5173"