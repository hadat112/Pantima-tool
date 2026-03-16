# Run with: powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Stop"

$POETRY_BIN = "$env:APPDATA\Python\Scripts\poetry.exe"
$POETRY_PATH = "$env:APPDATA\Python\Scripts"

Write-Host "==> Checking Python 3.13..."
$python = Get-Command python -ErrorAction SilentlyContinue
$pythonVersion = if ($python) { & python --version 2>&1 } else { "" }

if ($pythonVersion -notmatch "3\.13") {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "    Installing Python 3.13 via winget..."
        winget install --id Python.Python.3.13 --source winget --silent --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "    winget not found. Downloading Python 3.13 installer directly..."
        $installer = "$env:TEMP\python313.exe"
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe" -OutFile $installer -UseBasicParsing
        Write-Host "    Running installer (follow the prompts — check 'Add Python to PATH')..."
        Start-Process -FilePath $installer -ArgumentList "/passive InstallAllUsers=0 PrependPath=1" -Wait
        Remove-Item $installer
    }
    # Refresh PATH so python is available
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
} else {
    Write-Host "    Python 3.13 already installed: $pythonVersion"
}

Write-Host ""
Write-Host "==> Checking Poetry..."
if (-not (Test-Path $POETRY_BIN)) {
    Write-Host "    Installing Poetry..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
} else {
    $v = & $POETRY_BIN --version
    Write-Host "    Poetry already installed: $v"
}

# Export for this session
$env:PATH = "$POETRY_PATH;$env:PATH"

# Persist to user PATH if not already there
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$POETRY_PATH*") {
    [System.Environment]::SetEnvironmentVariable("PATH", "$POETRY_PATH;$userPath", "User")
    Write-Host "    Added Poetry to user PATH (restart terminal to take effect)"
}

Write-Host ""
Write-Host "==> Installing project dependencies..."
& $POETRY_BIN install --with chat

Write-Host ""
Write-Host "==> Installing Playwright browser (Chromium)..."
& $POETRY_BIN run playwright install chromium

Write-Host ""
Write-Host "==> Done. Verifying..."
& $POETRY_BIN run tc --help

Write-Host ""
Write-Host "Ready. Use: poetry run tc <command>"
Write-Host "  tc chat from-csv data.csv output/png/"
