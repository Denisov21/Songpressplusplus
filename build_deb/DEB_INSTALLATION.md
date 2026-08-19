# Songpress++ — Building and installing the `.deb` package

This guide covers **only** how to build the Debian package (`.deb`) of
Songpress++ and how to install it on Linux (Debian/Ubuntu and derivatives).

---

## Prerequisites

Make sure the following packages are installed on your system:

```bash
sudo apt install python3 python3-pip python3-venv fakeroot dpkg imagemagick
```

> **Wayland users:** to copy the song to the clipboard **as an image**, the
> `wl-clipboard` package (which provides `wl-copy`) is required. The `.deb`
> package lists it under `Recommends`, so `apt` installs it automatically. If
> you run from source on a Wayland session, install it manually:
> ```bash
> sudo apt install wl-clipboard
> ```
> On X11 sessions it is not needed. To find out which session you are on:
> ```bash
> # quick
> echo "$XDG_SESSION_TYPE"      # prints  wayland  or  x11
> # authoritative (systemd-logind, recommended on modern distros)
> loginctl show-session "$(loginctl --no-legend list-sessions | awk -v u="$USER" '$3==u {print $1; exit}')" -p Type --value
> ```

---

## Building the `.deb` package

The `build_deb.sh` script is located in the project root, next to `pyproject.toml`.

### 1. Enter the project folder

> **⚠️ Note:** the path below is just an **example** and **must be verified**. Replace it with the actual path where the project is located on your system.

```bash
cd /home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus
```

### 2. Make the script executable (first time only)

```bash
chmod +x build_deb.sh
```

### 3. Run the script

```bash
./build_deb.sh
```

The script automatically performs the following steps:

- Reads the package name and version from `pyproject.toml`
- Builds the Python wheel using `pip` and `hatchling`
- Installs the wheel into the package tree
- Normalises the layout to comply with Debian Policy (files are moved from
  `usr/local/` to `usr/`, modules into `usr/lib/python3/dist-packages`)
- Creates a `GDK_BACKEND=x11` wrapper for Wayland compatibility
- Creates a lowercase symlink `songpressplusplus` → `SongpressPlusPlus`
- Generates the application menu entry (`.desktop` file), the `text/x-chordpro`
  MIME type and the `hicolor` icons
- Writes the `postinst`/`postrm` scripts (system cache updates and installation
  of the PyPI-only dependencies)
- Produces the final `.deb` file in the `build_deb/` folder

When done, you will see (the version number shown is only an **example** — it depends on the one in `pyproject.toml`):

```
✅  Pacchetto creato: build_deb/songpressplusplus_8.0.2_all.deb
```

### Structure of the `build_deb/` folder

When the build finishes, the `build_deb/` folder contains the two documentation
files (this guide and its Italian counterpart) plus three generated items (the
version number — `8.0.2` here — depends on `pyproject.toml`):

```
build_deb/
├── DEB_INSTALLATION.md               ← this guide (English)
├── INSTALLAZIONE_DEB.md              ← Italian guide
├── songpressplusplus_8.0.2/          ← package staging tree
│   ├── DEBIAN/                        ← metadata and maintainer scripts
│   │   ├── control                    ← name, version, Depends, Maintainer…
│   │   ├── preinst                    ← removes /usr/local leftovers
│   │   ├── postinst                   ← PyPI deps + system cache refresh
│   │   └── postrm                     ← cleanup on removal
│   └── usr/                           ← what gets copied into the filesystem
│       ├── bin/SongpressPlusPlus      ← executable wrapper (GDK_BACKEND=x11)
│       ├── lib/python3/dist-packages/songpressplusplus/   ← program code
│       └── share/                     ← .desktop, MIME, hicolor icons, metainfo
├── wheel/                            ← intermediate Python wheel (.whl)
│   └── songpressplusplus-8.0.2-py3-none-any.whl
└── songpressplusplus_8.0.2_all.deb   ← final package to install
```

What they are and what they are for:

- **`songpressplusplus_<version>/`** — the **staging tree**: an exact copy of
  what the package will install on the system, plus the `DEBIAN/` folder
  (metadata and scripts). From this folder `dpkg-deb --build` produces the
  `.deb`. It is an intermediate artifact: you can inspect it to verify what will
  land on the system, but to install you only need the `.deb`.
- **`wheel/`** — holds the **Python wheel** (`.whl`) built with `hatchling`, the
  intermediate step from which the modules are extracted and installed into the
  staging tree. Also a build artifact.
- **`songpressplusplus_<version>_all.deb`** — the **final package**, the only
  file you need to install (or distribute) the program. The `_all` suffix means
  the package is architecture-independent (pure Python), so the same `.deb`
  works on amd64, arm64, etc.

> **Note:** the two folders (`songpressplusplus_<version>/` and `wheel/`) can be
> safely deleted after the build — they are regenerated every time `build_deb.sh`
> runs. Keep only the `.deb` file if you want to archive or distribute that
> version. At the start of each run `build_deb.sh` removes **only** these
> generated artifacts (staging tree, `wheel/`, and any previous `.deb`): the
> documentation files living in `build_deb/` are left untouched.

---

## Installing the `.deb` package

> **⚠️ Note:** the version number (`8.0.2`) is only an **example** and **must be verified**: use the one actually produced by the script, shown on screen at the end of the build.

```bash
sudo dpkg -i "build_deb/songpressplusplus_8.0.2_all.deb"
```

If any dependencies are missing:

```bash
sudo apt-get install -f
```

> **🌐 An Internet connection is required.** Two Python dependencies
> (`python-pptx` and `pyshortcuts`) are not packaged in the Debian repositories
> and are downloaded from PyPI during installation. The `postinst` warns you and
> asks for confirmation.
>
> **Installer language.** The installation messages follow the system locale:
> **Italian** on an Italian system, **English** on any other locale (English is
> the default, so any non-Italian system is covered). On a non-Italian system
> the prompt reads:
>
> ```
> 🌐  Continue and download the dependencies now? [Y/n]
> ```
>
> Answering `n` still installs the package, but you will have to finish the job
> manually:
>
> ```bash
> sudo pip3 install --break-system-packages python-pptx pyshortcuts
> ```
>
> The prompt only appears on a terminal: when installing from Discover or GDebi,
> or with `DEBIAN_FRONTEND=noninteractive`, the download starts unattended.

> **Status markers during installation.** While it handles the dependencies the
> `postinst` prints the same colour-coded markers used by the build script:
> `🌐` marks a network operation (download from PyPI), `✔` a completed step (a
> dependency already present or just installed), `⚠` a non-fatal problem (the
> download skipped at your request), and `✘` an error (a dependency could not be
> installed — the message shows how to finish by hand). The colours appear only
> on a terminal; from Discover/GDebi, or when the output is redirected to a file,
> the plain symbols are used. A successful run looks roughly like this:
>
> ```
> 🌐 Songpress++: checking PyPI dependencies (requires an Internet connection)...
> ✔ Songpress++: dependency 'python-pptx' already present.
> 🌐 Songpress++: installing 'pyshortcuts' via pip...
> ✔ Songpress++: 'pyshortcuts' installed.
> ```

**Installation folder.** The package installs the program files into the system
`dist-packages` tree:

```
/usr/lib/python3/dist-packages/songpressplusplus/
```

and the executable into `/usr/bin/SongpressPlusPlus`.

> **⚠️ Note:** the path does **not** include the Python version (`python3`, not
> `python3.13`): this is the only system directory actually present in `sys.path`
> on Debian, so the package keeps working across Python upgrades. The folder is
> owned by `root` and is therefore read-only for the user: personal templates and
> themes are stored in the user data folder instead.

> **⚠️ Upgrading from an earlier version.** Up to 7.0.1 the package installed
> under `/usr/local/`, a path that Debian Policy reserves for the local
> administrator. Migration is **automatic**: the package `preinst` script
> removes the leftovers before unpacking and reports what it did. It only removes
> files from the old installation, and only after checking with `dpkg-query` that
> no package claims them; anything else under `/usr/local` is left alone. To check
> which copy is actually in use:
>
> ```bash
> python3 -c "import songpressplusplus, os; print(os.path.dirname(songpressplusplus.__file__))"
> ```

---

## Graphical installation (double-click)

Double-clicking a `.deb` file in a desktop environment (e.g. KDE Plasma) normally opens **Discover**. However, Discover's PackageKit backend handles **local** `.deb` files poorly when they have external dependencies and a `postinst` that downloads packages from PyPI/apt (like this one): it often fails to resolve the package's `Depends:`, so the installation stops halfway or does not start at all.

For a reliable graphical installation, use a **dedicated installer** that resolves dependencies. On Debian 13 (trixie) the package is **`gdebi`** (the GUI; `gdebi-core` is the command-line version only):

```bash
sudo apt install gdebi
```

> **Note:** older Debian versions also shipped `qapt-deb-installer` (QApt, the native Qt/KDE installer), but it has been **removed** from the repositories as of trixie; likewise `gdebi-kde` no longer has an installable package. Use `gdebi`.

Then, in Dolphin: right-click the `.deb` → _Open With…_ → choose "GDebi Package Installer", ticking the option to always use it for this file type. On the next double-click the `.deb` will be installed through a graphical dialog that resolves dependencies on its own.

> **Note:** GDebi's GUI is GTK-based, so on KDE it pulls in a few small GTK dependencies and looks slightly less native, but it works correctly. If it misbehaves, use the terminal `apt` method below, which is the most reliable.

> **✅ Alternatively (more robust): `apt` from the terminal.** Use `apt` instead of `dpkg`, so it resolves dependencies automatically from the repositories:
>
> ```bash
> sudo apt install ./songpressplusplus_8.0.2_all.deb
> ```
>
> The `./` prefix (or a full path) is **mandatory**: without at least one `/` in the name, `apt` treats the argument as the name of a package to look up in the repositories and returns "unable to locate package". If you are not in the `.deb`'s folder, pass the full path, e.g. `sudo apt install ~/…/build_deb/songpressplusplus_8.0.2_all.deb`.

---

## Upgrading to a new version

### 1. Update the version in `pyproject.toml`

```toml
[project]
version = "8.0.2"   # ← change this number
```

### 2. Remove the installed version, rebuild and reinstall

```bash
sudo dpkg -r songpressplusplus
./build_deb.sh
```

When the script finishes, `build_deb/` will contain the new `.deb` with the
updated version number. Install it using the command printed by the script, for example:

```bash
sudo dpkg -i "build_deb/songpressplusplus_8.0.2_all.deb"
```

> **Tip:** you don't need to remember the exact version number — you can use
> shell Tab completion after typing
> `sudo dpkg -i "build_deb/songpressplusplus_`, or simply copy the command
> that the script prints at the end of the build.

---

## Uninstalling

```bash
sudo dpkg -r songpressplusplus
```

---

## Launching the program

After installation, the program can be launched in three ways:

**From the terminal:**
```bash
SongpressPlusPlus
# or (lowercase)
songpressplusplus
```

**From the application menu** (KDE/GNOME): search for "Songpress" in the launcher.

> The installed wrapper automatically sets `GDK_BACKEND=x11` to ensure
> compatibility with wxPython on Wayland systems. No manual configuration is
> needed. To see the raw output (useful for debugging):
>
> ```bash
> SONGPRESS_VERBOSE=1 SongpressPlusPlus
> ```

---
*This file is encoded in UTF-8 without BOM.*
