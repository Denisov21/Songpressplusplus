# How to build the Windows installer

In order to build the Windows installer you need to download:

- Windows x64 binaries of `uv`, e.g. [https://github.com/astral-sh/uv/releases/download/0.9.21/uv-x86_64-pc-windows-msvc.zip](https://github.com/astral-sh/uv/releases/download/0.9.21/uv-x86_64-pc-windows-msvc.zip)
- The [NSIS compiler](https://nsis.sourceforge.io/Download)

Extract the content of the zip files of `uv` in this folder (`uv.exe` is sufficient). Then, launch the NSIS compiler and compile the `songpress.nsi` script.





## File nsi 

La soluzione 1 (Windows-1252) gestisce perfettamente tutti questi caratteri: à, è, é, ì, ò, ù, É, À ecc. sono tutti nel set Windows-1252.Eseguito un comando, file lettoEseguito un comando, file lettoIl file è ora in Windows-1252. Tutti i caratteri accentati (à, è, é, È, É, ecc.) sono preservati correttamente e NSIS li leggerà senza problemi. Ricorda di salvarlo sempre in Windows-1252 quando lo modifichi in futuro.