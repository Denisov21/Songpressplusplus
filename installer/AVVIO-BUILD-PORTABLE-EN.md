# How to start building the portable version of Songpress++

The script `installer\Build-Portable.ps1` creates a portable ZIP of Songpress++ using cx_Freeze in a dedicated venv (`.venv-build`).

## Requirements

- Windows with **PowerShell**
- **Python** installed and reachable with the `python` command (check with `python --version`)
- Internet connection (on the first run it downloads the dependencies: wxPython, cx_Freeze, etc.)
- `pyproject.toml` in the project root, with a `version = "x.y.z"` line and a `[tool.cxfreeze.build_exe]` section

## Starting the build

1. Open **PowerShell** (administrator rights are not required).
2. Go to the project folder (the **root**, the one containing `pyproject.toml` and the `src` and `installer` folders).

   > ⚠️ **Note:** the path below is only an **example** and must be **checked**. Replace it with the actual path where you cloned or extracted the project on your system.

   ```powershell
   cd "E:\Users\Utente\Documents\GitHub\songpressplusplus"
   ```

   Check that you are in the right folder:

   ```powershell
   Get-Location
   Test-Path .\pyproject.toml
   Test-Path .\installer\Build-Portable.ps1
   ```

   - `Get-Location` shows the current path.
   - Both `Test-Path` commands must answer `True`. If either answers `False`, you are in the wrong folder.
   - Tip: in File Explorer, open the project folder, click the address bar, copy the path and paste it after `cd` between quotes.

3. Run the script **with the execution policy bypass** (on Windows PowerShell 5.1 scripts are disabled by default, so plain `.\installer\Build-Portable.ps1` fails with the error "running scripts is disabled on this system"):

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\installer\Build-Portable.ps1
   ```

   The bypass applies only to this command: system settings are not changed.

> The script uses `$PSScriptRoot`, so it also works if you run it from the `installer` folder with `-File .\Build-Portable.ps1`: the project root is computed automatically as the parent folder.

### Alternatives for the "script execution disabled" error

For the current session only (everything goes back to normal when you close the window):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\installer\Build-Portable.ps1
```

If a confirmation prompt appears, answer `Y`.

Permanently, for your user only:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## What the script does

| Step | Operation |
|------|-----------|
| 1 | Creates the `.venv-build` venv (or reuses it if it already exists) |
| 2 | Installs the dependencies with pip |
| 3 | Runs `cx_Freeze build_exe` (with `src` added to `PYTHONPATH`) |
| 4 | Locates the folder produced in `build\` |
| 5 | Copies the fonts into `templates\fonts` |
| 6 | Creates the ZIP in `dist\` |

The first run takes a few minutes (mostly installing the dependencies); later runs are faster because the venv is reused.

## Result

The ZIP is created at:

```
dist\Songpress++-<version>-portable.zip
```

The version is read from `pyproject.toml`. To use the program: extract the ZIP to any folder (even a USB drive) and start:

```
.\Songpress++.exe
```

## Starting Songpress++ from the ZIP

1. **Unblock the ZIP (recommended)**: if you downloaded or copied it from another computer, right-click the `.zip` file → **Properties** → check **Unblock** → **OK**. This stops Windows from blocking the extracted files.
2. **Extract all**: right-click the `.zip` file → **Extract All...** → choose a folder (a USB drive is fine). Do not run the program from inside the ZIP: it must be extracted first.
3. Open the extracted folder (the ZIP contains a folder with the program files) and double-click **`Songpress++.exe`**.

Alternatively, from PowerShell (replace the path with the real path of the extracted folder):

```powershell
cd "C:\Path\to\the\extracted\folder"
.\Songpress++.exe
```

Notes:

- Do not move or delete the files and folders next to `Songpress++.exe` (for example `templates\fonts`): the program needs them.
- If Windows shows "Windows protected your PC" (SmartScreen), click **More info** → **Run anyway**. This happens because the executable is not digitally signed.
- If your antivirus blocks or quarantines the executable, add the folder to its exclusions and extract the ZIP again.
- To clean up or update, just delete the extracted folder and extract the new ZIP.

## Common problems

- **`python` not recognized**: Python is not in the PATH. Reinstall it checking "Add Python to PATH", or use the `py` launcher.
- **`Impossibile leggere la versione da pyproject.toml`** (cannot read the version): the `version = "..."` line is missing, or it does not start at the beginning of a line in the file.
- **`No module named songpressPlusPlus`**: check that the `src` folder with the package exists; the script already adds it to `PYTHONPATH`.
- **Errors on a dependency (e.g. wxPython, pyenchant)**: check that your Python version is compatible with those package versions.
- **Strange errors after editing the script by hand** (for example `Impossibile recuperare la variabile $Pip perché non è stata impostata`, i.e. "cannot retrieve the variable $Pip because it is not set"): this is an encoding problem. Windows PowerShell 5.1 reads files without a BOM as ANSI, and the special characters in the script (`—`, `─`) break the strings. To prevent this from happening again when you edit the script by hand, always save it as “UTF-8 with BOM” (in VS Code: status bar at the bottom → Save with Encoding → UTF-8 with BOM).
- **Clean build**: if something is left in an inconsistent state, delete the `.venv-build`, `build` and `dist` folders and run the script again.
