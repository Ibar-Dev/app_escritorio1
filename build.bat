@echo off
cd /d "%~dp0"
echo Instalando pyinstaller si es necesario...
uv sync --group dev
echo.
echo Generando ejecutable en dist\ZooPicasso\ ...
uv run pyinstaller zoo_picasso.spec --clean
if errorlevel 1 (
    echo.
    echo BUILD FALLIDO. Revisa los errores arriba.
    pause
    exit /b 1
)
echo.
echo Listo: dist\ZooPicasso\ZooPicasso.exe
pause
