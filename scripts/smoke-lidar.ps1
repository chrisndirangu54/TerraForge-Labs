# LiDAR pipeline smoke test — starts API if needed, then runs sync LAZ→DTM job.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = $Root

$Base = "http://127.0.0.1:8001"
$Email = "lidar-smoke@example.com"
$Password = "securepass1"

function Test-ApiHealth {
    try {
        Invoke-RestMethod -Uri "$Base/health" -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-ApiHealth)) {
    Write-Host "API not running on $Base — starting uvicorn..."
    Start-Process python -ArgumentList @(
        "-m", "uvicorn", "backend.api.main:app",
        "--host", "127.0.0.1", "--port", "8001"
    ) -WorkingDirectory $Root -WindowStyle Hidden
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        if (Test-ApiHealth) { break }
    }
    if (-not (Test-ApiHealth)) {
        throw "API did not become healthy on $Base within 30s. Start manually:`n  python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8001 --reload"
    }
    Write-Host "API healthy."
}

# Register (ignore if already exists)
try {
    Invoke-RestMethod -Method POST -Uri "$Base/auth/register" `
        -ContentType "application/json" `
        -Body (@{ email = $Email; password = $Password; role = "geologist" } | ConvertTo-Json) | Out-Null
} catch {
    Write-Host "Register skipped (user may already exist)."
}

$login = Invoke-RestMethod -Method POST -Uri "$Base/auth/login" `
    -ContentType "application/json" `
    -Body (@{ email = $Email; password = $Password } | ConvertTo-Json)
$headers = @{ Authorization = "Bearer $($login.access_token)" }

$project = Invoke-RestMethod -Method POST -Uri "$Base/projects" `
    -Headers $headers -ContentType "application/json" `
    -Body '{"slug":"smoke-lidar","name":"Smoke LiDAR"}'

$body = @{
    project_id  = $project.id
    async       = $false
    storage_key = "lidar/demo.laz"
} | ConvertTo-Json

Write-Host "POST /platform/lidar/process (project_id=$($project.id))..."
$result = Invoke-RestMethod -Method POST -Uri "$Base/platform/lidar/process" `
    -Headers $headers -ContentType "application/json" -Body $body

$result | ConvertTo-Json -Depth 6