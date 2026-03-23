# Quick Reference — Songpress++

This guide describes all ChordPro commands supported by Songpress++ and the main editor features.

> **Legend** — The **Std** column indicates whether the directive is part of the official ChordPro standard (✅) or is specific to Songpress++ (🔧).

---

## ChordPro Format — Basic Concepts

A ChordPro file is a plain text file in which **chords** are embedded directly in the song lyrics, enclosed in square brackets `[chord]`. Metadata and structure **directives** are enclosed in curly braces `{directive:value}`.

```chordpro
{title: Amazing Grace}
{artist: Traditional}
{key: G}

[G]Amazing [G7]grace, how [C]sweet the [G]sound
```

---

## Song Metadata

| Directive | Alias | Std | Description |
| --- | --- | --- | --- |
| `{title:Title}` | `{t:Title}` | ✅ | Song title |
| `{subtitle:Text}` | `{st:...}` | ✅ | Subtitle or secondary artist |
| `{artist:Name}` | | ✅ | Artist / performer (rendered as subtitle) |
| `{composer:Name}` | | ✅ | Composer (rendered as subtitle) |
| `{album:Title}` | | ✅ | Album title (rendered as «Album: …») |
| `{year:Year}` | | ✅ | Year of publication (rendered as subtitle) |
| `{copyright:Text}` | | ✅ | Copyright notice (rendered as «© …») |
| `{key:Key}` | | ✅ | Key (e.g. `Am`, `C`, `G`, `F#m`); rendered as «Key: …» when display is active |
| `{capo:N}` | | ✅ | Capo at fret N (e.g. `{capo:2}`); rendered as «Capo: N» |
| `{tempo:BPM}` | | ✅ | Tempo in BPM with **quarter note** icon (e.g. `{tempo:120}`) |
| `{tempo_m:BPM}` | | 🔧 | Tempo with **half note** icon |
| `{tempo_s:BPM}` | | 🔧 | Tempo with **quarter note** icon |
| `{tempo_sp:BPM}` | | 🔧 | Tempo with **dotted quarter note** icon |
| `{tempo_c:BPM}` | | 🔧 | Tempo with **eighth note** icon |
| `{tempo_cp:BPM}` | | 🔧 | Tempo with **dotted eighth note** icon |
| `{time:N/M}` | | ✅ | Time signature (e.g. `{time:4/4}`, `{time:3/4}`); rendered as a graphic time signature symbol |

> **Note on tempo** — The `{tempo*}` directives have three display modes, configurable in the preferences: note icon + value (e.g. `♩ = 120`), text `BPM: 120`, or plain text `Tempo: 120`. Setting the mode to *hidden* (`-1`) treats the value as a pure metadata field that does not appear in the preview or in print.

---

## Song Structure

### Text Blocks

| Directive | Std | Description |
| --- | --- | --- |
| `{start_of_verse}` / `{end_of_verse}` | ✅ | Unnumbered verse, no label |
| `{start_verse:Label}` / `{end_verse}` | 🔧 | Unnumbered verse with optional label |
| `{start_verse_num}` / `{end_verse_num}` | 🔧 | Automatically numbered verse |
| `{verse:Label}` | ✅ | Opens a verse with a custom label (e.g. `{verse:1}`) |
| `{start_of_chorus}` / `{end_of_chorus}` | ✅ | Chorus |
| `{soc}` / `{eoc}` | ✅ | Shorthand for `start_of_chorus` / `end_of_chorus` |
| `{soc:Label}` | ✅ | Chorus with custom label |
| `{start_chorus:Label}` / `{end_chorus}` | 🔧 | Alternative chorus form (optional label) |
| `{start_bridge:Label}` / `{end_bridge}` | 🔧 | Bridge with optional label; defaults to «Bridge» if omitted |
| `{start_chord:Label}` / `{end_chord}` | 🔧 | Intro/chord block; defaults to «Intro» if label is omitted |
| `{new_song}` | 🔧 | Starts a new song in the same document: resets verse and chorus counters so numbering restarts from 1 |

> **Note on `{start_of_bridge}`** — This form (with `of_`) is not handled by the renderer; use `{start_bridge}` / `{end_bridge}` instead.

### Page and Column Breaks

| Directive | Alias | Std | Description |
| --- | --- | --- | --- |
| `{new_page}` | `{np}` | ✅ | Explicit page break for printing |
| `{column_break}` | `{colb}` | ✅ | Column break (2-column layout) |

---

## Chords and Inline Formatting

### Chords

Chords are inserted in the text using square brackets, immediately before the syllable they belong to:

```chordpro
[Am]Nel [F]blu [C]dipinto di [G]blu
```

### Local Fonts and Colors

These directives change the font for the following section; used without an argument they restore the default value.

| Opening directive | Closing directive | Std | Description |
| --- | --- | --- | --- |
| `{textfont:Name}` | `{textfont}` | ✅ | Text font family |
| `{textsize:Pt}` | `{textsize}` | ✅ | Text size in pt (also accepts percentage, e.g. `{textsize:80%}`) |
| `{textcolour:#HEX}` | `{textcolour}` | ✅ | Text color in `#RRGGBB` format |
| `{chordfont:Name}` | `{chordfont}` | ✅ | Chord font family |
| `{chordsize:Pt}` | `{chordsize}` | ✅ | Chord size in pt (also accepts percentage) |
| `{chordcolour:#HEX}` | `{chordcolour}` | ✅ | Chord color in `#RRGGBB` format |

### Spacing

| Directive | Std | Description |
| --- | --- | --- |
| `{linespacing:N}` | 🔧 | Line spacing in points (e.g. `{linespacing:1}`); restores default when used without argument |
| `{chordtopspacing:N}` | 🔧 | Space above chords in points (e.g. `{chordtopspacing:0}` to remove it); restores default when used without argument |
| `{row}` or `{r}` | 🔧 | Inserts half a line of vertical whitespace (spacer) |

---

## Comments and Editorial Notes

| Form | Alias | Std | Description |
| --- | --- | --- | --- |
| `{comment:Text}` | `{c:Text}` | ✅ | Comment visible in the preview, automatically enclosed in parentheses |
| `{comment_italic:Text}` | `{ci:Text}` | ✅ | Like `{comment}`, but rendered in italics |
| `{comment_box:Text}` | `{cb:Text}` | ✅ | Comment in a box |
| `# Text` | | ✅ | Line comment (preceded by `#`): treated as a blank line, does not appear in preview or print |

---

## Chord Diagrams, Keyboard and Images

| Directive | Std | Description |
| --- | --- | --- |
| `{define: C base-fret 1 frets X 3 2 0 1 0}` | ✅ | Defines a guitar chord diagram |
| `{taste:Chord}` | 🔧 | Shows highlighted keys on the piano keyboard (klavier) — e.g. `{taste:Am}` |
| `{image: filename}` | ✅ | Inserts an image (PNG, JPG, GIF, BMP, TIFF) into the song |

The keyboard (klavier) displays the keys corresponding to the specified chord, highlighted with the color set in preferences.

### Image Directive

The `{image:}` directive embeds a raster image at the point where it appears in the song. The file path can be relative to the song file's location or absolute.

| Option | Std | Description |
| --- | --- | --- |
| `width=N` | ✅ | Width in typographic points (1/72 inch), or percentage e.g. `width=50%` |
| `height=N` | ✅ | Height in typographic points, or percentage |
| `scale=N%` | ✅ | Scale factor, e.g. `scale=50%` (cannot be combined with width/height) |
| `align=left` | ✅ | Left alignment |
| `align=center` | ✅ | Center alignment (default) |
| `align=right` | ✅ | Right alignment |
| `border` | ✅ | Draws a 1pt border around the image |
| `border=N` | ✅ | Draws a border of N typographic points |

**Supported formats:**

| Format | Extensions |
| --- | --- |
| PNG | `.png` |
| JPEG | `.jpg`, `.jpeg` |
| GIF | `.gif` |
| BMP | `.bmp` |
| TIFF | `.tiff`, `.tif` |

**Examples:**
```chordpro
{image: logo.png}
{image: logo.png width=200 align=left}
{image: logo.png scale=50% border}
{image: "C:\Users\User\Pictures\photo.jpg" align=center}
```

If the image file is in the same folder as the song file, just the filename is sufficient. Paths containing spaces or backslashes must be enclosed in double quotes.

Images can be inserted via **Insert → Other → Image {image:}**, which opens a dialog to select the file and configure all options, with a real-time preview of the generated directive.

Numeric fields in the dialog use spinner controls:

| Field    | Initial value | Range  | Step | Notes                               |
| -------- | ------------- | ------ | ---- | ----------------------------------- |
| Width    | 0             | 0–9999 | 1    | 0 = not included in the directive   |
| Height   | 0             | 0–9999 | 1    | 0 = not included in the directive   |
| Scale    | 100           | 1–500  | 1    | 100 = not included (it is default)  |
| Border   | 1             | 0–50   | 0.5  | active only when checkbox is ticked |

---

## File Structure — Complete Example

```chordpro
{title: O Sole Mio}
{artist: Eduardo di Capua}
{key: C}
{time: 4/4}
{tempo: 80}
{capo: 0}

{start_verse_num}
[C]Che bella [G7]cosa na jurnata 'e [C]sole
[C]N'aria serena [G7]doppo na tempesta!
{end_verse_num}

{soc:Chorus}
[C]O sole [C7]mio sta [F]'nfronte a [C]te
[G7]O sole, o sole [C]mio
{eoc}

{new_page}

{start_verse_num}
[C]Ma n'atu sole [G7]cchiu bello, oje [C]ne'
{end_verse_num}
```

---

## Editor Features

### Guided Insertion (Insert Menu)

All main directives are accessible via the **Insert** menu, which opens helper dialogs to fill in values. The `|` cursor in InsertWithCaret indicates where the cursor will be positioned after insertion.

### Chord Management

- **Insert chord** — inserts `[|]` with the cursor inside the brackets
- **Move chord right / left** — moves the chord under the cursor one character
- **Remove chords** — deletes all chords from the selection
- **Paste chords** — pastes only the chords (without text) from the copied selection
- **Propagate chords to verses** — copies chords from the first verse to all verses with the same number of lines
- **Propagate chords to choruses** — same for choruses
- **Integrate chords** — converts two separate lines (chords above / text below) into inline ChordPro format

### Transposition and Notation

- **Transpose** — opens the dialog to transpose all chords
- **Simplify chords** — finds the simplest key to play in
- **Change notation** — converts between Anglo-Saxon notation (C D E…) and solfège (Do Re Mi…)
- **Normalize chords** — standardizes chord spelling (e.g. `Hm` → `Bm`)
- **Convert Tab → ChordPro** — automatically converts tab format (chords above text) to inline ChordPro

### Formatting and Structure

- **Song font** — opens the dialog to set the global font
- **Text font** — inserts `{textfont}` / `{textsize}` / `{textcolour}` directives for the current passage
- **Chord font** — inserts `{chordfont}` / `{chordsize}` / `{chordcolour}` directives
- **Verse labels** — shows/hides verse labels in the preview
- **Chords above / below** — positions chords above or below the text
- **Show chords** — three modes: none / first verse only / entire song
- **Page / column break lines** — shows/hides guide lines in the preview

### Text Cleanup

- **Remove extra blank lines** — deletes double blank lines
- **Normalize multiple spaces** — reduces multiple spaces to a single space

### Syntax Check

- **Check syntax** — analyzes the text and reports unrecognized or malformed directives, with the ability to navigate directly to the error

---

## Display Preferences

The following controls are found in the **Formatting** tab of the preferences and affect both preview and print output.

| Field | Default value | Range | Step |
| --- | --- | --- | --- |
| Title underline thickness | 2 | 1–5 | 1 |
| Verse number border thickness | 1 | 1–5 | 1 |

---

## Print and Preview

- **Print preview** — shows the preview with "Print options" and "Page setup" buttons
- **Print** — prints directly (without preview if the option is disabled in preferences)
- **Page setup** — paper size, orientation and margins (in mm)

### Print options

| Option | Description |
| --- | --- |
| Print 2 pages per sheet | Prints two logical pages side by side on a single physical sheet |
| Columns per page (1 / 2) | Distributes the text across one or two columns |
| Shrink and fit to page | Reduces the content to fit on a single page |
| Shrink to fit current page | Further reduces content to avoid it being cut off at the bottom |
| Do not replicate (leave right half blank) | With 2 pages/sheet: leaves the second half empty instead of replicating |
| Remove blank pages | Removes empty pages from the print output |


The `{new_page}` directive in the text forces a new logical page during printing. With the 2-column layout, `{column_break}` forces a jump to the next column.

---

## Export

| Format | Notes |
| --- | --- |
| SVG | Vector, scalable |
| EMF | Windows vector format |
| PNG | Raster image |
| HTML | Web page with colored chords |
| Tab | Plain text format with chords above |
| PDF | PDF document |
| PowerPoint (.pptx) | Presentation |
| Songbook | Song collection |
| Copy as image | Copies to clipboard as vector graphic |
| Copy text only | Copies text without chords |

---

## Supported Import File Formats

| Extension | Description |
| --- | --- |
| `.crd` | ChordPro (main extension) |
| `.cho` | ChordPro |
| `.chordpro` | ChordPro |
| `.chopro` | ChordPro |
| `.pro` | ChordPro |
| `.tab` | Tab format (chords above text) |

---

## License and Credits

**Songpress++** is a derivative work of **Songpress**, originally developed by Luca Allulli / [Skeed](https://www.skeed.it/songpress) — copyright © 2009–2026 Luca Allulli (Skeed).

The modifications in Songpress++ are copyright © Denisov21.

Songpress++ is distributed under the terms of the **GNU General Public License version 2** (GPL v2), the same license as the original project. The program is free software: you can redistribute it and/or modify it under the terms of the GPL v2 as published by the Free Software Foundation. The program is distributed in the hope that it will be useful, but **without any warranty**, not even the implied warranty of merchantability or fitness for a particular purpose.

The full license text is available at: <https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>

### Third-Party Components

Songpress (and consequently Songpress++) makes use of the following third-party software components:

| Component | License | Reference |
| --- | --- | --- |
| Python and the Python standard library | Python Software Foundation License | <https://www.python.org> |
| wxPython | wxWindows Library Licence | <https://wxpython.org> |
| Editra (error reporting dialog) | wxWindows Library Licence v3.1 | <https://github.com/cjprecord/editra> |
| uv (Windows installer only) | MIT License — copyright © 2025 Astral Software Inc. | <https://github.com/astral-sh/uv> |
