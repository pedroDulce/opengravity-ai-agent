@echo off
:: run_bot.bat - Auto-restart del bot si se cierra inesperadamente

:restart
echo [%DATE% %TIME%] Iniciando OpenGravity Bot...
python opengravity_bot.py
set EXIT_CODE=%ERRORLEVEL%

echo [%DATE% %TIME%] ⚠️ Bot cerrado con código: %EXIT_CODE%

:: Si el código es 0 (salida normal) o 1 (Ctrl+C), no reiniciar
if %EXIT_CODE% EQU 0 exit /b
if %EXIT_CODE% EQU 1 exit /b

:: Para cualquier otro código (error), esperar y reiniciar
echo [%DATE% %TIME%] 🔄 Reiniciando en 10 segundos...
timeout /t 10 /nobreak
goto restart