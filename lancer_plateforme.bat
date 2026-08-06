@echo off
title RestaurantPro - Plateforme (Serveur + Tunnel Serveo)
cd /d "%~dp0"

echo ================================================
echo   RestaurantPro - Lancement de la plateforme
echo ================================================
echo.

REM --- Arreter les anciennes instances (ports 8000, tunnels) ---
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
REM Arreter les anciens tunnels serveo/cloudflared
wmic process where "name='ssh.exe'" delete >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1

echo [1/3] Deploiement du serveur (port 8000)...
start "RestaurantPro - Serveur" cmd /c "cd /d %~dp0 && venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000 --noreload"
timeout /t 6 /nobreak >nul

echo [2/3] Lancement du tunnel Serveo (URL fixe)...
start "RestaurantPro - Tunnel" cmd /c "ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R restaurantpro:80:127.0.0.1:8000 serveo.net -N"

echo [3/3] Verification du tunnel...
timeout /t 8 /nobreak >nul

echo.
echo ================================================
echo   URL FIXE   :  https://restaurantpro.serveo.net
echo   Serveur    :  http://127.0.0.1:8000
echo   Superadmin :  admin / AdminPass123
echo   Abonnements:  /tenants/plateforme/
echo ================================================
echo.
echo IMPORTANT : gardez les 2 fenetres "Serveur" et "Tunnel"
echo ouvertes pour que la plateforme reste en ligne.
echo.
pause