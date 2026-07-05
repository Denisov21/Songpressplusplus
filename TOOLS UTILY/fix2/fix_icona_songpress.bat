@echo off
setlocal enabledelayedexpansion
title Songpress++ - Fix icona estensioni file

echo ============================================================
echo  Songpress++ - Fix icona per estensioni .crd .pro .chopro
echo  .chordpro .cho .tab .sng
echo ============================================================
echo.
echo Causa del problema:
echo   Windows salva la scelta di app/icona per ogni estensione in
echo   una chiave separata (FileExts\.ext\UserChoice), diversa da
echo   quella scritta dall'installer (Software\Classes\.ext). Se in
echo   passato quella chiave puntava a un ProgID poi rimosso durante
echo   un aggiornamento (es. "Songpress.crd" o "Songpress.ChordPro"),
echo   Explorer non riesce piu' a risolvere l'icona e mostra quella
echo   generica, anche se l'associazione vera e propria e' corretta.
echo.
echo Questo script rimuove solo quelle chiavi FileExts (per l'utente
echo corrente), cosi' Explorer le ricrea usando l'associazione attuale
echo con l'icona corretta. Non tocca file, non serve reinstallare.
echo.
pause

for %%E in (crd pro chopro chordpro cho tab sng) do (
    echo Pulizia FileExts\.%%E ...
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.%%E" /f >nul 2>&1
)

echo.
echo Aggiornamento cache icone di Explorer...
REM Notifica il sistema che le associazioni sono cambiate
rundll32.exe shell32.dll,SHChangeNotify 0x08000000 0 0 0 >nul 2>&1
ie4uinit.exe -show >nul 2>&1

echo.
echo Riavvio di Explorer per forzare il refresh visivo delle icone...
taskkill /f /im explorer.exe >nul 2>&1
timeout /t 1 /nobreak >nul
start explorer.exe

echo.
echo ============================================================
echo Fatto. Se le icone dei file .crd/.pro/... non sono ancora
echo corrette, apri una volta un file con Songpress++ (tasto destro
echo - Apri con - Songpress++ - "Usa sempre questa app") e poi
echo riesegui questo script.
echo ============================================================
pause
