# How to build the Windows installer

In order to build the Windows installer you need to download:

- Windows x64 binaries of `uv`, e.g. [Releases · astral-sh/uv](https://github.com/astral-sh/uv/releases/)
- The [NSIS compiler](https://nsis.sourceforge.io/Download)

Extract `uv.exe` from the zip into this folder.
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
└── license.txt
```

> The `plugins/` folder is not needed: both installers use NScurl (built-in NSIS)
> and require no external DLLs.

The `installer\` folder must be placed directly inside the project root
(the one containing `pyproject.toml`), because the script uses `SRCDIR = ".."`.

## Install paths

| What | Path |
|------|------|
| Application (standard) | `%LOCALAPPDATA%\Songpress++\bin\songpress.exe` |
| Application (portable) | `%DESKTOP%\Songpress++\bin\songpress.exe` |
| Song templates (standard) | `%APPDATA%\Songpress++\templates\songs\` |
| Slides templates (standard) | `%APPDATA%\Songpress++\templates\slides\` |
| Fonts (standard) | `%APPDATA%\Songpress++\templates\fonts\` |
| Song templates (portable) | `%DESKTOP%\Songpress++\templates\songs\` |
| Slides templates (portable) | `%DESKTOP%\Songpress++\templates\slides\` |
| Fonts (portable) | `%DESKTOP%\Songpress++\templates\fonts\` |

The entire `templates\` folder (including all subfolders: `songs`, `slides`, `fonts`
and any future additions) is copied recursively from the uv package tree
into the correct destination at install time.

- **Standard install**: `%APPDATA%\Songpress++\templates\`
- **Portable install**: `<portable folder>\templates\` (next to the exe)

On uninstall the user is asked whether to delete the data folder (default: No).

## Installer page options

| Option | Default | Description |
|--------|---------|-------------|
| **Standard installation** | ✔ | Installs to `%LOCALAPPDATA%\Songpress++`, creates Start menu shortcuts |
| **Portable installation** | — | Installs to `%DESKTOP%\Songpress++`, no registry entries or shortcuts |
| **Associate extensions** | — | Associates `.crd .pro .chopro .chordpro .cho` with Songpress++ |
| **Check connection** | ✔ | Tests the Internet connection before downloading packages |
| **Desktop shortcut** | ✔ | Creates a `.lnk` shortcut on the Desktop (standard install only) |

The installer language (Italian/English) is selected at startup.

## File association and legacy ProgID cleanup

The installers register file extensions under the ProgID `Songpress.ChordPro`
in the user registry (`HKCU\Software\Classes`).

Earlier versions of the installer used the incorrect ProgID `Songpress.crd`, which
could prevent `.crd` files from opening with a double-click even after reinstalling.
The current `.nsi` scripts include **automatic cleanup** of this legacy ProgID:

- **During installation**: before registering the new associations, the scripts remove
  `HKCU\Software\Classes\Songpress.crd` and its `OpenWithProgids` entries for all
  managed extensions.
- **During uninstallation**: the legacy ProgID is also removed if still present.

If file association does not work on a system with an old installation, the registry
can be corrected manually by importing `fix_songpress_assoc.reg`
(available in the `installer\` folder).

## Change program name and version

![Songpress++ change name and version](../src/songpress/img/GUIDE/Versione_en.png)

## Final result

If compilation succeeds, the following files will appear in the `installer/` folder:

```
songpress++64bit-setup.exe        ← 64-bit installer
songpress++x86-setup.exe          ← 32-bit installer
```

---
*This file is UTF-8 encoded without BOM.*
