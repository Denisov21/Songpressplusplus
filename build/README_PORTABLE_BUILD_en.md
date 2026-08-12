# Songpress++ Portable Build — ZIP with cx_Freeze

Alternative to the NSIS installer: produces a self-contained ZIP archive that requires
no installation. The user extracts and launches `Songpress++.exe` directly.
This procedure is Windows-specific; the portable build produces a `.exe` executable
and is not compatible with macOS or Linux.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
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
│   └── songpressplusplus/
│       ├── img/
│       ├── locale/
│       ├── templates/
│       │   ├── songs/
│       │   ├── slides/
│       │   ├── themes/      ← syntax colour themes (.ini)
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
cd "<project-path>"
```

> **Note:** The path shown above is an example. Replace it with the actual path where you cloned or extracted the project on your system.

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
|------|-----------|
| 1 | Creates `.venv-build\` in the project root (first run only; reused afterwards) |
| 2 | Upgrades pip and installs cx_Freeze + all pinned dependencies (every run) |
| 3 | Removes any previous `build\` folder, then runs `cx_Freeze build_exe` using the configuration in `pyproject.toml` |
| 4 | Locates the produced build folder (`build\exe.*`) |
| 5 | Copies `templates\fonts\` into the build folder if not already included |
| 6 | Compresses the build **contents** into `dist\Songpress++-<version>-portable.zip` |

> **Note on pip:** the pip upgrade and the dependency install run on **every**
> execution, not only the first one. When the packages are already present pip
> simply reports them as satisfied and downloads nothing.

### Installed dependencies (pinned)

The script installs cx_Freeze plus the following packages into the isolated venv:

| Package | Version constraint |
|---------|--------------------|
| wxPython | `>=4.2.4,<5.0.0` |
| requests | `>=2.32.4,<3.0.0` |
| python-pptx | `>=1.0.2,<2.0.0` |
| pyshortcuts | `>=1.9.5,<2.0.0` |
| reportlab | `>=4.0.0,<5.0.0` |
| pypdf | `>=6.0.0,<7.0.0` |
| markdown | `>=3.4,<4.0.0` |
| mistune | `>=3.0.0,<4.0.0` |
| pywin32 | `>=308` (Windows only, `sys_platform == 'win32'`) |

---

## Output

The archive stores the **contents** of the build folder, so after extraction
`Songpress++.exe` sits in the root of the extracted folder (there is no
intermediate `exe.win-amd64-3.12\` level inside the ZIP):

```
dist/
└── Songpress++-3.0.1-portable.zip   ← extract and distribute
    ├── Songpress++.exe
    ├── python3xx.dll
    ├── wx/
    ├── img/
    ├── locale/
    ├── templates/
    │   ├── songs/
    │   ├── slides/
    │   ├── themes/
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
| Colour themes | `<extracted folder>\templates\themes\` |
| Fonts | `<extracted folder>\templates\fonts\` |

Since `templates\` is next to the exe, Songpress++ automatically detects it
as a portable installation (logic in `MyPreferencesDialog.OnOpenTemplatesFolder`).

---

## Estimated times

| Operation | First run | Subsequent runs |
|-----------|-----------|-----------------|
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
version = "3.0.1"   ← update here, everything else is automatic
```

---

## Cleanup and troubleshooting

### pip upgrade warning during build

If you see a notice such as:

```
NOTICE: A new release of pip is available: 25.x → 26.x
```

pip is functional but outdated inside `.venv-build`. To upgrade it, use `&` and
quotes because the project path may contain spaces:

```powershell
& "<project-path>\.venv-build\Scripts\python.exe" -m pip install --upgrade pip
```

> **Note:** Replace `<project-path>` with the actual path to your project.

Or activate the venv first and then run the shorter form:

```powershell
& "<project-path>\.venv-build\Scripts\Activate.ps1"
python -m pip install --upgrade pip
```

> **Note:** Same as above — replace the path with your actual project path.

This warning does not block the build; upgrading is optional.

---

### Start from scratch (venv + build)

The script already removes the `build\` folder on every run, so a clean rebuild
only requires deleting the venv:

```powershell
Remove-Item -Recurse -Force .venv-build, build
.\installer\Build-Portable.ps1
```

### Error "Unable to create process" or "The system cannot find the file specified"

This error occurs when `.venv-build` was created in a previous project folder
(e.g. `SongpressV26`) and the project was then moved or copied to a new folder
(e.g. `SongpressV28`).

Python venvs contain absolute internal paths and **cannot be moved**. The script
detects the existing venv and reuses it, but its paths still point to the old location.

**Fix:** delete the venv and recreate everything from scratch:

```powershell
Remove-Item -Recurse -Force .\.venv-build
.\installer\Build-Portable.ps1
```

The script will create a fresh venv with the correct paths for the current folder.

---

*File encoding: UTF-8*
