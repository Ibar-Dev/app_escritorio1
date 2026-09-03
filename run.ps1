# run.ps1 - Script para ejecutar Zoo Picasso App (Windows PowerShell)

param(
    [switch]$Dev,
    [switch]$NoSync
)

$ErrorActionPreference = "Stop"

Write-Host "=== Zoo Picasso - App Launcher ===" -ForegroundColor Cyan

# Sincronizar dependencias si no se especifica -NoSync
if (-not $NoSync) {
    Write-Host "`n📦 Sincronizando dependencias..." -ForegroundColor Yellow
    uv sync
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error sincronizando dependencias" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Dependencias sincronizadas" -ForegroundColor Green
}

# Ejecutar en modo desarrollo o producción
Write-Host "`n▶️  Iniciando aplicación..." -ForegroundColor Yellow

if ($Dev) {
    Write-Host "📍 Modo desarrollo activado" -ForegroundColor Cyan
    uv run main.py
} else {
    uv run main.py
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error ejecutando la aplicación" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Aplicación cerrada correctamente" -ForegroundColor Green
