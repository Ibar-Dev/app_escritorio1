# build.ps1 - Script de construcción para Zoo Picasso App (Windows PowerShell)

param(
    [switch]$Clean,
    [switch]$Install,
    [switch]$Run,
    [switch]$Test,
    [switch]$Package
)

$ErrorActionPreference = "Stop"

Write-Host "=== Zoo Picasso - Build Script ===" -ForegroundColor Cyan

# Función auxiliar para ejecutar comandos
function Invoke-Cmd {
    param([string]$Command)
    Write-Host "→ $Command" -ForegroundColor Gray
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error ejecutando: $Command" -ForegroundColor Red
        exit 1
    }
}

# Limpiar artefactos de construcción anteriores
if ($Clean) {
    Write-Host "`n🧹 Limpiando directorios..." -ForegroundColor Yellow
    Invoke-Cmd "Remove-Item -Path build -Recurse -Force -ErrorAction SilentlyContinue"
    Invoke-Cmd "Remove-Item -Path dist -Recurse -Force -ErrorAction SilentlyContinue"
    Invoke-Cmd "Remove-Item -Path __pycache__ -Recurse -Force -ErrorAction SilentlyContinue"
    Write-Host "✓ Limpieza completada" -ForegroundColor Green
}

# Instalar/actualizar dependencias
if ($Install) {
    Write-Host "`n📦 Instalando dependencias..." -ForegroundColor Yellow
    Invoke-Cmd "uv sync"
    Write-Host "✓ Dependencias instaladas" -ForegroundColor Green
}

# Ejecutar pruebas
if ($Test) {
    Write-Host "`n🧪 Ejecutando pruebas..." -ForegroundColor Yellow
    Invoke-Cmd "uv run pytest -v"
    Write-Host "✓ Pruebas completadas" -ForegroundColor Green
}

# Ejecutar la aplicación
if ($Run) {
    Write-Host "`n▶️  Ejecutando aplicación..." -ForegroundColor Yellow
    Invoke-Cmd "uv run main.py"
}

# Empaquetar con PyInstaller
if ($Package) {
    Write-Host "`n📦 Empaquetando aplicación..." -ForegroundColor Yellow
    
    if (-not (Test-Path "zoo_picasso.spec")) {
        Write-Host "⚠️  zoo_picasso.spec no encontrado" -ForegroundColor Yellow
    }
    
    Invoke-Cmd "uv run pyinstaller zoo_picasso.spec --noconfirm"
    Write-Host "✓ Empaquetado completado en ./dist/" -ForegroundColor Green
}

# Si no hay parámetros, mostrar ayuda
if (-not ($Clean -or $Install -or $Run -or $Test -or $Package)) {
    Write-Host "`n📖 Uso:" -ForegroundColor Cyan
    Write-Host "  .\build.ps1 -Install          # Instalar dependencias"
    Write-Host "  .\build.ps1 -Test             # Ejecutar pruebas"
    Write-Host "  .\build.ps1 -Run              # Ejecutar aplicación"
    Write-Host "  .\build.ps1 -Package          # Empaquetar con PyInstaller"
    Write-Host "  .\build.ps1 -Clean            # Limpiar artefactos de construcción"
    Write-Host "  .\build.ps1 -Install -Run     # Instalar y ejecutar"
    Write-Host "  .\build.ps1 -Clean -Install -Package  # Limpiar, instalar y empaquetar"
}

Write-Host "`n✅ Completado" -ForegroundColor Green
