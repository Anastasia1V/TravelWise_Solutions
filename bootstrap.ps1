# bootstrap.ps1
# Project bootstrap script: install deps, run migrations, load airports.

param(
    [string]$venvPath = ".\.venv",
    [string]$csvPath  = ".\airports\data\airports_data.csv"
)

Write-Host "=== Begin bootstrap ==="

# 1) Activate virtualenv
if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -NoNewline
    & "$venvPath\Scripts\Activate.ps1"
    Write-Host " OK"
} else {
    Write-Host "ERROR: Activate.ps1 not found" -ForegroundColor Red
    exit 1
}

# 2) Install requirements
Write-Host "Installing dependencies..." -NoNewline
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host " FAIL" -ForegroundColor Red; exit $LASTEXITCODE }
else { Write-Host " OK" }

# 3) Run makemigrations & migrate
Write-Host "Running makemigrations..." -NoNewline
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) { Write-Host " FAIL" -ForegroundColor Red; exit $LASTEXITCODE }
else { Write-Host " OK" }

Write-Host "Running migrate..." -NoNewline
python manage.py migrate
if ($LASTEXITCODE -ne 0) { Write-Host " FAIL" -ForegroundColor Red; exit $LASTEXITCODE }
else { Write-Host " OK" }

# 4) Load airports if CSV exists
if (Test-Path $csvPath) {
    Write-Host "Loading airports from $csvPath..." -NoNewline
    python manage.py load_airports $csvPath
    if ($LASTEXITCODE -ne 0) { Write-Host " FAIL" -ForegroundColor Red; exit $LASTEXITCODE }
    else { Write-Host " OK" }
} else {
    Write-Host "CSV file not found: $csvPath"
}

Write-Host "=== Bootstrap completed successfully ==="
