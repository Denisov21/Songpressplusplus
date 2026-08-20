# Songpress++ — Building and installing the RPM package

Quick guide to build the `.rpm` package with `build_rpm.sh` and install it on
**Fedora/RHEL** or **openSUSE/SLE**.

---

## 1. Prerequisites (build system)

| Component | Fedora / RHEL | openSUSE / SLE |
|---|---|---|
| RPM tooling | `sudo dnf install rpm-build` | `sudo zypper install rpm-build` |
| Python ≥ 3.12 + pip | `sudo dnf install python3 python3-pip` | `sudo zypper install python3 python3-pip` |
| ImageMagick *(optional, for the icon from `.ico`)* | `sudo dnf install ImageMagick` | `sudo zypper install ImageMagick` |

> **Network required.** During the build, `pip` downloads from PyPI what it needs
> to build the wheel (hatchling and the build dependencies).

---

## 2. Building the package

From the project folder (the one with `pyproject.toml` and `build_rpm.sh`):

```bash
chmod +x build_rpm.sh
./build_rpm.sh
```

The script **auto-detects** the distribution (`Fedora` or `openSUSE`) and picks
the correct dependency package names. When finished, the package is at:

```
build_rpm/songpressplusplus-<version>-1.noarch.rpm
```

### Distribution detection

Detection reads the `ID` and `ID_LIKE` fields of `/etc/os-release` and classifies
the machine into one of the two families:

| Detected | Typical `ID` / `ID_LIKE` | Profile chosen |
|---|---|---|
| **Fedora** | `fedora`, `rhel`, `centos`, `rocky`, `almalinux` | Fedora/RHEL names |
| **openSUSE** | `opensuse-leap`, `opensuse-tumbleweed`, `sles`, `suse` | openSUSE/SLE names |
| *unknown* | anything else (e.g. `debian`) | warning + fall back to Fedora |

On startup the script prints the detected family, for example:

```
✔ Detected distribution family: fedora
```

To see in advance what will be detected on your machine:

```bash
. /etc/os-release && echo "ID=$ID  ID_LIKE=$ID_LIKE"
```

If detection is wrong or the distro is not recognised, **force** the family with
the `SPP_DISTRO` variable:

```bash
SPP_DISTRO=suse   ./build_rpm.sh     # force the openSUSE profile
SPP_DISTRO=fedora ./build_rpm.sh     # force the Fedora profile
```

### Useful options

| Option | Effect |
|---|---|
| `-y`, `--yes` | Skip the initial confirmation (useful in CI / automated scripts). |
| `--check-deps` | Verify the dependency names against the local package manager **before** building (non-blocking). Recommended for the first build on openSUSE. |
| `SPP_DISTRO=fedora\|suse` | Force the distro family, ignoring auto-detection. |
| `SPP_BUILD_LANG=it\|en` | Force the language of the build messages. |

Examples:

```bash
# Verify the dependency names, then build
./build_rpm.sh --check-deps

# Force the openSUSE profile and skip the confirmation
SPP_DISTRO=suse ./build_rpm.sh -y
```

> **openSUSE:** the names `python3-wxPython` and `python3-pyenchant` may differ
> between Leap and Tumbleweed. If `--check-deps` reports them as *NOT found*,
> verify them with `zypper se -s <name>` and fix them in the `DISTRO = suse`
> block of the script.

---

## 3. Installation

Use your distro's package manager: it resolves the system dependencies **for you**.

**Fedora / RHEL:**

```bash
sudo dnf install ./build_rpm/songpressplusplus-*.noarch.rpm
```

**openSUSE / SLE:**

```bash
sudo zypper install ./build_rpm/songpressplusplus-*.noarch.rpm
```

**With `rpm` directly** *(does NOT resolve dependencies — not recommended):*

```bash
sudo rpm -i ./build_rpm/songpressplusplus-*.noarch.rpm
```

> **Network also required at install time.** During the `%post` scriptlet, `pip`
> downloads the dependencies not present in the distro repositories
> (`python-pptx`, `pyshortcuts`). If you answer *No* at the prompt, the package
> is still installed but you will have to install them manually:
> ```bash
> sudo pip3 install --break-system-packages python-pptx pyshortcuts
> ```

---

## 4. Running

From the applications menu (**Songpress++**) or from a terminal:

```bash
SongpressPlusPlus        # or the symlink: songpressplusplus
```

To see all log messages (disables the wrapper filter):

```bash
SONGPRESS_VERBOSE=1 SongpressPlusPlus
```

---

## 5. Inspecting and uninstalling

```bash
# What was installed
rpm -ql songpressplusplus        # file list
rpm -qi songpressplusplus        # package information

# Uninstall
sudo dnf remove songpressplusplus       # Fedora/RHEL
sudo zypper remove songpressplusplus    # openSUSE/SLE
```

> Dependencies installed via `pip` (`python-pptx`, `pyshortcuts`) are **not**
> removed automatically. To remove them:
> ```bash
> sudo pip3 uninstall python-pptx pyshortcuts
> ```

---

## Technical notes

- The package is **`noarch`** (pure Python), but the modules land in
  `/usr/lib/pythonX.Y/site-packages`: install the `.rpm` on a machine with the
  **same Python minor version** used to build it.
- Dependencies are declared by hand (`AutoReqProv: no`): no `Requires`
  auto-generated from non-existent Python module names.
- Byte-compilation of `.pyc` files is disabled at build time (consistent with
  `pip --no-compile`); Python regenerates them at runtime.
