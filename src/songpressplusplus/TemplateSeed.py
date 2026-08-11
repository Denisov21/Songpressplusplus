###############################################################
# Name:         TemplateSeed.py
# Purpose:      Popola la cartella template dell'utente copiandovi, al primo
#               avvio, tutti i template distribuiti con il pacchetto.
# Modified by:  Denisov21
# License:      GNU GPL v2
##############################################################
"""Seeding della cartella template dell'utente.

Perché non lo fa il pacchetto .deb
----------------------------------
La copia *non* può avvenire nel ``postinst`` del pacchetto: ``dpkg`` gira come
``root``, non sa quale sia la home dell'utente (la macchina può averne molti) e
i file che creasse in ``~/.Songpress++/`` sarebbero di proprietà di ``root``,
cioè di nuovo non scrivibili — esattamente il problema da evitare.

La copia avviene quindi al **primo avvio dell'applicazione per quell'utente**:
il risultato è identico (dopo l'installazione l'utente trova tutti i template
nella propria cartella), ma con proprietario e permessi corretti.

Cosa viene copiato
------------------
Tutto il contenuto di ``<pacchetto>/templates/`` dentro
``~/.Songpress++/templates/``:

    templates/               →  ~/.Songpress++/templates/
    ├── fonts/               →  ├── fonts/
    ├── slides/              →  ├── slides/
    ├── songs/               →  ├── songs/
    ├── themes/              →  └── themes/
    └── local_dir/           →  (non copiata come tale: il suo sotto-albero
        └── templates/           templates/ viene fuso nella destinazione)
            ├── songs/
            └── slides/

``local_dir/`` è lo *scheletro* storico della cartella dati: il suo contenuto
``local_dir/templates/*`` viene fuso nella destinazione, ma la cartella
``local_dir`` in sé non viene ricreata nella home dell'utente (sarebbe una
duplicazione priva di senso).

Garanzie
--------
* **Non sovrascrive mai** un file già presente nella cartella dell'utente: le
  sue personalizzazioni sono intoccabili.
* **Idempotente**: un file marcatore (``.seeded``) evita di ricopiare a ogni
  avvio i file che l'utente ha volutamente cancellato.
* **Non solleva mai eccezioni** verso il chiamante: un problema di copia non
  deve impedire l'avvio dell'applicazione.
"""

import os
import shutil

# Sottocartelle di templates/ che devono comunque esistere nella cartella
# dell'utente, anche se il pacchetto non le contiene.
TEMPLATE_SUBDIRS = ('fonts', 'slides', 'songs', 'themes')

# Nome del marcatore scritto nella cartella dell'utente dopo il primo seeding.
_MARKER = '.seeded'

# Cartella del pacchetto che NON va ricreata nella home: è lo scheletro, il suo
# contenuto viene fuso (vedi _merge_local_dir).
_SKELETON = 'local_dir'


def _copy_tree_no_overwrite(src, dst):
    """Copia ricorsivamente src dentro dst senza sovrascrivere nulla.

    Restituisce il numero di file effettivamente copiati.
    """
    copied = 0
    if not os.path.isdir(src):
        return 0
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        s = os.path.join(src, name)
        d = os.path.join(dst, name)
        if os.path.isdir(s):
            copied += _copy_tree_no_overwrite(s, d)
        elif not os.path.exists(d):
            try:
                shutil.copy2(s, d)
                # copy2 preserva anche i permessi della sorgente: nel .deb i
                # file sono 0644 di root, quindi dopo la copia sono di proprietà
                # dell'utente ma potrebbero risultare non scrivibili. Forziamo
                # il bit di scrittura per l'utente.
                os.chmod(d, os.stat(d).st_mode | 0o200)
                copied += 1
            except OSError:
                pass  # un singolo file illeggibile non deve bloccare il resto
    return copied


def _merge_skeleton(pkg_templates, user_templates):
    """Fonde <pacchetto>/templates/local_dir/templates/* nella cartella utente."""
    skel = os.path.join(pkg_templates, _SKELETON, 'templates')
    if os.path.isdir(skel):
        return _copy_tree_no_overwrite(skel, user_templates)
    return 0


def seed_user_templates(pkg_templates, user_templates, force=False):
    """Popola `user_templates` con i template distribuiti in `pkg_templates`.

    :param pkg_templates:  <pacchetto>/templates  (sola lettura con il .deb)
    :param user_templates: ~/.Songpress++/templates  (scrivibile)
    :param force: ricopia anche se il marcatore è già presente (i file esistenti
                  restano comunque intoccati).
    :return: numero di file copiati (0 se non c'era nulla da fare).

    Non solleva eccezioni: in caso di errore restituisce 0.
    """
    try:
        if not user_templates:
            return 0

        user_templates = os.path.normpath(user_templates)
        pkg_templates = os.path.normpath(pkg_templates or '')

        # Modalità portable / venv / albero sorgenti: le due radici coincidono,
        # non c'è nulla da copiare (e copiare su sé stessi sarebbe un disastro).
        if pkg_templates and pkg_templates == user_templates:
            return 0

        os.makedirs(user_templates, exist_ok=True)

        # Le sottocartelle devono esistere sempre: ListLocalGlobalDir() e
        # _PopulateTemplateMenu() ci contano.
        for sub in TEMPLATE_SUBDIRS:
            os.makedirs(os.path.join(user_templates, sub), exist_ok=True)

        marker = os.path.join(user_templates, _MARKER)
        if os.path.exists(marker) and not force:
            return 0

        copied = 0
        if pkg_templates and os.path.isdir(pkg_templates):
            # 1. tutto il contenuto di templates/, tranne lo scheletro local_dir/
            for name in sorted(os.listdir(pkg_templates)):
                if name == _SKELETON:
                    continue
                s = os.path.join(pkg_templates, name)
                d = os.path.join(user_templates, name)
                if os.path.isdir(s):
                    copied += _copy_tree_no_overwrite(s, d)
                elif not os.path.exists(d):
                    try:
                        shutil.copy2(s, d)
                        os.chmod(d, os.stat(d).st_mode | 0o200)
                        copied += 1
                    except OSError:
                        pass

            # 2. lo scheletro local_dir/templates/* fuso nella destinazione
            copied += _merge_skeleton(pkg_templates, user_templates)

        # Marcatore: il seeding è avvenuto, non ripeterlo a ogni avvio (altrimenti
        # i file che l'utente cancella tornerebbero a ripopolarsi da soli).
        try:
            with open(marker, 'w') as f:
                f.write(
                    "Songpress++ ha copiato qui i template distribuiti con "
                    "l'applicazione.\n"
                    "Cancella questo file per farli ricopiare al prossimo avvio "
                    "(i tuoi file non verranno sovrascritti).\n")
        except OSError:
            pass

        return copied
    except Exception:      # pylint: disable=broad-except
        # Il seeding è un'agevolazione, non deve mai impedire l'avvio.
        return 0
