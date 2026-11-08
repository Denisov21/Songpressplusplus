# coding: utf-8

###############################################################
# Name:             Globals.py
# Purpose:     Hold global settings
# Author:         Luca Allulli (webmaster@roma21.it)
# Created:     2009-09-04
# Modified by: Denisov21 (https://github.com/Denisov21/Songpressplusplus)
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

import os.path
import sys
import shutil
from importlib.metadata import version, PackageNotFoundError

import wx


def _candidate_pyproject_paths():
    """Percorsi in cui cercare pyproject.toml, in ordine di priorità.

    - Build congelata (cx_Freeze): il file viene copiato *accanto*
      all'eseguibile tramite include_files. __file__ punta invece dentro lib/
      e risalendo di tre livelli non lo si raggiunge: era la ragione per cui
      la versione ripiegava su "dev" e il nome su "Songpress++".
    - Checkout sorgente / editable install: pyproject.toml sta tre livelli
      sopra questo file (src/<package>/Globals.py → radice del repo).
    """
    paths = []
    if getattr(sys, 'frozen', False):
        paths.append(os.path.join(
            os.path.dirname(os.path.abspath(sys.executable)), 'pyproject.toml'))
    paths.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'pyproject.toml'))
    return paths


def _read_pyproject():
    """Carica il primo pyproject.toml leggibile; None se nessuno disponibile."""
    try:
        import tomllib
    except ModuleNotFoundError:
        return None  # < Python 3.11: tomllib assente (requires-python >=3.12)
    for _toml_path in _candidate_pyproject_paths():
        try:
            with open(_toml_path, 'rb') as f:
                return tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            continue
    return None


def _read_version():
    try:
        return version("songpressplusplus")
    except PackageNotFoundError:
        pass
    data = _read_pyproject()
    if data is not None:
        try:
            return data['project']['version']
        except (KeyError, TypeError):
            pass
    return "dev"


def _read_name():
    try:
        from importlib.metadata import metadata
        return metadata("songpressplusplus")['Name']
    except Exception:
        pass
    data = _read_pyproject()
    if data is not None:
        try:
            return data['project']['name']
        except (KeyError, TypeError):
            pass
    return "Songpress++"


def _windows_install_dir():
    """Cartella di installazione di Songpress++ (Windows), o None.

    Riconosce l'installazione fatta dall'installer NSIS con "uv tool install"
    (venv in <INSTDIR>\\tools\\songpressplusplus = sys.prefix) e la build
    congelata. Non dipende da wx: si può usare anche prima dell'avvio
    dell'applicazione (es. per startup.log).
    """
    if os.name != 'nt':
        return None
    try:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
        parent = os.path.dirname(os.path.abspath(sys.prefix))
        if os.path.basename(parent).lower() == 'tools':
            return os.path.dirname(parent)
    except Exception:      # pylint: disable=broad-except
        return None
    return None


def _windows_install_data_dir():
    """Cartella dati utente sull'unità dove Songpress++ è installato (Windows).

    Così template, configurazione e dizionari seguono la lettera dell'unità di
    installazione (es. D:\\Songpress++\\Songpress) invece di finire sempre in
    C:\\Users\\...\\AppData\\Roaming\\Songpress++.

    Ritorna None se non applicabile o se nessuna cartella è scrivibile: in quel
    caso si usa il percorso standard di wx.StandardPaths.
    """
    inst_dir = _windows_install_dir()
    if not inst_dir:
        return None
    candidates = [os.path.join(inst_dir, 'Songpress')]
    drive = os.path.splitdrive(inst_dir)[0]
    if drive:
        candidates.append(os.path.join(drive + os.sep, 'Songpress'))
    for cand in candidates:
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, '.write_test')
            with open(probe, 'w') as f:
                f.write('x')
            os.remove(probe)
            return cand
        except OSError:
            continue
    return None


def startup_log(msg):
    """Scrive una riga in startup.log (diagnostica di avvio). Non solleva mai.

    Il file sta nella cartella di installazione, cioe' sull'unita' dove e'
    installato Songpress++ (non sempre C:). Se l'installazione non e'
    riconosciuta (esecuzione da sorgente) ripiega sul vecchio percorso
    ~\\AppData\\Local\\Songpress++. Punto unico per tutti i moduli.
    """
    import datetime
    try:
        inst_dir = _windows_install_dir()
        if inst_dir and os.path.isdir(inst_dir):
            log_path = os.path.join(inst_dir, 'startup.log')
        else:
            log_path = os.path.join(
                os.path.expanduser('~'), 'AppData', 'Local', 'Songpress++',
                'startup.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except Exception:      # pylint: disable=broad-except
        pass


def _move_tree(src, dst):
    """Sposta il contenuto di src dentro dst, unendo le cartelle.

    I file già presenti in dst vengono sovrascritti. Ogni file è copiato e poi
    cancellato dall'origine solo se la copia è riuscita; la cartella src viene
    rimossa soltanto se non resta nulla al suo interno, così un errore non fa
    perdere dati. Ritorna True se src è stata spostata per intero.
    """
    ok = True
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target = dst if rel == '.' else os.path.join(dst, rel)
        try:
            os.makedirs(target, exist_ok=True)
        except OSError:
            ok = False
            continue
        for name in files:
            s = os.path.join(root, name)
            try:
                shutil.copy2(s, os.path.join(target, name))
                os.remove(s)
            except OSError:
                ok = False
    if ok:
        try:
            shutil.rmtree(src)
        except OSError:
            ok = False
    return ok


class Globals(object):
    # Subfolders of templates/ that must always exist, both in the package
    # (global root) and in the user data dir (local root). Kept in sync with
    # MyPreferencesDialog._TEMPLATE_SUBDIRS: this is exactly the tree that the
    # "Open templates folder" button reveals to the user.
    #   fonts/      → custom fonts used by preview/export
    #   local_dir/  → skeleton copied into the data dir on first run
    #   slides/     → PowerPoint templates (.pptx)
    #   songs/      → song templates (.crd)
    #   themes/     → editor colour themes (.ini)
    TEMPLATE_SUBDIRS = ('fonts', 'local_dir', 'slides', 'songs', 'themes')

    # Subfolders that must exist in the *user data dir*. Same list minus
    # local_dir/: that folder is the skeleton shipped inside the package, and
    # re-creating an empty copy of it in the user's home would be a pointless
    # duplicate. Its contents (local_dir/templates/*) are merged straight into
    # the user's templates/ tree by TemplateSeed.seed_user_templates().
    USER_TEMPLATE_SUBDIRS = ('fonts', 'slides', 'songs', 'themes')

    def __init__(self):
        object.__init__(self)
        if getattr(sys, 'frozen', False):
            # Build congelata (cx_Freeze): le risorse (xrc/, img/, templates/,
            # locale/) vengono copiate da include_files nella cartella
            # dell'eseguibile, non dentro lib/songpressPlusPlus/. Usare la dir
            # dell'exe come radice risorse; __file__ punterebbe invece dentro
            # lib/ dove xrc/ ecc. non esistono → wxDir::Open fallisce.
            self.path = os.path.dirname(os.path.abspath(sys.executable))
        else:
            current_file = os.path.abspath(__file__)
            self.path = os.path.dirname(current_file)
        self.data_path = None

    def InitDataPath(self):
        sp = wx.StandardPaths.Get()
        portable_config = os.path.join(self.path, 'config.ini')
        if os.path.isfile(portable_config):
            # Monkey-patch StandardPaths instance so that portable config.ini is used
            def my_get(*args, **kwargs):
                return self.path
            sp.GetUserDataDir = my_get
        else:
            # Windows: dati sull'unità di installazione (non sempre C:).
            inst_data = _windows_install_data_dir()
            if inst_data:
                legacy = sp.GetUserDataDir()      # %APPDATA%\Songpress++
                marker = os.path.join(inst_data, '.migrated_from_appdata')
                if not os.path.isfile(marker):
                    # Migrazione una tantum: i file vengono SPOSTATI (non
                    # copiati) e i file personalizzati dell'utente prevalgono
                    # su quelli copiati dall'installer.
                    try:
                        if (legacy and os.path.isdir(legacy) and
                                os.path.realpath(legacy) != os.path.realpath(inst_data)):
                            _move_tree(legacy, inst_data)
                    except Exception:      # pylint: disable=broad-except
                        pass
                    try:
                        open(marker, 'w').close()
                    except OSError:
                        pass

                def inst_get(*args, **kwargs):
                    return inst_data
                sp.GetUserDataDir = inst_get

        self.data_path = sp.GetUserDataDir()
        old_config = None
        if os.path.isfile(self.data_path):
            old_config = self.data_path + ".orig"
            shutil.move(self.data_path, old_config)
        if not os.path.exists(self.data_path):
            local_dir_src = os.path.join(self.path, 'templates', 'local_dir')
            if os.path.isdir(local_dir_src):
                shutil.copytree(local_dir_src, self.data_path)
            else:
                os.makedirs(self.data_path, exist_ok=True)
        if old_config is not None:
            # Preserve old config file, but don't use it
            shutil.move(old_config, os.path.join(self.data_path, "config.ini.orig"))

        # Ensure the user data dir always exposes every template subfolder, even
        # if templates/local_dir was incomplete or not shipped at all. Without
        # them ListLocalGlobalDir('templates/slides') would find nothing and the
        # "Open templates folder" button would show an incomplete tree.
        for sub in self.USER_TEMPLATE_SUBDIRS:
            try:
                os.makedirs(os.path.join(self.data_path, 'templates', sub),
                            exist_ok=True)
            except OSError:
                pass  # read-only data dir: features degrade gracefully

        self.SeedUserTemplates()

    def SeedUserTemplates(self, force=False):
        """Copy the templates shipped with the package into the user data dir.

        With a system-wide install (.deb) the package lives in
        /usr/local/lib/pythonX.Y/dist-packages/songpressplusplus/ and belongs to
        root: the user can read templates/ but cannot create anything there.
        The user data dir, on the other hand, is writable but starts out empty.
        Seeding merges the two: after the first run ~/.Songpress++/templates/ is
        both complete *and* writable.

        This cannot be done from the .deb postinst: dpkg runs as root, before any
        user session exists, so it neither knows which home to use (a machine may
        have many users) nor could it create files owned by anyone but root —
        which is exactly the problem we are trying to avoid.

        Never overwrites an existing user file; idempotent (a .seeded marker
        prevents deleted files from silently reappearing on every launch);
        never raises.
        """
        if not self.data_path:
            return 0
        try:
            from .TemplateSeed import seed_user_templates
            return seed_user_templates(
                os.path.join(self.path, 'templates'),
                os.path.join(self.data_path, 'templates'),
                force=force)
        except Exception:      # pylint: disable=broad-except
            return 0           # seeding is a convenience: never block startup

    def AddPath(self, filename):
        return os.path.join(self.path, filename)

    def ListLocalGlobalDir(self, rel_path):
        """
        List both the local (data) and global (program) versions of a directory.

        I file con lo stesso nome vengono restituiti UNA volta sola: la copia
        *locale* (cartella dati utente) prevale su quella *globale* (pacchetto).
        È il comportamento che i chiamanti si aspettano — cfr.
        SongpressFrame._BuildNewFromTemplateMenu(), che implementava già a mano
        l'identica logica "i file utente sovrascrivono gli omonimi globali".

        Senza questa de-duplicazione ogni template distribuito con il pacchetto e
        poi copiato nella cartella dati utente dal seeding
        (TemplateSeed.seed_user_templates) comparirebbe *due volte* nei selettori
        come il dialogo "Esporta come PowerPoint": è il bug dei template
        duplicati.

        Le cartelle mancanti o illeggibili vengono ignorate silenziosamente: con
        un'installazione di sistema (.deb) la cartella dati può non contenere
        ancora ogni sottocartella e os.listdir() solleverebbe FileNotFoundError.

        :param rel_path: relative path
        :return: lista di percorsi assoluti, uno per nome file distinto, ordinata
                 per nome (case-insensitive); a parità di nome vince la copia
                 locale.
        """
        found = {}            # nome_file_lower -> percorso assoluto
        seen_folders = set()  # cartelle già visitate (realpath)
        # Prima la globale, poi la locale: iterando in quest'ordine la copia
        # locale, assegnata per ultima, sovrascrive quella globale per ogni nome
        # file condiviso.
        for root in (self.path, self.data_path):
            if not root:
                continue  # data_path not initialised yet
            folder = os.path.join(root, rel_path)
            if not os.path.isdir(folder):
                continue
            # In modalità portable self.data_path == self.path, quindi le due
            # root risolvono alla stessa cartella: senza questo controllo la
            # scorreremmo due volte inutilmente (la de-duplicazione per nome la
            # renderebbe comunque innocua).
            real = os.path.realpath(folder)
            if real in seen_folders:
                continue
            seen_folders.add(real)
            try:
                for f in sorted(os.listdir(folder)):
                    found[f.lower()] = os.path.join(folder, f)
            except OSError:
                pass  # unreadable directory: skip it
        return [found[k] for k in sorted(found)]

    languages = {
        'en': "English",
        'it': "Italiano",
    }

    translators = {
        'en': "Luca Allulli, Denisov21",
        'it': "Luca Allulli, Denisov21",
    }

    default_language = 'en'

    PROG_NAME = _read_name()
    VERSION = _read_version()
    BUG_REPORT_ADDRESS = ''
    YEAR = '2026'

glb = Globals()
