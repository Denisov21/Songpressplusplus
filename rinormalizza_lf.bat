@echo off
rem Rinormalizza i fine riga a LF in un repository Git (Windows).
rem Uso: copia questo file e .gitattributes nella radice del repo e fai doppio clic.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Questa cartella non e' un repository Git.
    pause
    exit /b 1
)

if not exist .gitattributes (
    echo [ERRORE] Manca il file .gitattributes in questa cartella.
    pause
    exit /b 1
)

echo [1/3] Imposto core.autocrlf=input...
git config --global core.autocrlf input

echo [2/3] Rinormalizzo i file a LF...
git add .gitattributes
git add --renormalize .

echo [3/3] Creo il commit...
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Normalizza fine riga a LF"
    echo [OK] Fatto! I file ora arrivano su Linux senza CRLF.
) else (
    echo [OK] Niente da committare: i file erano gia' a posto.
)

pause
