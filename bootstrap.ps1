# bootstrap.ps1
# Project bootstrap script: install deps, run migrations, load airports.

param(
    [string]$csvPath = ".\airports\data\airports_data.csv"
)

Write-Host "=== Begin bootstrap ===" -ForegroundColor Cyan

# 1) Auto-detect virtual environment
$venvFolders = @(".venv", "venv")
$activateScript = $null

foreach ($folder in $venvFolders) {
    $tryPath = Join-Path $folder "Scripts\Activate.ps1"
    if (Test-Path $tryPath) {
        $activateScript = $tryPath
        break
    }
}

if ($null -eq $activateScript) {
    Write-Host "ERROR: Не найдено виртуальное окружение (.venv или venv)" -ForegroundColor Red
    exit 1
}

# 2) Activate virtualenv
Write-Host "Activating virtual environment from $activateScript..." -NoNewline
& "$activateScript"
Write-Host " OK"

# 3) Install requirements
Write-Host "Installing dependencies..." -NoNewline
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    exit $LASTEXITCODE
} else {
    Write-Host " OK"
}

# 4) Run makemigrations & migrate
Write-Host "Running makemigrations..." -NoNewline
python manage.py makemigrations
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    exit $LASTEXITCODE
} else {
    Write-Host " OK"
}

Write-Host "Running migrate..." -NoNewline
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host " FAIL" -ForegroundColor Red
    exit $LASTEXITCODE
} else {
    Write-Host " OK"
}

# 5) Load airports if CSV exists
if (Test-Path $csvPath) {
    Write-Host "Loading airports from $csvPath..." -NoNewline
    python manage.py load_airports $csvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host " FAIL" -ForegroundColor Red
        exit $LASTEXITCODE
    } else {
        Write-Host " OK"
    }
} else {
    Write-Host "CSV file not found: $csvPath" -ForegroundColor Yellow
}

Write-Host "=== Bootstrap completed successfully ===" -ForegroundColor Green
