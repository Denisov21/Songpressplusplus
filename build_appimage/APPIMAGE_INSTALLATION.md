# Songpress++ — AppImage Guide (install, use, uninstall)

This guide covers the `SongpressPlusPlus-<version>-<arch>.AppImage` file
produced by `build_appimage.sh`. It is independent from the `.deb` build:
both can coexist on the same machine without conflicts, since the AppImage
never touches `/usr` or the system package manager.

> 🌐 **Note:** building the AppImage requires an Internet connection (see
> `build_appimage.sh`). Once built, the `.AppImage` file **works offline**:
> it already bundles Python, wxPython, and the required libraries.

---

## 0. What it is: a portable installation

The AppImage **is not an installation in the traditional sense** — it's a
*portable* package. Everything the application needs (Python, wxPython, the
libraries) lives inside a single executable file, which you can keep
anywhere — your home folder, a USB stick, a shared network folder — and
move from one compatible Linux machine to another without reinstalling
anything: just copy the file.

It doesn't modify the system (no files under `/usr`, no entry in the
package manager's database), requires no root privileges, and can be
removed by simply deleting the file. That's why some steps in this guide
(menu icon, file association) are **optional**: the app works without them.

### Pros and cons compared to the `.deb` package

**Pros:**
- **Real portability**: a single file, no system-wide install, works on
  any sufficiently recent Linux distribution (Debian, Fedora, openSUSE,
  Arch, etc.), not just Debian/Ubuntu derivatives.
- **No root privileges required**, either to use it or to remove it.
- **No dependencies to resolve**: Python, wxPython, and the Python
  libraries (pptx, reportlab, etc.) are already inside the file.
- **Works offline** once built: unlike the `.deb`, whose `postinst`
  downloads dependencies from PyPI during installation, the AppImage
  doesn't contact the network to run.
- **Peaceful coexistence**: it can be installed alongside the `.deb` on the
  same machine with no file conflicts.
- **Multiple versions side by side**: you can keep several `.AppImage`
  files of different versions in the same folder and launch whichever you
  want.

**Cons:**
- **Larger file**: it bundles Python, wxPython, GTK, and native libraries,
  so it's much heavier than the `.deb` (which relies on system libraries
  already present).
- **No automatic integration**: by default it doesn't show up in the
  application menu or associate file types; it needs to be integrated
  manually or with AppImageLauncher (§2a).
- **No automatic updates**: no `apt upgrade`. Updating means
  downloading/building the new file and replacing the old one (§3);
  third-party tools like AppImageUpdate exist for incremental updates, but
  aren't covered by this guide.
- **Requires FUSE** for automatic mounting (workaround available, see §8).
- **Tied to the build machine's ABI**: since it's built against the native
  system libraries (glibc, GTK) of the machine that created it, it may fail
  to start on distributions much older than the build one. The `.deb`,
  resolving dependencies through apt, is generally more reliable long-term
  within the same distro family.
- **No standardized copyright/changelog file** like the Debian format:
  license traceability is less "system-integrated".

In short: choose the AppImage if you want to **try the app without
installing it**, use it on a **non-Debian-based distribution**, or carry it
across multiple machines; choose the `.deb` if you want **full system
integration** with updates managed by apt.

---

## 1. Target system requirements

The AppImage is meant to run as-is, with nothing to install. You only need:

- A Linux desktop, **x86_64** or **aarch64** (the architecture is in the file name).
- **FUSE** available, for automatic mounting of the image:
  - Recent Debian/Ubuntu: `sudo apt install libfuse2t64` (or `libfuse2` on
    older releases).
  - Fedora: `sudo dnf install fuse-libs`.
  - openSUSE: `sudo zypper install libfuse2`.
  - If you can't install FUSE, see [8. Running without
    FUSE](#8-running-without-fuse).

No Python, no wxPython, no application libraries needed: they're all inside
the image.

---

## 2. Installation

An AppImage isn't "installed" in the classic sense — it's a single
executable file. "Installing" it simply means:

```bash
# 1. Make it executable
chmod +x SongpressPlusPlus-*.AppImage

# 2. (Optional but recommended) move it somewhere stable
mkdir -p ~/Applications
mv SongpressPlusPlus-*.AppImage ~/Applications/
```

From here you can already launch it by double-clicking it in your file
manager, or from a terminal:

```bash
~/Applications/SongpressPlusPlus-*.AppImage
```

### 2a. Desktop integration (icon, menu entry, file type)

By default the AppImage **won't show up in the application menu** until you
integrate it. The easiest way is
**[AppImageLauncher](https://github.com/TheAssassin/AppImageLauncher)**,
which intercepts the first run and offers to integrate it automatically
(icon, menu entry, file association):

```bash
# Debian/Ubuntu — the project's official PPA:
# https://launchpad.net/~appimagelauncher-team/+archive/ubuntu/stable
sudo add-apt-repository ppa:appimagelauncher-team/stable
sudo apt update
sudo apt install appimagelauncher
```

For Fedora/openSUSE/Arch and other distributions, the project publishes
ready-made packages on the
**[AppImageLauncher releases page](https://github.com/TheAssassin/AppImageLauncher/releases)**.

Alternatively, manual integration (works everywhere, no external package):

```bash
APPIMG=~/Applications/SongpressPlusPlus-*.AppImage

# Icon
mkdir -p ~/.local/share/icons/hicolor/256x256/apps
"$APPIMG" --appimage-extract 'usr/share/icons/hicolor/256x256/apps/*.png'
cp squashfs-root/usr/share/icons/hicolor/256x256/apps/*.png \
   ~/.local/share/icons/hicolor/256x256/apps/songpressplusplus.png
rm -rf squashfs-root

# Menu entry
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/songpressplusplus.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=Songpress++
Comment=Generates high-quality songbooks in PDF and PPTX
Exec=$APPIMG %f
Icon=songpressplusplus
Terminal=false
Categories=Office;Publishing;Education;
MimeType=text/x-chordpro;
DESKTOP

update-desktop-database ~/.local/share/applications 2>/dev/null || true
gtk-update-icon-cache -qf ~/.local/share/icons/hicolor 2>/dev/null || true
```

After this step, Songpress++ shows up in the application menu with its icon,
and `.crd`/`.cho`/`.chordpro`/`.chopro`/`.pro`/`.sng` files can be associated
with it from the file manager (right-click → Open with).

> ℹ️ The `.desktop` file above follows the
> **[Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/)**
> from freedesktop.org — the same standard used by the `.deb`. If you want
> to further customize the menu entry (translations, extra actions, etc.),
> that's the reference to consult.

---

## 3. Updating

A new AppImage simply **replaces** the old file:

```bash
mv SongpressPlusPlus-<new_version>-x86_64.AppImage \
   ~/Applications/SongpressPlusPlus-*.AppImage
chmod +x ~/Applications/SongpressPlusPlus-*.AppImage
```

If you had integrated the icon/menu entry manually (§2a) and the file
**path doesn't change**, nothing else needs updating — the `.desktop` file
already points to the right file. If you change the name/path, update the
`Exec=` line in the `.desktop` file.

User data (songs, custom templates, preferences) lives in `~/.Songpress++`,
**outside** the AppImage: it survives any update or removal of the
`.AppImage` file.

---

## 4. Uninstallation

Since the AppImage doesn't touch the system, uninstalling it is simple:

```bash
# 1. Remove the executable file
rm ~/Applications/SongpressPlusPlus-*.AppImage

# 2. If you manually integrated icon/menu entry (§2a), remove them too
rm -f ~/.local/share/applications/songpressplusplus.desktop
rm -f ~/.local/share/icons/hicolor/256x256/apps/songpressplusplus.png
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```

If you used **AppImageLauncher**, first un-integrate the app from its
context menu (right-click the icon → *Remove integration* / *Uninstall
AppImage*), or run:

```bash
~/.local/share/applications/appimagekit_*-songpressplusplus.desktop
# or, simpler, from the menu: right-click the icon → Uninstall AppImage
```

### 4a. Removing user data too (optional)

Personal data (songs, templates, preferences) is **not** touched by the
steps above. To delete it:

```bash
rm -rf ~/.Songpress++
```

⚠️ This also deletes any songs/templates you created — back them up first
if you need them.

---

## 5. Verifying the downloaded file's integrity (optional)

If you downloaded the AppImage from a GitHub release and want to verify its
integrity:

```bash
sha256sum SongpressPlusPlus-*.AppImage
```

Compare the output with the checksum published on the release page.

---

## 6. Debugging and diagnostics

To see all GTK/wx messages without the filter applied by the wrapper (see
`AppRun` in `build_appimage.sh`):

```bash
SONGPRESS_VERBOSE=1 ~/Applications/SongpressPlusPlus-*.AppImage
```

To extract the image's contents without running it (useful to inspect what's
inside):

```bash
./SongpressPlusPlus-*.AppImage --appimage-extract
ls squashfs-root/
```

---

## 7. Spell checker (dictionaries)

The AppImage bundles the `pyenchant` Python binding and the system
`libenchant` library, but **not** the dictionaries themselves
(`hunspell-it`, `hunspell-en-us`, etc.), which remain whatever is already
installed on the system. To get them:

```bash
# Debian/Ubuntu
sudo apt install hunspell-it hunspell-en-us

# Fedora
sudo dnf install hunspell-it hunspell-en-US

# openSUSE
sudo zypper install hunspell-it hunspell-en_US
```

Alternatively, Songpress++ lets you download dictionaries from its own menu:
**Spelling options → Install dictionaries...**.

---

## 8. Running without FUSE

If the system has no FUSE (e.g. some containers or sandboxes), the AppImage
can still run by extracting itself:

```bash
export APPIMAGE_EXTRACT_AND_RUN=1
~/Applications/SongpressPlusPlus-*.AppImage
```

Slower to start (it has to extract the image each time), but doesn't
require FUSE.

---

## 9. FAQ

**Can the AppImage and the `.deb` package be installed together?**
Yes. They don't share system files; they only share the user data folder
`~/.Songpress++`, so they see the same songs/templates.

**Do I need root to use it?**
No, never. All installation/uninstallation happens entirely in user space.

**Why does the app start from a terminal but has no menu icon?**
Because you haven't done the integration described in §2a yet. It's an
optional step — the app still works via double-click or the command line.

**"FUSE error" on startup.**
Install FUSE (§1) or use the no-FUSE mode (§8).
