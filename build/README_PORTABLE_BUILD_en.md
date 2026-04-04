# Songpress++ Portable Build — ZIP with cx_Freeze

Alternative to the NSIS installer: produces a self-contained ZIP archive that requires
no installation. The user extracts and launches `Songpress++.exe` directly.
This procedure is Windows-specific; the portable build produces a `.exe` executable
and is not compatible with macOS or Linux.

---

## Prerequisites

| Requirement | Notes |
|-----------|------|
| Python 3.12+ | Installed and in the system `PATH` |
| Internet connection | To download dependencies into the venv on first run |

No NSIS, uv, or any other external tool is required.

---

## Required folder structure

```
Songpressplusplus/
├── installer/
│   └── Build-Portable.ps1   ← script to run
├── src/
│   └── songpress/
│       ├── img/
│       ├── locale/
│       ├── templates/
│       │   ├── songs/
│       │   ├── slides/
│       │   └── fonts/       ← optional .ttf fonts
│       └── xrc/
├── pyproject.toml
└── ...
```

---

## Procedure

### 1. Open PowerShell in the project folder

Replace the path below with the full path to your Songpress++ project:

```powershell
cd "E:\Users\Utente\Documents\GitHub\Songpressplusplus"
```

### 2. Allow script execution (first time only, system-wide setting)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3. Unblock the script (first run only)

Windows marks files downloaded from the internet with a security zone flag (NTFS
Alternate Data Stream "Zone.Identifier") that prevents PowerShell scripts from running.
Once the flag is removed, this command does not need to be repeated.

```powershell
Unblock-File .\installer\Build-Portable.ps1
```

### 4. Run the script

```powershell
.\installer\Build-Portable.ps1
```

The script automatically performs these steps:

| Step | Operation |
|------|------|
| 1 | Creates `.venv-build\` in the project root (first run only) |
| 2 | Installs cx_Freeze + all dependencies into the isolated venv |
| 3 | Runs `cx_Freeze build_exe` using the configuration in `pyproject.toml` |
| 4 | Copies `templates\fonts\` into the build folder if not already included |
| 5 | Compresses into `dist\Songpress++-<version>-portable.zip` |

---

## Output

```
dist/
└── Songpress++-2.2.2-portable.zip
    └── exe.win-amd64-3.12\      ← folder to extract and distribute
        ├── Songpress++.exe
        ├── python3xx.dll
        ├── wx/
        ├── img/
        ├── locale/
        ├── templates/
        │   ├── songs/
        │   ├── slides/
        │   └── fonts/
        ├── xrc/
        └── pyproject.toml
```

---

## Runtime paths (portable mode)

| What | Path |
|------|------|
| Executable | `<extracted folder>\Songpress++.exe` |
| Song templates | `<extracted folder>\templates\songs\` |
| Slide templates | `<extracted folder>\templates\slides\` |
| Fonts | `<extracted folder>\templates\fonts\` |

Since `templates\` is next to the exe, Songpress++ automatically detects it
as a portable installation (logic in `MyPreferencesDialog.OnOpenTemplatesFolder`).

---

## Estimated times

| Operation | First run | Subsequent runs |
|------------|-----------------|-----------------|
| venv creation + dependency download | 5–15 min | — (venv reused) |
| cx_Freeze build | 2–5 min | 2–5 min |
| ZIP compression | 1–2 min | 1–2 min |
| **Total** | **~20 min** | **~7 min** |

---

## Expected sizes

| What | Size |
|------|------|
| Build folder (uncompressed) | ~150–250 MB |
| Final ZIP | ~80–130 MB |

Size depends mainly on wxPython (~80 MB) and Python DLLs.

---

## Version update

The version in the ZIP filename is read automatically from `pyproject.toml`:

```toml
[project]
version = "2.2.2"   ← update here, everything else is automatic
```

---

## Cleanup

To start from scratch (venv + build):

```powershell
Remove-Item -Recurse -Force .venv-build, build
```

---

*File encoding: UTF-8*
