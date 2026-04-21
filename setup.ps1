# Run with: powershell -ExecutionPolicy Bypass -File setup.ps1

$POETRY_BIN = "$env:APPDATA\Python\Scripts\poetry.exe"
$POETRY_PATH = "$env:APPDATA\Python\Scripts"

Write-Host "==> Checking Python 3.13..."
$pythonPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
$pythonVersion = ""
if ($pythonPath -and $pythonPath -notlike "*WindowsApps*") {
    try {
        $pythonVersion = & $pythonPath --version 2>&1 | Out-String
    } catch {
        $pythonVersion = ""
    }
}

if ($pythonVersion -notmatch "3\.13") {
    Write-Host "    Python 3.13 not found or not functional. Installing/Updating via winget..."
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        winget install --id Python.Python.3.13 --source winget --silent --accept-package-agreements --accept-source-agreements
    } else {
        $installer = "$env:TEMP\python313.exe"
        Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe" -OutFile $installer -UseBasicParsing
        Start-Process -FilePath $installer -ArgumentList "/passive InstallAllUsers=0 PrependPath=1" -Wait
        Remove-Item $installer
    }
    
    # Refresh PATH and try to find python again
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH", "User")
    $pythonPath = Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike "*WindowsApps*" } | Select-Object -ExpandProperty Source -First 1
} else {
    Write-Host "    Python 3.13 already installed: $($pythonVersion.Trim())"
}

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==> Checking Poetry..."
if (-not (Test-Path $POETRY_BIN)) {
    Write-Host "    Installing Poetry..."
    $installScript = "$env:TEMP\install-poetry.py"
    Invoke-WebRequest -Uri https://install.python-poetry.org -OutFile $installScript -UseBasicParsing
    & python $installScript
    Remove-Item $installScript
} else {
    $v = & $POETRY_BIN --version
    Write-Host "    Poetry already installed: $v"
}

# Export for this session
$env:PATH = "$POETRY_PATH;$env:PATH"

Write-Host ""
Write-Host "==> Synchronizing lock file..."
& $POETRY_BIN lock

Write-Host ""
Write-Host "==> Installing project dependencies..."
& $POETRY_BIN install

Write-Host ""
Write-Host "==> Installing Playwright browser (Chromium)..."
& $POETRY_BIN run playwright install chromium

Write-Host ""
Write-Host "==> Done. Verifying..."
& $POETRY_BIN run tc --help

Write-Host ""
Write-Host "Ready. Use: poetry run tc command"
Write-Host "  tc chat from-csv data.csv output/png/"
