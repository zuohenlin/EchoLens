param(
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "start",
    [ValidateSet("all", "echolens", "insight", "interactive")]
    [string]$Mode = "interactive"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path -replace '\\', '/'

function Show-Intro {
    Write-Host ""
    Write-Host "EchoLens Launcher" -ForegroundColor Cyan
    Write-Host "1) Generate a research report in EchoLens Insight"
    Write-Host "2) Upload the report as EchoLens seed file on Home"
    Write-Host "3) Enter prompt to run prediction/simulation"
    Write-Host ""
}

function Show-Endpoints {
    Write-Host ""
    Write-Host "Web Endpoints" -ForegroundColor Cyan
    Write-Host "EchoLens Frontend   : http://localhost:3000"
    Write-Host "EchoLens Backend    : http://localhost:5001"
    Write-Host "Insight Flask    : http://localhost:5000"
    Write-Host "Insight Streamlit: http://localhost:8501"
    Write-Host ""
}

function Choose-Mode {
    Write-Host ""
    Write-Host "Select start mode:" -ForegroundColor Cyan
    Write-Host "1) Start EchoLens + EchoLens Insight"
    Write-Host "2) Start EchoLens only"
    Write-Host "3) Start EchoLens Insight only"
    Write-Host "4) Status only"
    Write-Host "5) Stop services"
    $choice = Read-Host "Enter 1-5"
    switch ($choice) {
        "1" { return @("start", "all") }
        "2" { return @("start", "echolens") }
        "3" { return @("start", "insight") }
        "4" { return @("status", "all") }
        "5" { return @("stop", "all") }
        default { return @("start", "all") }
    }
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-DockerDaemon {
    if (-not (Test-Command -Name "docker")) {
        return $false
    }
    try {
        cmd /c "docker info >nul 2>nul"
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Test-Port {
    param([int]$Port)
    $conn = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $conn
}

function Test-EnvFile {
    param([string]$Path)
    return (Test-Path -Path $Path)
}

function Show-PortStatus {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        if (Test-Port -Port $port) {
            Write-Host "Port $port is already in use." -ForegroundColor Yellow
        }
        else {
            Write-Host "Port $port is free." -ForegroundColor Green
        }
    }
}

if ($Mode -eq "interactive") {
    Show-Intro
    $selection = Choose-Mode
    $Action = $selection[0]
    $Mode = $selection[1]
}

if ($Action -eq "status") {
    Show-PortStatus -Ports @(3000, 5001, 5000, 8501, 8502, 8503)
    Show-Endpoints
    return
}

if ($Action -eq "stop") {
    if (Test-DockerDaemon) {
        Push-Location "$rootPath"
        docker compose -f "$rootPath/docker-compose.insight.yml" down
        Pop-Location
    }
    else {
        Write-Host "Docker Desktop is not running. Skip EchoLens Insight stop." -ForegroundColor Yellow
    }
    Write-Host "Close the EchoLens devserver window(s) to stop npm run dev." -ForegroundColor Yellow
    Show-Endpoints
    return
}

Write-Host "Checking ports..." -ForegroundColor Cyan
Show-PortStatus -Ports @(3000, 5001, 5000, 8501, 8502, 8503)

if ($Mode -in @("all", "echolens")) {
    if (Test-Command -Name "npm") {
        $echolensEnv = "$rootPath/.env"
        if (-not (Test-EnvFile -Path $echolensEnv)) {
            Write-Host "EchoLens .env not found. Copy .env.example and fill keys if needed:" -ForegroundColor Red
            Write-Host "Copy-Item `"$rootPath/.env.example`" `"$rootPath/.env`"" -ForegroundColor Red
        }
        Write-Host "Starting EchoLens (frontend + backend)..." -ForegroundColor Cyan
        $echolensCmd = "cd `"$rootPath`"; npm run dev"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $echolensCmd
    }
    else {
        Write-Host "npm not found. Skip EchoLens start." -ForegroundColor Yellow
    }
}

if ($Mode -in @("all", "insight")) {
    $insightEnv = "$rootPath/third_party/EchoLens-Insight/.env"
    if (-not (Test-EnvFile -Path $insightEnv)) {
        Write-Host "EchoLens Insight .env not found. Copy .env.example and fill API keys:" -ForegroundColor Red
        Write-Host "Copy-Item `"$rootPath/third_party/EchoLens-Insight/.env.example`" `"$rootPath/third_party/EchoLens-Insight/.env`"" -ForegroundColor Red
        Write-Host "Skip EchoLens Insight start." -ForegroundColor Red
        return
    }
    if (Test-DockerDaemon) {
        Write-Host "Starting EchoLens Insight via Docker Compose..." -ForegroundColor Cyan
        Push-Location "$rootPath"
        docker compose -f "$rootPath/docker-compose.insight.yml" up -d
        Pop-Location
    }
    else {
        Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
        Write-Host "Tip: Open 'Docker Desktop' from Start Menu and wait for Engine Running." -ForegroundColor Red
        Read-Host "Press Enter after Docker Desktop is running"
        if (Test-DockerDaemon) {
            Write-Host "Starting EchoLens Insight via Docker Compose..." -ForegroundColor Cyan
            Push-Location "$rootPath"
            docker compose -f "$rootPath/docker-compose.insight.yml" up -d
            Pop-Location
        }
        else {
            Write-Host "Docker Desktop is still not running. Skip EchoLens Insight start." -ForegroundColor Red
        }
    }
}

Write-Host "Done. Check ports: EchoLens 3000/5001, EchoLens Insight 5000/8501/8502/8503" -ForegroundColor Green
Show-Endpoints
