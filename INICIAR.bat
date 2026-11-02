@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo    DASHBOARD DE APUESTAS
echo ------------------------------------------------------------
echo    Iniciando el servidor...
echo    Se abrira solo en tu navegador en unos segundos.
echo.
echo    Direccion:  http://localhost:5000
echo    Para CERRAR la app: cierra esta ventana.
echo ============================================================
echo.
start "" cmd /c "timeout /t 3 >nul & start http://localhost:5000"
python server\app.py
echo.
echo El servidor se detuvo. Pulsa una tecla para salir.
pause >nul
