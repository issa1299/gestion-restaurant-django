@echo off
title RestaurantPro - Serveur
cd /d "%~dp0"
echo ========================================
echo   RestaurantPro - Lancement du serveur
echo ========================================
echo.
echo Serveur demarre sur: http://127.0.0.1:8000
echo Pour le reseau local, ouvrez http://192.168.1.156:8000
echo Fermez cette fenetre pour arreter le serveur.
echo.
venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8000 config.asgi:application
pause
