# Install-LibreOffice.ps1
# Run this script ONCE on your robot machine / template to install LibreOffice.
# Requires administrator privileges.

Write-Host "Installing LibreOffice..." -ForegroundColor Cyan

winget install TheDocumentFoundation.LibreOffice `
    --silent `
    --accept-package-agreements `
    --accept-source-agreements

if ($LASTEXITCODE -eq 0) {
    Write-Host "LibreOffice installed successfully." -ForegroundColor Green
    Write-Host "Please restart Studio or the robot process before running the activity."
} else {
    Write-Host "Installation failed. Please install manually from https://www.libreoffice.org/download/" -ForegroundColor Red
}
