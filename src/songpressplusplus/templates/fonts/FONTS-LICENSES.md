# Licenze dei font opzionali consigliati

Questo documento riguarda i **font opzionali** che SongpressPlusPlus può caricare
automaticamente per ampliare la copertura del piano **SMP** (Supplementary
Multilingual Plane) e dei simboli musicali.

> **Nota importante**
> Questi font **non sono inclusi di default** nell'applicazione. Vengono caricati
> solo se l'utente li aggiunge manualmente alla propria installazione. Di
> conseguenza SongpressPlusPlus, così com'è distribuito (AppImage, `.deb`, ecc.),
> **non ridistribuisce** questi file e non assume gli obblighi di licenza legati
> alla loro ridistribuzione. Gli obblighi ricadono su chi decide effettivamente di
> impacchettare o redistribuire i font.

---

## Riepilogo

| Font | Nome file tipico | Licenza | Titolare del copyright |
|------|------------------|---------|------------------------|
| Bravura | `Bravura.ttf` | SIL Open Font License 1.1 | Steinberg Media Technologies GmbH |
| Noto Music | `NotoMusic.ttf` / `NotoMusicRegular.ttf` | SIL Open Font License 1.1 | The Noto Project Authors / Google Inc. |
| Altri `.ttf` aggiunti dall'utente | qualsiasi | **secondo la licenza del singolo font** | il rispettivo autore |

Tutti i font consigliati e verificati qui sono sotto **SIL Open Font License,
versione 1.1** (in breve *OFL-1.1*), una licenza libera e open source approvata da
OSI, FSF e conforme alle Debian Free Software Guidelines.

---

## Bravura

- **File:** `Bravura.ttf` (ed eventualmente `BravuraText.ttf`)
- **Licenza:** SIL Open Font License, Version 1.1
- **Copyright:** © Steinberg Media Technologies GmbH
- **Sorgente ufficiale:** <https://github.com/steinbergmedia/bravura>
- **Informazioni SMuFL:** <https://www.smufl.org/fonts/>

Bravura è il font di riferimento per la specifica SMuFL (Standard Music Font
Layout). È distribuito sotto SIL OFL: è libero di essere scaricato, usato,
incorporato nei documenti, ridistribuito insieme ad altro software (anche
commerciale) e usato come base per font derivati. Le uniche restrizioni rilevanti
sono che il font non può essere venduto da solo, che un font derivato non può
chiamarsi "Bravura" né contenere tale nome riservato, e che ogni derivato deve
essere rilasciato sotto la stessa licenza OFL.

---

## Noto Music

- **File:** `NotoMusic.ttf` o `NotoMusicRegular.ttf`
- **Licenza:** SIL Open Font License, Version 1.1
- **Copyright:** © The Noto Project Authors (Google Inc.)
- **Sorgente ufficiale:** <https://github.com/notofonts/notofonts.github.io> (progetto Noto)
- **Sito del progetto:** <https://notofonts.github.io/>

Noto Music fa parte della famiglia Noto di Google, pensata per coprire tutti gli
script codificati in Unicode. L'intera famiglia Noto è distribuita sotto SIL
OFL-1.1 (dal 2015; alcune versioni molto precoci, 2013–2015, erano sotto Apache
License 2.0). Valgono le stesse libertà e restrizioni descritte per Bravura.

---

## Altri font `.ttf` aggiunti dall'utente

SongpressPlusPlus caricherà automaticamente qualunque altro `.ttf` presente nella
cartella dei font. **La licenza di questi file è responsabilità di chi li
aggiunge.** Prima di redistribuire un pacchetto che li includa, verifica che la
licenza del singolo font ne consenta l'incorporazione/ridistribuzione (molti font
musicali SMuFL — ad es. Petaluma, Leland, Sebastian — sono sotto OFL-1.1, ma non è
una regola universale: alcuni, come November 2.0, hanno licenza commerciale).

---

## SIL Open Font License 1.1 — punti chiave

Testo completo e FAQ: <https://openfontlicense.org/> (in precedenza
`https://scripts.sil.org/OFL`).

Sintesi (non sostituisce il testo di licenza):

1. **Uso libero.** I font possono essere usati, studiati, modificati e
   ridistribuiti liberamente.
2. **Bundling consentito.** Possono essere impacchettati, incorporati e
   ridistribuiti — anche con software commerciale.
3. **Non vendibili da soli.** Non possono essere venduti come prodotto a sé stante;
   possono però essere inclusi (anche a pagamento) insieme ad altro software.
4. **Nomi riservati (Reserved Font Names).** Un font derivato non può usare il nome
   riservato dell'originale.
5. **Stessa licenza per i derivati.** Le versioni modificate devono essere
   distribuite anch'esse sotto OFL.
6. **Copia della licenza allegata.** Ogni copia del font (originale o modificata)
   deve essere accompagnata dal testo della licenza OFL.
7. **Nessuna garanzia.** Il software è fornito "così com'è", senza garanzie.

### Obbligo pratico in caso di ridistribuzione

Se — e solo se — decidi di **includere** questi font in un pacchetto che
distribuisci, ricordati di:

- inserire il file di licenza `OFL.txt` accanto a ciascun font;
- mantenere le note di copyright presenti nei metadati del font;
- non rinominare i font con i loro Reserved Font Names se li modifichi.

Se invece i font restano **aggiunti localmente dall'utente** (comportamento
predefinito), non hai obblighi di ridistribuzione da assolvere.

---

*Documento a scopo informativo; non costituisce consulenza legale. In caso di
dubbi sulla ridistribuzione, fai riferimento al testo integrale della SIL Open
Font License 1.1 e ai file di licenza forniti con ciascun font.*
