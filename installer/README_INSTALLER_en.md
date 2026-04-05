# How to build the Windows installer

In order to build the Windows installer you need to download:

- Windows x64 binaries of `uv`, e.g. [Releases · astral-sh/uv](https://github.com/astral-sh/uv/releases/)
- The [NSIS compiler](https://nsis.sourceforge.io/Download)
- The [INetC plug-in – NSIS amd64-unicode](https://nsis.sourceforge.io/Inetc_plug-in) (for the 64-bit installer)
- The [INetC plug-in – NSIS x86-unicode](https://nsis.sourceforge.io/Inetc_plug-in) (for the 32-bit installer)

Extract `uv.exe` from the zip into this folder.
Then launch the NSIS compiler and compile the appropriate `.nsi` script:

- **64-bit installer**: compile `songpressx64.nsi`
- **32-bit installer**: compile `songpressx32.nsi`

## Step-by-step compilation

1. Open the NSIS program
2. Click on **Compile NSI scripts**
3. Press **File → Load Script**
4. Select `songpressx64.nsi` (64-bit) or `songpressx32.nsi` (32-bit)
5. Click **Compile**

## NSI file

NSI file encoding: **UTF-16 LE with BOM** (required by NSIS Unicode mode).

The script contains:

```nsi
Unicode true
Target: NSIS_TARGET_X86   ; 32-bit installer only (songpressx32.nsi)
!addplugindir /amd64-unicode "plugins/64-bit"
!addplugindir /x86-unicode  "plugins/x86-bit"
!include "MUI2.nsh"
```

The version number is read automatically from `pyproject.toml` via `!searchparse`,
so it does not need to be updated manually in the NSI script.

## Notes

URL changed: the internet connection check uses `http://1.1.1.1/` — Cloudflare's IP,
which always responds in a few milliseconds without SSL, avoiding potential TLS hangs.

`inetc::head` → `inetc::get`: HEAD requests via INetC are notoriously unreliable on
Windows 10/11. Using `get` downloads a tiny body and works much more reliably.
The temporary file is deleted immediately afterwards.

## Folder structure

```
installer/
├── songpressx64.nsi
├── songpressx32.nsi
├── songpressplusplus.ico
├── uv.exe
├── license.txt
└── plugins/
    ├── 64-bit/
    │   └── INetC.dll      ← from the INetC zip, folder Plugins\amd64-unicode\
    └── x86-bit/
        └── INetC.dll      ← from the INetC zip, folder Plugins\x86-unicode\
```

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
into the correct destination at install time, so the user can edit them directly:

- **Standard install**: `%APPDATA%\Songpress++\templates\`
- **Portable install**: `<portable folder>\templates\` (next to the exe)

On uninstall the user is asked whether to delete the data folder (default: No).

## Installer page options

During installation a page is shown with the following options:

| Option | Default | Description |
|--------|---------|-------------|
| **Standard installation** | ✔ | Installs to `%LOCALAPPDATA%\Songpress++`, creates Start menu shortcuts |
| **Portable installation** | — | Installs to `%DESKTOP%\Songpress++`, no registry entries or shortcuts |
| **Associate extensions** | — | Associates `.crd .pro .chopro .chordpro .cho` with Songpress++ |
| **Check connection** | ✔ | Tests the Internet connection before downloading packages |
| **Desktop shortcut** | ✔ | Creates a `.lnk` shortcut on the Desktop (standard install only) |

The installer language (Italian/English) is selected at startup.

## Change program name and version

![Songpress++ change name and version](../src/songpress/img/GUIDE/Versione_en.png)

## Final result

If compilation succeeds, the following files will appear in the `installer/` folder:

```
songpress++-setup.exe        ← 64-bit installer
songpress++-setup-x32.exe   ← 32-bit installer
```

These are the Windows installers ready for distribution.

---
*This file is UTF-8 encoded without BOM.*
