# AI Finance Assistant Setup Script for Windows PowerShell
# Run this script as Administrator for best results

Write-Host "AI Finance Assistant Setup Script" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.") {
        Write-Host "✓ Python is installed: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "✗ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python first:" -ForegroundColor Yellow
    Write-Host "1. Go to https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host "2. Download Python 3.11 or later" -ForegroundColor Cyan
    Write-Host "3. During installation, CHECK 'Add Python to PATH'" -ForegroundColor Cyan
    Write-Host "4. Restart PowerShell and run this script again" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Opening Python download page..." -ForegroundColor Yellow
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow

# Install dependencies
try {
    pip install -r requirements.txt
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Error installing dependencies" -ForegroundColor Red
    Write-Host "Trying alternative method..." -ForegroundColor Yellow
    try {
        python -m pip install -r requirements.txt
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        Write-Host "Please run manually: pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Testing application..." -ForegroundColor Yellow

# Test if the app can be imported
try {
    python -c "from app import app; print('✓ Application imports successfully')"
    Write-Host "✓ Application is ready to run" -ForegroundColor Green
} catch {
    Write-Host "✗ Application has errors" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Yellow
Write-Host "1. Run: python app.py" -ForegroundColor Cyan
Write-Host "2. Or double-click: run_app.bat" -ForegroundColor Cyan
Write-Host "3. Open browser to: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Would you like to start the application now? (y/n)" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "y" -or $response -eq "Y" -or $response -eq "yes") {
    Write-Host "Starting AI Finance Assistant..." -ForegroundColor Green
    python app.py
}
