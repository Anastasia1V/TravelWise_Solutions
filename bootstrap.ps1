# bootstrap.ps1
# Project bootstrap script: create venv if needed, install deps, run migrations, load airports, run server.

param(
    [string]$csvPath = ".\airports\data\airports_data.csv"
)

Write-Host "=== Starting bootstrap ==="

# 1) Determine venv path
$venvPath = ".\.venv"
if (!(Test-Path "$venvPath")) {
    $venvPath = ".\venv"
}

# 2) Create virtual environment if missing
if (!(Test-Path "$venvPath")) {
    Write-Host "Virtual environment not found. Creating..." -NoNewline
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host " FAIL" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host " OK"
}

# 3) Activate virtual environment
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -NoNewline
    & "$activateScript"
    Write-Host " OK"
} else {
    Write-Host "Activation script not found: $activateScript" -ForegroundColor Red
    exit 1
}

# 4) Install dependencies
Write-Host "Installing dependencies..." -NoNewline
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host " OK"

# 5) Run migrations
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

# 7) Run development server
Write-Host "Starting Django development server at http://127.0.0.1:8000/" -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$PWD`"; & $venvPath\Scripts\Activate.ps1; python manage.py runserver"

Write-Host "=== Bootstrap finished successfully ===" -ForegroundColor Green
