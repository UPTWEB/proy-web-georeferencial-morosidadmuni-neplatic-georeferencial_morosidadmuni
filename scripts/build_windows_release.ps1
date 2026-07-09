param(
    [string]$AppName = "NeplaticDesktop",
    [string]$ZipName = "NeplaticDesktop-Windows.zip"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "No se encontro .venv\Scripts\python.exe. Crea el entorno virtual antes de empaquetar."
}

& $Python -m pip install pyinstaller
& $Python -m PyInstaller --noconfirm --clean --windowed --name $AppName src\main.py

Copy-Item -LiteralPath ".env.example" -Destination "dist\$AppName\.env.example" -Force
Copy-Item -LiteralPath "RELEASE_WINDOWS.md" -Destination "dist\$AppName\README-WINDOWS.md" -Force

New-Item -ItemType Directory -Force -Path "release" | Out-Null
Compress-Archive -Path "dist\$AppName\*" -DestinationPath "release\$ZipName" -Force

Write-Host "Release creado: release\$ZipName"
