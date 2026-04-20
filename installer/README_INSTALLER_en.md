# How to build the Windows installer

In order to build the Windows installer you need to download:

- Windows x64 binaries of `uv`, e.g. [Releases · astral-sh/uv](https://github.com/astral-sh/uv/releases/)
- The [NSIS compiler](https://nsis.sourceforge.io/Download)

Extract `uv.exe` from the zip into this folder.

> **Antivirus note — `uv.exe` is not a virus:** Some antivirus software may flag `uv.exe`
> as suspicious due to heuristic detection on next-generation executables. This is a
> **false positive**: `uv.exe` is a legitimate, safe, and widely adopted open-source tool
> in the Python ecosystem ([astral-sh/uv](https://github.com/astral-sh/uv)). If your
> antivirus blocks it, add an exception for the `installer/` folder.

Then launch the NSIS compiler and compile the appropriate `.nsi` script:

- **64-bit installer**: compile `songpress++64bit.nsi`
- **32-bit installer**: compile `songpress++x86.nsi`

## Step-by-step compilation

1. Open the NSIS program
2. Click on **Compile NSI scripts**
3. Press **File → Load Script**
4. Select `songpress++64bit.nsi` (64-bit) or `songpress++x86.nsi` (32-bit)
5. Click **Compile**

## NSI file

NSI file encoding: **UTF-16 LE with BOM** (required by NSIS Unicode mode).

The script contains:

```nsi
Unicode true
!include "MUI2.nsh"
```

No external DLLs or `!addplugindir` directives are needed: both installers use
**NScurl**, which is bundled with NSIS.

The version number is read automatically from `pyproject.toml` via `!searchparse`,
so it does not need to be updated manually in the NSI script.

## Internet connection check plugin

Both installers use **NScurl** (built-in NSIS) — no external DLL required.

```nsi
NScurl::http GET "http://1.1.1.1/" "$INSTDIR\nettest.tmp" /TIMEOUT 10000 /END
Pop $0   ; "OK" or error string
Delete "$INSTDIR\nettest.tmp"
```

URL: `http://1.1.1.1/` — Cloudflare's IP, always responds in milliseconds without SSL,
avoiding potential TLS hangs.

## Folder structure

```
installer/
├── songpress++64bit.nsi
├── songpress++x86.nsi
├── songpressplusplus.ico
├── uv.exe
├── license.txt
└── tools/
    ├── rcedit-x64.exe
    ├── rcedit-x86.exe
    ├── set_iconx64.bat
    └── set_iconx86.bat
```

> The `plugins/` folder is not needed: both installers use NScurl (built-in NSIS)
> and require no external DLLs.

## tools/ folder

The `tools/` folder contains utilities used **during the build process only** — they are
not included in the installer or the final application.

| File | Purpose |
|------|---------|
| `rcedit-x64.exe` | Command-line tool to embed an icon into a Windows `.exe` file (64-bit systems) |
| `rcedit-x86.exe` | Command-line tool to embed an icon into a Windows `.exe` file (32-bit systems) |
| `set_iconx64.bat` | Helper script for **64-bit** systems — uses `rcedit-x64.exe` |
| `set_iconx86.bat` | Helper script for **32-bit** systems — uses `rcedit-x86.exe` |

### How to use the bat scripts

Run the appropriate bat **after** building the application with cx_Freeze and **before**
compiling the NSIS installer, so that the final `.exe` already has the correct icon.

- On **64-bit** systems: use `set_iconx64.bat`
- On **32-bit** systems: use `set_iconx86.bat`

1. Double-click the correct bat (it will request administrator privileges automatically)
2. When prompted, drag and drop `SongPressPlusPlus.exe` onto the window (or paste its path)
3. When prompted, drag and drop `songpressplusplus.ico` onto the window (or paste its path)
4. The script will apply the icon and confirm success

> **Download rcedit**: https://github.com/electron/rcedit/releases — download both
> `rcedit-x64.exe` and `rcedit-x86.exe` and place them in the `tools/` folder.

> **Antivirus note**: Windows Defender may flag rcedit as `Exploit.PayloadProtect`.
> This is a **false positive** caused by the nature of the tool (it modifies exe binaries).
> To unblock it: Windows Security → Virus & threat protection → Protection history
> → select the detection → Actions → **Allow on device**.

The `installer\` folder must be placed directly inside the project root
(the one containing `pyproject.toml`), because the script uses `SRCDIR = ".."`.

## ⚠️ Do not install in Program Files

**Do not install Songpress++ into `C:\Program Files` or `C:\Program Files (x86)`.**

These folders are protected by UAC (User Account Control) and require administrator
privileges for any write operation. Songpress++ downloads and updates its packages at
runtime via `uv`: if installed in `Program Files`, these operations would fail silently
or produce access-denied errors.

Always use the default paths suggested by the installer (`%LOCALAPPDATA%` for the
standard installation, `%DESKTOP%` for the portable one), which require no elevated
privileges.

## Install paths

| What | Path |
|------|------|
| Application (standard) | `%LOCALAPPDATA%\Songpress++\bin\SongPressPlusPlus.exe` |
| Application (portable) | `%DESKTOP%\Songpress++\bin\SongPressPlusPlus.exe` |
| Song templates (standard) | `%APPDATA%\Songpress++\templates\songs\` |
| Slides templates (standard) | `%APPDATA%\Songpress++\templates\slides\` |
| Fonts (standard) | `%APPDATA%\Songpress++\templates\fonts\` |
| Song templates (portable) | `<install folder>\templates\songs\` |
| Slides templates (portable) | `<install folder>\templates\slides\` |
| Fonts (portable) | `<install folder>\templates\fonts\` |

The entire `templates\` folder (including all subfolders: `songs`, `slides`, `fonts`
and any future additions) is copied recursively from the uv package tree
into the correct destination at install time.

- **Standard install**: `%APPDATA%\Songpress++\templates\`
- **Portable install**: `<install folder>\templates\` (next to the exe)

On uninstall the user is asked whether to delete the data folder (default: No).

## Installer page options

| Option | Default | Description |
|--------|---------|-------------|
| **Standard installation** | ✔ | Installs to `%LOCALAPPDATA%\Songpress++`, creates Start menu shortcuts |
| **Portable installation** | — | Installs to `%DESKTOP%\Songpress++`, no registry entries or shortcuts |
| **Associate extensions** | ✔ | Associates `.crd .pro .chopro .chordpro .cho .tab` with Songpress++ |
| **Check connection** | ✔ | Tests the Internet connection before downloading packages |
| **Desktop shortcut** | ✔ | Creates a `.lnk` shortcut on the Desktop (standard install only) |

The installer language (Italian/English) is selected at startup.

## File association and legacy ProgID cleanup

The installers register file extensions under the ProgID `SongpressPlusPlus.ChordPro`
in the user registry (`HKCU\Software\Classes`).

Earlier versions of the installer used the incorrect ProgIDs `Songpress.crd` and
`Songpress.ChordPro`, which could prevent `.crd` files from opening with a double-click
even after reinstalling. The current `.nsi` scripts include **automatic cleanup** of both
legacy ProgIDs:

- **During installation**: before registering the new associations, the scripts remove
  `HKCU\Software\Classes\Songpress.crd`, `HKCU\Software\Classes\Songpress.ChordPro` and
  their `OpenWithProgids` entries for each managed extension (`.crd`, `.pro`, `.chopro`,
  `.chordpro`, `.cho`).
- **During uninstallation**: both legacy ProgID keys and their `OpenWithProgids` entries
  are deleted; then all references to `SongpressPlusPlus.ChordPro` are removed
  **selectively**: the `Default` value and the `OpenWithProgids` entry for each managed
  extension, plus the `HKCU\Software\Classes\SongpressPlusPlus.ChordPro` key itself.
  The `.EXT` keys are **not deleted outright**, to avoid accidentally removing associations
  belonging to other programs on the same system.

## Required disk space shown by the wizard

The wizard always shows **100 KB** as required space, because NSIS only counts the files
physically included in the package (in this case just the `.ico` icon). The bulk of the
installation — Python, uv packages, tools — is downloaded and installed at runtime by
`uv tool install`, and NSIS has no way to calculate it in advance.

To show a realistic estimate, the script includes the `AddSize` directive:

```nsi
Section "Songpress++" SongpressSection
  SectionIn RO
  AddSize 117760   ; estimated size: ~115 MB (uv + Python + packages)
  SetOutPath "$INSTDIR"
```

The value `117760` equals 115 MB (115 × 1024 KB). If the real installation size changes
in the future, update this value by measuring the `$INSTDIR\bin`, `$INSTDIR\tools` and
`$INSTDIR\python` folders after a complete installation.

## Change program name and version

![Songpress++ change name and version](../src/songpressplusplus/img/GUIDE/Versione_en.png)

## Final result

If compilation succeeds, the following files will appear in the `installer/` folder:

```
songpress++64bit-setup.exe        ← 64-bit installer
songpress++x86-setup.exe          ← 32-bit installer
```

### Recommended build order

1. Build the application with cx_Freeze
2. Run `tools\set_iconx64.bat` (or `set_iconx86.bat` on 32-bit) to embed the icon into `SongPressPlusPlus.exe`
3. Compile the NSIS script to generate the installer

## Notes

### SongpressOpen.pyw

After installation, the file `SongpressOpen.pyw` may appear in the `bin\` folder.
This is a leftover from the original Songpress by Luca Allulli and is not referenced
anywhere in the project (neither in `pyproject.toml` nor in the NSI scripts).
**It can be safely deleted.**

---
*This file is UTF-8 encoded without BOM.*
