# Quick Reference — Songpress++

This guide describes all ChordPro directives supported by Songpress++ and the main editor features.

> **Legend** — The **Std** column indicates whether the directive is part of the official ChordPro standard (✅) or is specific to Songpress++ (🔧). The **Menu** column indicates whether the directive can be inserted via an application menu (⌨️) or must be typed manually in the editor (🖊).

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

| Directive | Alias | Std | Menu | Description |
| --- | --- | --- | --- | --- |
| `{title:Title}` | `{t:Title}` | ✅ | ⌨️ | Song title |
| `{subtitle:Text}` | `{st:...}` | ✅ | ⌨️ | Subtitle or secondary artist |
| `{artist:Name}` | | ✅ | 🖊 | Artist / performer (rendered as subtitle) |
| `{composer:Name}` | | ✅ | 🖊 | Composer (rendered as subtitle) |
| `{album:Title}` | | ✅ | 🖊 | Album title (rendered as «Album: …») |
| `{year:Year}` | | ✅ | 🖊 | Publication year (rendered as subtitle) |
| `{copyright:Text}` | | ✅ | 🖊 | Copyright notice (rendered as «© …») |
| `{key:Key}` | | ✅ | ⌨️ | Key (e.g. `Am`, `C`, `G`, `F#m`); rendered as «Key: …» when display is enabled |
| `{capo:N}` | | ✅ | 🖊 | Capo at fret N (e.g. `{capo:2}`); rendered as «Capo: N» |
| `{tempo:BPM}` | | ✅ | ⌨️ | Tempo in BPM with **quarter note** icon (e.g. `{tempo:120}`) |
| `{tempo_m:BPM}` | | 🔧 | 🖊 | Tempo with **half note** icon |
| `{tempo_s:BPM}` | | 🔧 | 🖊 | Tempo with **quarter note** icon |
| `{tempo_sp:BPM}` | | 🔧 | 🖊 | Tempo with **dotted quarter note** icon |
| `{tempo_c:BPM}` | | 🔧 | 🖊 | Tempo with **eighth note** icon |
| `{tempo_cp:BPM}` | | 🔧 | 🖊 | Tempo with **dotted eighth note** icon |
| `{time:N/M}` | | ✅ | ⌨️ | Time signature (e.g. `{time:4/4}`, `{time:3/4}`); rendered as a graphical time signature symbol |

> **Note on tempo** — The `{tempo*}` directives support three display modes, configurable in preferences: note icon + value (e.g. `♩ = 120`), text `BPM: 120`, or plain text `Tempo: 120`. Setting the mode to *hidden* (`-1`) treats the value as pure metadata — it will not appear in the preview or in print.

---

## Song Structure

### Text Blocks

| Directive | Std | Menu | Description |
| --- | --- | --- | --- |
| `{start_of_verse}` / `{end_of_verse}` | ✅ | ⌨️ | Unnumbered verse, no label |
| `{start_verse:Label}` / `{end_verse}` | 🔧 | ⌨️ | Unnumbered verse with optional label |
| `{start_verse_num}` / `{end_verse_num}` | 🔧 | ⌨️ | Automatically numbered verse |
| `{verse:Label}` | ✅ | ⌨️ | Opens a verse with a custom label (e.g. `{verse:1}`) |
| `{start_of_chorus}` / `{end_of_chorus}` | ✅ | ⌨️ | Chorus |
| `{soc}` / `{eoc}` | ✅ | ⌨️ | Shorthand for `start_of_chorus` / `end_of_chorus` |
| `{soc:Label}` | ✅ | ⌨️ | Chorus with custom label |
| `{start_chorus:Label}` / `{end_chorus}` | 🔧 | ⌨️ | Alternative chorus form (with optional label) |
| `{start_bridge:Label}` / `{end_bridge}` | 🔧 | ⌨️ | Bridge with optional label; defaults to «Bridge» if omitted |
| `{start_chord:Label}` / `{end_chord}` | 🔧 | ⌨️ | Intro/chord block; defaults to «Intro» if label is omitted |
| `{new_song}` | 🔧 | 🖊 | Starts a new song in the same document: resets verse and chorus counters so numbering restarts from 1 |

> **Note on `{start_of_bridge}`** — This form (with `of_`) is not handled by the renderer; use `{start_bridge}` / `{end_bridge}` instead.

### Page and Column Breaks

| Directive | Alias | Std | Menu | Description |
| --- | --- | --- | --- | --- |
| `{new_page}` | `{np}` | ✅ | ⌨️ | Explicit page break for printing |
| `{column_break}` | `{colb}` | ✅ | ⌨️ | Column break (2-column layout) |

---

## Chords and Inline Formatting

### Chords

Chords are inserted in the text using square brackets, immediately before the syllable they belong to:

```chordpro
[Am]Nel [F]blu [C]dipinto di [G]blu
```

### Local Fonts and Colours

These directives change the font for the following section; used without an argument they restore the default value.

| Opening directive | Closing directive | Std | Menu | Description |
| --- | --- | --- | --- | --- |
| `{textfont:Name}` | `{textfont}` | ✅ | ⌨️ | Text font family |
| `{textsize:Pt}` | `{textsize}` | ✅ | ⌨️ | Text size in pt (also accepts percentage, e.g. `{textsize:80%}`) |
| `{textcolour:#HEX}` | `{textcolour}` | ✅ | ⌨️ | Text colour in `#RRGGBB` format |
| `{chordfont:Name}` | `{chordfont}` | ✅ | ⌨️ | Chord font family |
| `{chordsize:Pt}` | `{chordsize}` | ✅ | ⌨️ | Chord size in pt (also accepts percentage) |
| `{chordcolour:#HEX}` | `{chordcolour}` | ✅ | ⌨️ | Chord colour in `#RRGGBB` format |

### Spacing

| Directive | Std | Menu | Description |
| --- | --- | --- | --- |
| `{linespacing:N}` | 🔧 | ⌨️ | Line spacing in points (e.g. `{linespacing:1}`); without argument restores the default value |
| `{chordtopspacing:N}` | 🔧 | ⌨️ | Space above chords in points (e.g. `{chordtopspacing:0}` to remove it); without argument restores the default value |
| `{row}` or `{r}` | 🔧 | 🖊 | Inserts a half vertical blank space (spacer) — not available in the menu, must be typed manually |

---

# Spacing Directives in Songpress++

---

## `{linespacing: <value>}`

**Menu item:** *Line Spacing*

### Description — linespacing

Sets the **line spacing** between text lines in the song from the point where the directive is inserted. It controls the overall vertical spacing between one line of text (with its chords) and the next.

### Syntax — linespacing

```chordpro
{linespacing: 13}
```

### Parameter — linespacing

| Value | Effect |
| --- | --- |
| `0` | Removes extra space between lines (default value in the insert dialog) |
| positive number | Adds vertical space between lines (in typographic points) |

### Usage Notes — linespacing

- The directive can be inserted anywhere in the song; it affects all subsequent lines.
- Typical values range from `10` to `20` depending on the font and size used.
- Useful for adjusting text density in print, especially with two-column layout or two-pages-per-sheet format.

---

## `{chordtopspacing: <value>}`

**Menu item:** *Space Above Chords*

### Description — chordtopspacing

Sets the **vertical space above the chords**, i.e. the distance between the top edge of the chord line and the content preceding it (e.g. the text line of the previous verse). It allows you to loosen or tighten the margin that visually separates the chords from the line above them.

### Syntax — chordtopspacing

```chordpro
{chordtopspacing: 4}
```

### Parameter — chordtopspacing

| Value | Effect |
| --- | --- |
| `0` | Removes extra space above chords (default value in the insert dialog) |
| positive number | Increases the visual breathing room above the chord line |

### Usage Notes — chordtopspacing

- Acts independently from `linespacing`: the two parameters add up in the overall spacing.
- Useful when chords appear visually "squeezed" against the text of the previous line.
- Like `linespacing`, it can be used multiple times in the same song at different points to vary the spacing section by section.

## Difference Between the Two Directives chordtopspacing vs linespacing

```text
[previous text line]
                         ↕  chordtopspacing  (space above chords)
[chord line:  G   D   A]
[text line:   When the sun...]
                         ↕  linespacing      (spacing between complete line pairs)
[chord line:  E   B...]
[text line:   ...rises and...]
```

In summary: `chordtopspacing` controls the margin **above** the chord+text pair, while `linespacing` controls the space **between** successive pairs.

## `{row}` / `{r}` 🖊

**Menu item:** *none — must be typed manually*

### Description — row

Inserts a **half vertical space** (spacer) between lines in the song. Useful for adding a small visual breath between verses without resorting to `{linespacing}`.

### Syntax — row

```chordpro
{row}
```

or in its abbreviated form:

```chordpro
{r}
```

### Usage Notes — row

- Inserts a space equal to approximately **half a line** relative to the current line spacing.
- Has no parameters: `{row}` and `{r}` are equivalent and accept no values.
- Not accessible from the **Insert** menu: must be typed directly in the editor.

---

## Comments and Editorial Notes

| Form | Alias | Std | Menu | Description |
| --- | --- | --- | --- | --- |
| `{comment:Text}` | `{c:Text}` | ✅ | ⌨️ | Comment visible in the preview, automatically enclosed in parentheses |
| `{comment_italic:Text}` | `{ci:Text}` | ✅ | 🖊 | Like `{comment}`, but with italic text |
| `{comment_box:Text}` | `{cb:Text}` | ✅ | 🖊 | Comment in a box |
| `# Text` | | ✅ | 🖊 | Comment line (preceded by `#`): treated as a blank line, does not appear in preview or print |

---

## Chord Diagrams, Keyboard and Images

| Directive | Std | Menu | Description |
| --- | --- | --- | --- |
| `{define: C base-fret 1 frets X 3 2 0 1 0}` | ✅ | ⌨️ | Defines a guitar chord diagram |
| `{taste:Chord}` | 🔧 | ⌨️ | Displays highlighted keys on the keyboard (klavier) — e.g. `{taste:Am}` |
| `{image: filename}` | ✅ | ⌨️ | Inserts an image (PNG, JPG, GIF, BMP, TIFF) into the song |

The keyboard (klavier) displays the keys corresponding to the specified chord, highlighted with the colour set in preferences.

### Image Directive

The `{image:}` directive embeds a raster image at the point where it appears in the song. The file path can be relative to the song file location or absolute.

| Option | Std | Description |
| --- | --- | --- |
| `width=N` | ✅ | Width in typographic points (1/72 inch), or percentage e.g. `width=50%` |
| `height=N` | ✅ | Height in typographic points, or percentage |
| `scale=N%` | ✅ | Scale factor, e.g. `scale=50%` (cannot be combined with width/height) |
| `align=left` | ✅ | Left alignment |
| `align=center` | ✅ | Centered alignment (default) |
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

If the image file is in the same folder as the song file, just the filename is enough. Paths containing spaces or backslashes must be enclosed in double quotes.

The image can be inserted via **Insert → Other → Image {image:}**, which opens a dialog to select the file and configure all options, with a real-time preview of the generated directive.

The numeric fields in the dialog use spin controls with increment arrows:

| Field | Initial value | Range | Step | Notes |
| --- | --- | --- | --- | --- |
| Width | 0 | 0–9999 | 1 | 0 = not included in directive |
| Height | 0 | 0–9999 | 1 | 0 = not included in directive |
| Scale | 100 | 1–500 | 1 | 100 = not included (it is the default) |
| Border | 1 | 0–50 | 0.5 | active only when checkbox is ticked |

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

All main directives are accessible via the **Insert** menu, which opens helper dialogs to fill in values. The `|` cursor in InsertWithCaret indicates where the cursor will be placed after insertion.

### Chord Management

- **Insert chord** — inserts `[|]` with the cursor inside the brackets
- **Move chord right / left** — moves the chord under the cursor by one character
- **Remove chords** — deletes all chords from the selection
- **Paste chords** — pastes only the chords (without text) from the copied selection
- **Propagate chords to verses** — copies the chords of the first verse to all verses with the same number of lines
- **Propagate chords to choruses** — same for choruses
- **Integrate chords** — converts two separate lines (chords above / text below) into inline ChordPro format

### Transposition and Notation

- **Transpose** — opens the dialog to transpose all chords
- **Simplify chords** — finds the easiest key to play in
- **Change notation** — converts between English notation (C D E…) and solfège (Do Re Mi…)
- **Normalize chords** — standardises chord spelling (e.g. `Hm` → `Bm`)
- **Convert Tab → ChordPro** — automatically converts tab format (chords above text) to inline ChordPro

### Format and Structure

- **Song font** — opens the dialog to set the global font
- **Text font** — inserts `{textfont}` / `{textsize}` / `{textcolour}` directives for the current span
- **Chord font** — inserts `{chordfont}` / `{chordsize}` / `{chordcolour}` directives
- **Verse labels** — shows/hides verse and chorus labels in the preview
- **Chords above / below** — positions chords above or below the text
- **Show chords** — three modes: none / first verse only / entire song
- **Page / column break lines** — shows/hides guide lines in the preview

### Text Cleanup

- **Remove superfluous blank lines** — deletes double blank lines
- **Normalize multiple spaces** — reduces multiple spaces to a single space

### Syntax Check

- **Check syntax** — analyses the text and flags unrecognised or malformed directives, with the option to navigate directly to the error

---

## Display Preferences

The following controls are found in the **Formatting** tab of preferences and affect the preview and print output.

| Field | Default value | Range | Step |
| --- | --- | --- | --- |
| Title underline thickness | 2 | 1–5 | 1 |
| Verse number border thickness | 1 | 1–5 | 1 |

---

## Print and Preview

- **Print preview** — shows the preview with "Print Options" and "Page Setup" buttons
- **Print** — prints directly (without preview if the option is disabled in preferences)
- **Page setup** — paper size, orientation and margins (in mm)

### Print Options

| Option | Description |
| --- | --- |
| Print 2 pages per sheet | Prints two logical pages side by side on a single physical sheet |
| Columns per page (1 / 2) | Distributes the text across one or two columns |
| Shrink to fit page | Scales down content to fit on a single page |
| Shrink to fit current page | Scales down further to avoid content being cut off at the bottom |
| Do not replicate (leave right half blank) | With 2 pages/sheet: leaves the second half empty instead of replicating |
| Remove blank pages | Eliminates empty pages from the print output |

The `{new_page}` directive in the text forces a new logical page during printing. With the 2-column layout, `{column_break}` forces a move to the next column.

---

## Export

| Format | Notes |
| --- | --- |
| SVG | Vector, scalable |
| EMF | Windows vector |
| PNG | Raster image |
| HTML | Web page with coloured chords |
| Tab | Plain text format with chords above |
| PDF | PDF document |
| PowerPoint (.pptx) | Presentation |
| Songbook | Song collection |
| Copy as image | Copies to clipboard as vector |
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

The modifications present in Songpress++ are copyright © Denisov21.

Songpress++ is distributed under the terms of the **GNU General Public License version 2** (GPL v2), the same license as the original project. The program is free software: you can redistribute it and/or modify it under the terms of the GPL v2 as published by the Free Software Foundation. The program is distributed in the hope that it will be useful, but **without any warranty**, not even the implied warranty of merchantability or fitness for a particular purpose.

The full license text is available at: <https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>

### Third-party Components

Songpress (and consequently Songpress++) makes use of the following third-party software components:

| Component | License | Reference |
| --- | --- | --- |
| Python and Python standard library | Python Software Foundation License | <https://www.python.org> |
| wxPython | wxWindows Library Licence | <https://wxpython.org> |
| Editra (error reporting dialog) | wxWindows Library Licence v3.1 | <https://github.com/cjprecord/editra> |
| uv (Windows installer only) | MIT License — copyright © 2025 Astral Software Inc. | <https://github.com/astral-sh/uv> |
