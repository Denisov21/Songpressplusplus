# Songpress++ — Installing from the `.tar` package

Guide to **installing**, **launching** and **uninstalling** the Songpress++
package distributed as a tarball (`.tar.gz` or `.tar.xz`).

The tarball contains:

```
songpressplusplus-<version>/
├── usr/            # the application files (same tree as the .deb package)
├── install.sh      # installs: dependencies + files + system caches
├── uninstall.sh    # uninstalls: removes the files and restores the caches
└── README.txt      # short bilingual summary
```

> **Note.** Unlike the `.deb`, a tarball has no package manager behind it:
> `install.sh` is the one that handles the system dependencies (via `apt`), the
> PyPI-only dependencies and the refresh of the desktop/MIME/icon caches.

> **Still need to create the tarball?** If you don't have the
> `songpressplusplus-<version>.tar.gz` file but you do have the project sources,
> jump straight to the [Appendix — Building the package with `build_tar.sh`](#appendix--building-the-tar-package-with-build_tarsh).

---

## 1. Requirements

- A **Debian/Ubuntu** distribution (or a derivative) with `apt`.
  On other distributions copying the files still works, but the system
  dependencies have to be installed by hand (see §7).
- **Root privileges** (`sudo`): the installation writes under `/usr`.
  The scripts re-run themselves with `sudo` if launched as a normal user.
- An **Internet connection**, used to download the dependencies.
  With `--no-deps` only the files are copied, without touching the network (see §4).

---

## 2. Installation

From the `songpressplusplus-<version>.tar.gz` (or `.tar.xz`) file:

```bash
# 1. Extract the archive
tar xf songpressplusplus-<version>.tar.gz

# 2. Enter the extracted folder
cd songpressplusplus-<version>

# 3. Install
sudo ./install.sh
```

`tar xf` detects the compression on its own, so the same command works for both
`.tar.gz` and `.tar.xz`.

During installation the script:

1. removes any leftovers of old installations under `/usr/local`
   (only if they don't belong to another package);
2. installs the **system dependencies** with `apt` (asks for confirmation);
3. copies the files under `/usr` and writes a **manifest** for uninstalling;
4. refreshes the desktop, MIME, icon and AppStream caches;
5. installs the **PyPI-only dependencies** (`python-pptx`, `pyshortcuts`) with
   `pip` (asks for confirmation).

When it finishes you'll see an `✔ Installation complete` message.

---

## 3. Launching

After installation the application is available in three ways:

- **From the applications menu** of the desktop, as the **Songpress++** entry
  (Office / Publishing categories).
- **From a terminal**, with either of these (equivalent) commands:

  ```bash
  SongpressPlusPlus
  songpressplusplus      # all-lowercase alias
  ```

- **By opening a song file** (`.crd`, `.cho`, `.chordpro`, `.chopro`, `.pro`,
  `.sng`): they are automatically associated with Songpress++.

> **Why the command forces X11.** Launching goes through a wrapper that sets
> `GDK_BACKEND=x11` for compatibility with wxPython on Wayland. To see the full
> debug output (without the filter that hides the harmless GTK messages):
>
> ```bash
> SONGPRESS_VERBOSE=1 SongpressPlusPlus
> ```

---

## 4. Installation options

`install.sh` accepts a few options:

| Option         | Effect |
|----------------|--------|
| `--prefix DIR` | Install under `DIR` instead of `/usr` (see §5). |
| `--no-deps`    | Copy **the files only**: no `apt`, no `pip`, no network. |
| `-y`, `--yes`  | Answer "yes" to every prompt (useful in non-interactive scripts). |
| `-h`, `--help` | Show the help. |

Examples:

```bash
# Install without touching the dependencies (you manage them yourself)
sudo ./install.sh --no-deps

# Non-interactive install, fully automatic
sudo ./install.sh -y
```

---

## 5. Installing to a prefix other than `/usr`

By default everything goes under `/usr`, just like the `.deb` would. You can,
however, choose a different prefix, for example for a local installation:

```bash
sudo ./install.sh --prefix /usr/local
```

When the prefix is **not** `/usr`, `install.sh` automatically adjusts the
absolute paths:

- it rewrites the binary path in the **wrapper** and in the **`.desktop`** file;
- it sets `PYTHONPATH` in the wrapper, so the Python modules stay importable even
  outside the standard system paths.

> Remember the prefix you used: you'll need the same value to uninstall
> (`uninstall.sh --prefix ...`).

---

## 6. Uninstalling

From the same extracted folder (the one containing `uninstall.sh`):

```bash
sudo ./uninstall.sh
```

If you installed with a different prefix, pass it again:

```bash
sudo ./uninstall.sh --prefix /usr/local
```

The script reads the **manifest** created during installation and removes exactly
the files it had copied, then restores the system caches. If the manifest is gone
(folder moved or deleted), it falls back to the `usr/` tree sitting next to the
script.

`uninstall.sh` options:

| Option         | Effect |
|----------------|--------|
| `--prefix DIR` | Prefix to uninstall from (default `/usr`). |
| `--purge`      | Also remove the **user data** in `~/.Songpress++`. |
| `-h`, `--help` | Show the help. |

```bash
# Full removal, user data included
sudo ./uninstall.sh --purge
```

> **What is NOT removed.** The dependencies installed by `apt` and `pip` stay on
> the system, exactly as `dpkg -r` would leave them. Without `--purge` the user
> data in `~/.Songpress++` is kept too.

---

## 7. Dependencies (for reference)

If you install with `--no-deps`, or on a distribution without `apt`, you'll have
to install these dependencies by hand.

**System** (in the Debian/Ubuntu repositories):

```
python3 (>= 3.12), python3-pip, python3-wxgtk4.0 | python3-wxpython4,
python3-requests, python3-reportlab, python3-markdown, python3-mistune,
python3-pypdf, python3-enchant, xdg-utils
```

**Recommended** (they improve the experience but aren't required):

```
wl-clipboard, hunspell-it, hunspell-en-us
```

**PyPI-only** (not in the Debian repositories, installed with `pip`):

```bash
sudo pip3 install --break-system-packages python-pptx pyshortcuts
```

---

## 8. Troubleshooting

**"The installation asks for a password"**
`install.sh` and `uninstall.sh` need root privileges and re-run themselves with
`sudo`: type your password when prompted, or launch them with `sudo ./install.sh`
in the first place.

**"An Internet connection is required"**
Copying the files is local, but installing the dependencies downloads packages
from `apt` and from PyPI. If you're offline use `--no-deps` and install the
dependencies later (§7).

**"The app won't start or shows graphical errors on Wayland"**
Launching already forces `GDK_BACKEND=x11`. To see the full messages:

```bash
SONGPRESS_VERBOSE=1 SongpressPlusPlus
```

**"I installed with a prefix but the app can't find the Python modules"**
Make sure you used `install.sh --prefix ...` (which sets `PYTHONPATH` in the
wrapper), not a manual copy of the files.

**"The menu entry or the icon don't show up right away"**
The caches are refreshed at the end of the installation. If needed, log out and
back into the desktop session, or refresh them by hand:

```bash
sudo update-desktop-database -q /usr/share/applications
sudo gtk-update-icon-cache -qf /usr/share/icons/hicolor
```

---

## 9. Command summary

```bash
# Install
tar xf songpressplusplus-<version>.tar.gz
cd songpressplusplus-<version>
sudo ./install.sh

# Launch
SongpressPlusPlus

# Uninstall
sudo ./uninstall.sh            # add --purge to remove ~/.Songpress++
```

---

## Appendix — Building the `.tar` package with `build_tar.sh`

This section is for **whoever builds and distributes** the package, not for the
end user. It's used to generate the `songpressplusplus-<version>.tar.gz` file
from the project sources.

### A.1 Build requirements

- The same as `build_deb.sh`: **Python ≥ 3.12**, `pip`, and an Internet
  connection (the wheel is built by downloading `hatchling` and the build
  dependencies from PyPI).
- `tar` and the compressor for the chosen format: `gzip` for `.tar.gz`,
  `xz-utils` for `.tar.xz`.
- The project files in the same folder as the script: `pyproject.toml`
  (from which name and version are read) and `build_deb.sh`.

### A.2 How it works

`build_tar.sh` **reuses the payload** that `build_deb.sh` produces
(`build_deb/<name>_<version>/usr`), so the source patches and the wheel build are
not duplicated. If that payload doesn't exist — or if you pass `--rebuild` — the
script runs `build_deb.sh` itself to build it. It then places `install.sh`,
`uninstall.sh` and `README.txt` next to it and creates the archive.

### A.3 Running it

```bash
# 1. Make the script executable (once)
chmod +x build_tar.sh

# 2. Build the package (default: .tar.gz)
./build_tar.sh
```

When it finishes the script prints the path of the archive, which ends up in:

```
build_tar/songpressplusplus-<version>.tar.gz
```

> **No `sudo` needed.** The build runs as a normal user; the files inside the
> archive are still owned by `root` (as in the `.deb`).

### A.4 Options

| Option             | Effect |
|--------------------|--------|
| `--format gz`      | `.tar.gz` archive (default). |
| `--format xz`      | `.tar.xz` archive (better compression, slower). |
| `--format tar`     | Uncompressed `.tar`. |
| `-z` / `-J`        | Shorthands for `--format gz` / `--format xz`. |
| `--rebuild`        | Rebuild the payload even if it already exists. |
| `-y`, `--yes`      | Ask no questions (useful in CI). |
| `-h`, `--help`     | Show the help. |

Examples:

```bash
# .tar.xz archive
./build_tar.sh --format xz

# Clean rebuild of the payload, no questions
./build_tar.sh --rebuild -y
```

### A.5 Environment variables

| Variable          | Effect |
|-------------------|--------|
| `SPP_TAR_FORMAT`  | Default format (`gz` \| `xz` \| `tar`). |
| `SPP_ASSUME_YES=1`| Equivalent to `-y`. |
| `SPP_DEB_SCRIPT`  | Path to `build_deb.sh`, if it isn't next to `build_tar.sh`. |
| `SPP_BUILD_LANG`  | Language of the build messages (`it` \| `en`). |

### A.6 Quick check

After the build you can inspect the archive's contents without extracting it:

```bash
tar tf build_tar/songpressplusplus-<version>.tar.gz | head
```

You should see the `songpressplusplus-<version>/` folder containing `usr/`,
`install.sh`, `uninstall.sh` and `README.txt`. At that point the package is ready
to be distributed and installed as described in §2–§6.
