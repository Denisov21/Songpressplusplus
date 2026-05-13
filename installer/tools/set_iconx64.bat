@echo off
setlocal enabledelayedexpansion

:: Auto-elevazione come Amministratore
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cls
echo ================================================
echo   Songpress++ - Aggiunta icona all'exe
echo ================================================
echo.

:: rcedit nella stessa cartella del bat
set RCEDIT=%~dp0rcedit-x64.exe

if not exist "%RCEDIT%" (
    echo ERRORE: rcedit-x64.exe non trovato nella cartella:
    echo %~dp0
    pause & exit /b 1
)

:: === EXE ===
echo [1/2] Percorso di SongPressPlusPlus.exe
echo        (trascina il file qui oppure incolla il percorso)
echo.
set /p EXE="> "
set EXE=%EXE:"=%

if not exist "%EXE%" (
    echo.
    echo ERRORE: exe non trovato.
    pause & exit /b 1
)

echo.
:: === ICO ===
echo [2/2] Percorso dell'icona .ico
echo        (trascina il file qui oppure incolla il percorso)
echo.
set /p ICO="> "
set ICO=%ICO:"=%

if not exist "%ICO%" (
    echo.
    echo ERRORE: icona non trovata.
    pause & exit /b 1
)

echo.
echo ================================================
echo  Applicazione icona in corso...
echo ================================================
echo.

:: Lavora su copia temporanea per evitare blocchi
set TEMP_EXE=%TEMP%\SPP_temp.exe
copy /Y "%EXE%" "%TEMP_EXE%" >nul

"%RCEDIT%" "%TEMP_EXE%" --set-icon "%ICO%"

if %ERRORLEVEL% == 0 (
    copy /Y "%TEMP_EXE%" "%EXE%" >nul
    del "%TEMP_EXE%"
    echo  Icona aggiunta con successo!
) else (
    del "%TEMP_EXE%"
    echo  ERRORE durante l'aggiunta dell'icona. Codice: %ERRORLEVEL%
)

echo.
pause
endlocal
