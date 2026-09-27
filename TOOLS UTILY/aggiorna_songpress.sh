#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
#
# aggiorna_songpress.sh
# Copyright (C) 2026 Denisov21
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# ---------------------------------------------------------------------
# Aggiorna un file di Songpress++ con quello scaricato in ~/Scaricati,
# creando prima una copia di sicurezza (.bak).

# chmod +x aggiorna_songpress.sh
# ./aggiorna_songpress.sh

DEST="/usr/lib/python3/dist-packages/songpressplusplus"
SRC_DIR="$HOME/Scaricati"

read -rp "Nome del file da aggiornare (es. MyPreferencesDialog.py): " FILE

# Nessun nome inserito
if [ -z "$FILE" ]; then
    echo "❌ Errore: nessun nome inserito"
    exit 1
fi

# Il file scaricato deve esistere
if [ ! -f "$SRC_DIR/$FILE" ]; then
    echo "❌ Errore: $SRC_DIR/$FILE non trovato"
    exit 1
fi

cd "$DEST" || { echo "❌ Errore: cartella $DEST non trovata"; exit 1; }

# Copia di sicurezza (solo se il file esiste già)
if [ -f "$FILE" ]; then
    sudo cp "$FILE" "$FILE.bak" \
        && echo "✅ Copia di sicurezza creata: $FILE.bak" \
        || { echo "❌ Errore: backup NON creato, aggiornamento annullato"; exit 1; }
else
    echo "ℹ️  $FILE non esiste ancora in $DEST: nessun backup necessario"
fi

# Copia del nuovo file
sudo cp "$SRC_DIR/$FILE" . \
    && echo "✅ Nuovo $FILE copiato" \
    || { echo "❌ Errore: copia NON riuscita"; exit 1; }

# Verifica: il file installato deve essere identico a quello scaricato
if cmp -s "$SRC_DIR/$FILE" "$DEST/$FILE"; then
    echo "🎉 Versione nuova installata: riavvia Songpress++"
else
    echo "❌ Errore: il file installato non corrisponde a quello scaricato"
    exit 1
fi
