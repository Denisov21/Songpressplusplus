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

The "project path" is the folder that contains `pyproject.toml` and the
`installer\` subfolder (i.e. the repo root — not `installer\` and not `src\`).

Change into that folder with `cd`, wrapping the path in quotes because it may
contain spaces. Example with a project on the Desktop:

```powershell
cd "<project-path>"
```

> **Note:** The path shown above is only an example. Replace it with the actual
> path where you cloned or extracted the project on your system.

**How to get the exact path:** open the project folder in File Explorer, click
the address bar at the top (the path becomes selectable), copy it with `Ctrl+C`
and paste it after `cd ` inside quotes. Alternatively, hold `Shift`, right-click
the folder and choose **"Copy as path"**: it copies the full path with the
quotes already included.

> **Tip:** a shortcut is to open the folder in File Explorer, type `powershell`
> in the address bar and press `Enter`: PowerShell opens already positioned in
> that folder, so you can skip the `cd`.

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
| 3 | Temporarily prepends `src\` to `PYTHONPATH` (so the `songpressPlusPlus` package is importable) and runs `cx_Freeze build_exe` using the configuration in `pyproject.toml` |
| 4 | Locates the produced build folder by picking the most recently modified subfolder of `build\` (`build\exe.*` or `build\<name>`). **Note:** the script does *not* delete the `build\` folder before compiling |
| 5 | Copies `templates\fonts\` into the build folder if not already included |
| 6 | Compresses the **build folder** into `dist\Songpress++-<version>-portable.zip` (the folder is included as the archive's top level) |

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

The archive includes the build folder as its top level, so after extraction
`Songpress++.exe` sits inside an `exe.win-amd64-3.12\` subfolder (the name
depends on platform and Python version):

```
dist/
└── Songpress++-8.0.0-portable.zip   ← extract and distribute
    └── exe.win-amd64-3.12/          ← intermediate level created by Compress-Archive
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

After extraction the files live inside the `exe.win-amd64-3.12\` subfolder
(shown below as `<exe folder>`):

| What | Path |
|------|------|
| Executable | `<exe folder>\Songpress++.exe` |
| Song templates | `<exe folder>\templates\songs\` |
| Slide templates | `<exe folder>\templates\slides\` |
| Colour themes | `<exe folder>\templates\themes\` |
| Fonts | `<exe folder>\templates\fonts\` |

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
version = "8.0.0"   ← update here, everything else is automatic
```

---

## Automated build with GitHub Actions (CI)

In addition to the local build described above, the repository includes a
GitHub Actions workflow — `.github/workflows/build-portable.yml` — that runs
**the same** `Build-Portable.ps1` on GitHub's Windows runners. This lets you
produce the portable ZIP without having a Windows machine of your own: the build
happens in the cloud and yields exactly the same package as the local build.

The workflow runs on `windows-latest` with **Python 3.13** and can be triggered
in two ways.

### Manual run (`workflow_dispatch`)

Useful for generating a ZIP on demand, e.g. to test a change.

| Step | Operation |
|------|-----------|
| 1 | Open the repository's **Actions** tab on GitHub |
| 2 | In the sidebar select the **"Build portable (Windows)"** workflow |
| 3 | Click **Run workflow**, choose the branch (usually `main`) and confirm |
| 4 | When it finishes, open the run and download the ZIP from the **Artifacts** section at the bottom of the summary page |

> **Note:** a manual run produces **only** the downloadable artifact. Publishing
> to a Release happens exclusively on version tags (see below), because the final
> step is gated by `if: startsWith(github.ref, 'refs/tags/')`.

### Automatic run on version tags (`v*`)

When you push a tag starting with `v` (e.g. `v8.0.0`), the workflow runs on its
own, builds the ZIP and **automatically attaches it to the corresponding GitHub
Release**:

```bash
git tag v8.0.0
git push origin v8.0.0
```

> **⚠️ Note:** the tag's version number should match the one in
> `pyproject.toml`, to keep the Release and the package consistent.

> **Permissions.** The step that attaches the file to the Release needs the
> `contents: write` permission, already declared in the workflow:
>
> ```yaml
> permissions:
>   contents: write
> ```
>
> If the release step fails with a permissions error, check under
> **Settings → Actions → General → Workflow permissions** that the repository's
> actions are not restricted to read-only.

Since the workflow reuses the same `Build-Portable.ps1`, the ZIP produced by CI
is identical to the one you would get locally (same folder structure and same
runtime paths described above).

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

The script does **not** delete the `build\` folder: it reuses the most recent
subfolder. For a truly clean rebuild, delete both the venv and `build\` before
running the script again:

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
