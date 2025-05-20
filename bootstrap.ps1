# bootstrap.ps1
# Full project bootstrap: setup venv, install requirements, migrate DB, load airports, runserver, open browser

param(
    [string]$csvPath = ".\airports\data\airports_data.csv"
)

Write-Host "=== Starting bootstrap ==="

# 1) Determine venv path
$venvPath = ".\.venv"
if (!(Test-Path "$venvPath")) {
    $venvPath = ".\venv"
}

# 2) Create venv if missing
if (!(Test-Path "$venvPath")) {
    Write-Host "Virtual environment not found. Creating..." -NoNewline
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host " FAIL" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host " OK"
}

# 3) Activate venv
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -NoNewline
    & "$activateScript"
    Write-Host " OK"
} else {
    Write-Host "Activation script not found: $activateScript" -ForegroundColor Red
    exit 1
}

# 4) Install requirements
Write-Host "Installing dependencies..." -NoNewline
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host " OK"

# 5) Migrations
Write-Host "Running makemigrations..." -NoNewline
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host " OK"

Write-Host "Running migrate..." -NoNewline
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host " OK"

# 6) Load airports
if (Test-Path $csvPath) {
    Write-Host "Loading airports from $csvPath..." -NoNewline
    python manage.py load_airports $csvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host " FAIL" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host " OK"
} else {
    Write-Host "CSV file not found: $csvPath" -ForegroundColor Yellow
}

# 7) Run server and open browser
Write-Host "Starting server and opening browser..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$PWD`"; & '$venvPath\Scripts\Activate.ps1'; python manage.py runserver"
Start-Process "http://127.0.0.1:8000/"

Write-Host "=== Bootstrap completed successfully ===" -ForegroundColor Green
