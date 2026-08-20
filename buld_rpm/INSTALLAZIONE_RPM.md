# Songpress++ — Creazione e installazione del pacchetto RPM

Guida rapida per costruire il pacchetto `.rpm` con `build_rpm.sh` e installarlo su
**Fedora/RHEL** o **openSUSE/SLE**.

---

## 1. Prerequisiti (sistema di build)

| Componente | Fedora / RHEL | openSUSE / SLE |
|---|---|---|
| Strumenti RPM | `sudo dnf install rpm-build` | `sudo zypper install rpm-build` |
| Python ≥ 3.12 + pip | `sudo dnf install python3 python3-pip` | `sudo zypper install python3 python3-pip` |
| ImageMagick *(opzionale, per l'icona da `.ico`)* | `sudo dnf install ImageMagick` | `sudo zypper install ImageMagick` |

> **Serve la rete.** Durante il build `pip` scarica da PyPI ciò che serve a
> costruire la wheel (hatchling e dipendenze di build).

---

## 2. Costruzione del pacchetto

Dalla cartella del progetto (quella con `pyproject.toml` e `build_rpm.sh`):

```bash
chmod +x build_rpm.sh
./build_rpm.sh
```

Lo script **rileva da solo** la distribuzione (`Fedora` o `openSUSE`) e sceglie i
nomi corretti dei pacchetti di dipendenza. Al termine il pacchetto si trova in:

```
build_rpm/songpressplusplus-<versione>-1.noarch.rpm
```

### Riconoscimento della distribuzione

Il rilevamento legge i campi `ID` e `ID_LIKE` di `/etc/os-release` e classifica
la macchina in una delle due famiglie:

| Rilevato | `ID` / `ID_LIKE` tipici | Profilo scelto |
|---|---|---|
| **Fedora** | `fedora`, `rhel`, `centos`, `rocky`, `almalinux` | nomi Fedora/RHEL |
| **openSUSE** | `opensuse-leap`, `opensuse-tumbleweed`, `sles`, `suse` | nomi openSUSE/SLE |
| *sconosciuto* | qualsiasi altro (es. `debian`) | avviso + ripiego su Fedora |

All'avvio lo script stampa la famiglia riconosciuta, ad esempio:

```
✔ Famiglia distribuzione rilevata: fedora
```

Per vedere in anticipo cosa verrà rilevato sulla tua macchina:

```bash
. /etc/os-release && echo "ID=$ID  ID_LIKE=$ID_LIKE"
```

Se il rilevamento sbaglia o la distro non è riconosciuta, **forza** la famiglia
con la variabile `SPP_DISTRO`:

```bash
SPP_DISTRO=suse   ./build_rpm.sh     # forza il profilo openSUSE
SPP_DISTRO=fedora ./build_rpm.sh     # forza il profilo Fedora
```

### Opzioni utili

| Opzione | Effetto |
|---|---|
| `-y`, `--yes` | Salta la conferma iniziale (utile in CI / script automatici). |
| `--check-deps` | Verifica i nomi delle dipendenze contro il gestore pacchetti locale **prima** di costruire (non bloccante). Consigliato al primo build su openSUSE. |
| `SPP_DISTRO=fedora\|suse` | Forza la famiglia di distro, ignorando il rilevamento automatico. |
| `SPP_BUILD_LANG=it\|en` | Forza la lingua dei messaggi di build. |

Esempi:

```bash
# Verifica i nomi delle dipendenze, poi costruisci
./build_rpm.sh --check-deps

# Forza il profilo openSUSE e salta la conferma
SPP_DISTRO=suse ./build_rpm.sh -y
```

> **openSUSE:** i nomi `python3-wxPython` e `python3-pyenchant` possono variare
> tra Leap e Tumbleweed. Se `--check-deps` li segnala come *NON trovati*,
> verificali con `zypper se -s <nome>` e correggili nel blocco `DISTRO = suse`
> dello script.

---

## 3. Installazione

Usa il gestore pacchetti della tua distro: risolve **da solo** le dipendenze di
sistema.

**Fedora / RHEL:**

```bash
sudo dnf install ./build_rpm/songpressplusplus-*.noarch.rpm
```

**openSUSE / SLE:**

```bash
sudo zypper install ./build_rpm/songpressplusplus-*.noarch.rpm
```

**Con `rpm` diretto** *(NON risolve le dipendenze — sconsigliato):*

```bash
sudo rpm -i ./build_rpm/songpressplusplus-*.noarch.rpm
```

> **Serve la rete anche all'installazione.** Durante lo scriptlet `%post`, `pip`
> scarica le dipendenze non presenti nei repository della distro
> (`python-pptx`, `pyshortcuts`). Se rispondi *No* al prompt, il pacchetto viene
> installato comunque ma dovrai installarle a mano:
> ```bash
> sudo pip3 install --break-system-packages python-pptx pyshortcuts
> ```

---

## 4. Avvio

Dal menu delle applicazioni (**Songpress++**) oppure da terminale:

```bash
SongpressPlusPlus        # oppure il symlink: songpressplusplus
```

Per vedere tutti i messaggi di log (disattiva il filtro del wrapper):

```bash
SONGPRESS_VERBOSE=1 SongpressPlusPlus
```

---

## 5. Verifica e disinstallazione

```bash
# Cosa è stato installato
rpm -ql songpressplusplus        # elenco file
rpm -qi songpressplusplus        # informazioni pacchetto

# Disinstallazione
sudo dnf remove songpressplusplus       # Fedora/RHEL
sudo zypper remove songpressplusplus    # openSUSE/SLE
```

> Le dipendenze installate via `pip` (`python-pptx`, `pyshortcuts`) **non**
> vengono rimosse automaticamente. Se vuoi eliminarle:
> ```bash
> sudo pip3 uninstall python-pptx pyshortcuts
> ```

---

## Note tecniche

- Il pacchetto è **`noarch`** (puro Python), ma i moduli finiscono in
  `/usr/lib/pythonX.Y/site-packages`: installa l'`.rpm` su una macchina con la
  **stessa minor version di Python** usata per costruirlo.
- Le dipendenze sono dichiarate a mano (`AutoReqProv: no`): niente `Requires`
  generati automaticamente su nomi di moduli Python inesistenti.
- La compilazione dei `.pyc` è disattivata in fase di build (coerente con
  `pip --no-compile`); Python li rigenera all'uso.
