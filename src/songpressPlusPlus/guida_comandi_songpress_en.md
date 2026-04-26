# Songpress++ Command Reference

Songpress++ uses the extended **ChordPro** format. Commands are enclosed in curly braces `{...}` and may accept a value separated by a colon `{command: value}`. Chords are inserted in square brackets `[Chord]` directly within the text. Lines beginning with `#` are comments and are ignored.

---

## Table of Contents

1. [Song structure](#1-song-structure)
   - [title / t](#title--t)
   - [subtitle / st](#subtitle--st)
   - [start_of_verse / end_of_verse](#start_of_verse--end_of_verse)
   - [start_verse / end_verse](#start_verse--end_verse)
   - [start_verse_num / end_verse_num](#start_verse_num--end_verse_num)
   - [start_of_chorus / end_of_chorus](#start_of_chorus--end_of_chorus)
   - [start_chorus / end_chorus](#start_chorus--end_chorus)
   - [start_of_bridge / end_of_bridge](#start_of_bridge--end_of_bridge)
   - [start_bridge / end_bridge](#start_bridge--end_bridge)
   - [start_chord / end_chord](#start_chord--end_chord)
   - [start_of_part / end_of_part](#start_of_part--end_of_part)
   - [verse](#verse)
   - [row / r](#row--r)
   - [new_song](#new_song)
2. [Tab and chord grid](#2-tab-and-chord-grid)
   - [start_of_tab / end_of_tab](#start_of_tab--end_of_tab)
   - [start_of_grid / end_of_grid](#start_of_grid--end_of_grid)
3. [Comments and annotations](#3-comments-and-annotations)
   - [comment / c](#comment--c)
   - [comment_italic / ci](#comment_italic--ci)
   - [comment_box / cb](#comment_box--cb)
4. [Metadata](#4-metadata)
   - [artist](#artist)
   - [composer](#composer)
   - [lyricist](#lyricist)
   - [arranger](#arranger)
   - [album](#album)
   - [year](#year)
   - [duration](#duration)
   - [ccli](#ccli)
   - [copyright](#copyright)
   - [key](#key)
   - [capo](#capo)
5. [Page layout](#5-page-layout)
   - [new_page / np](#new_page--np)
   - [column_break / colb](#column_break--colb)
6. [Musical directives](#6-musical-directives)
   - [tempo](#tempo)
   - [tempo_m](#tempo_m)
   - [tempo_s](#tempo_s)
   - [tempo_c](#tempo_c)
   - [tempo_sp](#tempo_sp)
   - [tempo_cp](#tempo_cp)
   - [time](#time)
   - [beats_time](#beats_time)
7. [Text formatting](#7-text-formatting)
   - [textsize](#textsize)
   - [textfont](#textfont)
   - [textcolour / textcolor](#textcolour--textcolor)
   - [linespacing](#linespacing)
8. [Chord formatting](#8-chord-formatting)
   - [chordsize](#chordsize)
   - [chordfont](#chordfont)
   - [chordcolour / chordcolor](#chordcolour--chordcolor)
   - [chordtopspacing](#chordtopspacing)
9. [Diagrams and images](#9-diagrams-and-images)
   - [define](#define)
   - [taste](#taste)
   - [fingering](#fingering)
   - [image](#image)
10. [Inline chords](#10-inline-chords)
11. [Line comments](#11-line-comments)
12. [Application preferences](#12-application-preferences)
    - [General tab](#general-tab)
    - [Auto-corrections tab (AutoAdjust)](#auto-corrections-tab-autoadjust)
    - [Format tab](#format-tab)
    - [Preview tab (Songpress++ Preview)](#preview-tab-songpress-preview)
    - [Quick guide tab](#quick-guide-tab)
    - [Context menu tab](#context-menu-tab)
    - [File associations tab](#file-associations-tab)
    - [Format menu settings](#format-menu-settings)
13. [Final summary](#13-final-summary)

---

## 1. Song structure

### `title` / `t`

**Syntax:** `{title: Song title}` or `{t: Title}`

Sets the song title. It is displayed at the top of the page with the title typographic style (larger font, optional decorative line). A value is required.

```chordpro
{title: Amazing Grace}
```

---

### `subtitle` / `st`

**Syntax:** `{subtitle: Subtitle}` or `{st: Subtitle}`

Sets the song subtitle, displayed below the title in a smaller style. Useful for indicating the artist, original key, or other secondary information.

```chordpro
{subtitle: Traditional}
```

---

### `start_of_verse` / `end_of_verse`

**Syntax:**
```chordpro
{start_of_verse: Label}
...text...
{end_of_verse}
```

Delimits a verse. The label is optional: if omitted, the verse receives an automatic sequential number (1., 2., etc.) based on the "show labels" setting in Songpress++. Abbreviations are `{sov}` and `{eov}`.

```chordpro
{sov: Verse 1}
[C]Text of the [G]first verse
[Am]more text [F]here
{eov}
```

---

### `start_verse` / `end_verse`

**Syntax:**
```chordpro
{start_verse: Optional label}
...text...
{end_verse}
```

Alternative variant of `start_of_verse` / `end_of_verse`, introduced as a Songpress++ extension. Behaviour is identical. Useful if a more compact syntax is preferred.

---

### `start_verse_num` / `end_verse_num`

**Syntax:**
```chordpro
{start_verse_num: Label}
...text...
{end_verse_num}
```

Like `start_verse`, but **forces** automatic numbering even when a label is specified. If the label is empty or absent, the sequential number is still assigned. Use when numbering must be guaranteed regardless of the label.

---

### `start_of_chorus` / `end_of_chorus`

**Syntax:**
```chordpro
{start_of_chorus: Optional label}
...chorus text...
{end_of_chorus}
```

Delimits a chorus. The chorus is displayed with a distinct visual style (box, background, configurable label via Songpress++ preferences). Abbreviations are `{soc}` and `{eoc}`.

```chordpro
{soc}
[G]Chorus: text of the [D]chorus
{eoc}
```

---

### `start_chorus` / `end_chorus`

**Syntax:**
```chordpro
{start_chorus}
...text...
{end_chorus}
```

Alternative variant of `start_of_chorus` / `end_of_chorus`. Identical behaviour.

---

### `start_of_bridge` / `end_of_bridge`

**Syntax:**
```chordpro
{start_of_bridge: Optional label}
...bridge text...
{end_of_bridge}
```

Delimits a bridge. It is treated as a special verse with its own separate numbering distinct from ordinary verses. Abbreviations are `{sob}` and `{eob}`.

---

### `start_bridge` / `end_bridge`

**Syntax:**
```chordpro
{start_bridge: Optional label}
...text...
{end_bridge}
```

Alternative variant of `start_of_bridge` / `end_of_bridge`. Identical behaviour.

---

### `start_chord` / `end_chord`

**Syntax:**
```chordpro
{start_chord: Optional label}
...block...
{end_chord}
```

Creates a generic verse-type block with a custom label. Useful for sections that do not fit standard categories (e.g. intro, coda, solo).

```chordpro
{start_chord: Intro}
[C] / / / | [G] / / /
{end_chord}
```

---

### `start_of_part` / `end_of_part`

**Syntax:**
```chordpro
{start_of_part: Optional label}
...text...
{end_of_part}
```

Generic section conforming to **ChordPro 6**. Treated exactly like `start_chord` / `end_chord`: creates a verse block with the given label, not automatically numbered. If the label is omitted, the default label `Part` is used. Abbreviations are `{sop}` and `{eop}`.

```chordpro
{sop: Outro}
[Em]Text of the final section
{eop}
```

---

### `verse`

**Syntax:** `{verse: Label}`

Adds a reference to an already-defined verse. In Songpress++ it is treated as opening a new verse block with the given label. Rarely used: prefer `start_of_verse`.

---

### `row` / `r`

**Syntax:** `{row}` or `{r}`

Inserts a **blank separator row** between sections, without creating a new block. Adds half a line of vertical visual space. Can also be used **inside a `{start_of_grid}` block** to separate groups of grid rows.

```chordpro
{sov}
First part text
{row}
Second part text
{eov}
```

---

### `new_song`

**Syntax:** `{new_song}`

Completely resets the renderer state: clears verse, chorus and label counters, and restores fonts and colours to their default values. Useful when concatenating multiple songs in a single ChordPro file or using `{start_of_grid}` on multi-song documents.

---

## 2. Tab and chord grid

### `start_of_tab` / `end_of_tab`

**Syntax:**
```chordpro
{start_of_tab: Optional label}
...ASCII text...
{end_of_tab}
```

Delimits an ASCII tablature block. Inside the block:
- A **monospace font** (e.g. Courier New) is used automatically.
- Chords in `[...]` are **suppressed**: the tab is already complete notation.
- Text is displayed exactly as written, preserving spaces and alignment.
- Abbreviations are `{sot}` and `{eot}`.

```chordpro
{sot: Fingerpicking}
e|---0---2---3---|
B|---1---3---0---|
G|---0---2---0---|
{eot}
```

---

### `start_of_grid` / `end_of_grid`

**Syntax:**
```chordpro
{start_of_grid: Label [size=N] [chordtopspacing=N] [linespacing=N]}
...chord rows...
{end_of_grid}
```

Delimits a **chord grid** block (harmonic scheme per bar). Abbreviations are `{sog}` / `{eog}` and the bare `{grid}` also opens the block.

**Optional parameters in the opening directive:**

| Parameter | Description | Example |
|---|---|---|
| `size=N` | Cell size multiplier (default: 1). Accepts decimals. | `size=2` |
| `sizedir=horizontal\|vertical\|both` | Direction to which `size=N` applies: horizontal, vertical, or both (default: value from preferences, usually `both`) | `sizedir=horizontal` |
| `chordtopspacing=N` | Extra space in pixels above each grid row | `chordtopspacing=10` |
| `linespacing=N` | Extra space in pixels below each grid row | `linespacing=8` |
| Free label | Block label text (after any key=value parameters) | `size=2 Chorus` |

**Row format inside the block:**

*Pipe format* (default): bars are separated by `|`. Chords may be written as plain text or in `[...]`.

```chordpro
{sog: size=1.5 Harmony}
C | G | Am | F
C | G | F  | F
{eog}
```

*Plain format* (spaces only): bars are separated by spaces. Proportional width is calculated automatically based on text length.

```chordpro
{sog}
C  G  Am F
{eog}
```

**Display modes** (configurable in preferences):
- `pipe` — table with visible `|` separators
- `plain` — side-by-side cells without borders
- `table` — cells with graphic borders

**Using `{row}` / `{r}` inside the block:** inserts a blank separator row between groups of bars.

```chordpro
{sog}
C | G | Am | F
{r}
F | C | G  | G
{eog}
```

---

## 3. Comments and annotations

### `comment` / `c`

**Syntax:** `{comment: Text}` or `{c: Text}`

Inserts a visible comment in the preview, in normal style. Useful for performance annotations (e.g. "D.C. al Coda", "with pedal", "ritardando"). The text is displayed in the song flow, visually distinct from the sung text.

```chordpro
{c: Repeat 2 times}
```

---

### `comment_italic` / `ci`

**Syntax:** `{comment_italic: Text}` or `{ci: Text}`

Like `comment`, but the text is displayed in **italics**. Typically used for dynamic or expressive indications.

```chordpro
{ci: Piano, with delicacy}
```

---

### `comment_box` / `cb`

**Syntax:** `{comment_box: Text}` or `{cb: Text}`

Like `comment`, but the text is enclosed in a **graphic box** for greater emphasis. Used for important sections or warnings.

```chordpro
{cb: CODA}
```

---

## 4. Metadata

Metadata is stored in the song but **does not appear visually in the preview** as separate elements (except `title`, `subtitle`, `key`, `capo`). It is included in export formats that support it.

> **ChordPro 6 metadata silently ignored:** the following commands are recognised and consumed by the renderer without generating errors, but produce no visual output and are not exported: `{sorttitle}`, `{keywords}`, `{topic}`, `{collection}`, `{language}`, `{pagetype}`, `{columns}`, `{meta}`, `{transpose}`. They can be included in the file for compatibility with other ChordPro editors without side effects.

### `artist`

**Syntax:** `{artist: Artist name}`

Name of the artist or group performing the song.

```chordpro
{artist: The Beatles}
```

---

### `composer`

**Syntax:** `{composer: Composer name}`

Name of the music composer (may differ from the performing artist).

```chordpro
{composer: John Lennon}
```

---

### `lyricist`

**Syntax:** `{lyricist: Lyricist name}`

Name of the lyricist (text author), when different from the music composer. Displayed in the preview as a subtitle with the prefix **`Lyrics:`**.

```chordpro
{lyricist: Paul McCartney}
```

> Displayed as: *Lyrics: Paul McCartney*

---

### `arranger`

**Syntax:** `{arranger: Arranger name}`

Name of the arranger. Displayed in the preview as a subtitle with the prefix **`Arrangement:`**.

```chordpro
{arranger: George Martin}
```

> Displayed as: *Arrangement: George Martin*

---

### `album`

**Syntax:** `{album: Album title}`

Title of the album the song comes from.

```chordpro
{album: Abbey Road}
```

---

### `year`

**Syntax:** `{year: Year}`

Year of publication or composition.

```chordpro
{year: 1969}
```

---

### `duration`

**Syntax:** `{duration: Duration}`

Duration of the song. The recommended format is `mm:ss` (e.g. `3:45`), but the field accepts any text string. **Storage-only metadata**: the value is silently consumed by the renderer and does not appear in the preview or in print. It can be included in the file for compatibility with other ChordPro editors or for external use (exporters, databases).

```chordpro
{duration: 3:45}
{duration: 4:28}
```

> To associate beat durations to individual chords on a line, use `{beats_time:}` instead (section 6).

---

### `ccli`

**Syntax:** `{ccli: Number}`

**CCLI** (Christian Copyright Licensing International) licence number, used in liturgical/choral settings to track songs covered by a CCLI licence. Storage-only metadata, not displayed in the preview.

```chordpro
{ccli: 1234567}
```

---

### `copyright`

**Syntax:** `{copyright: Copyright text}`

Copyright information. A non-empty value is required.

```chordpro
{copyright: © 1969 Northern Songs}
```

---

### `key`

**Syntax:** `{key: Key}`

Indicates the **key** of the song. The value is displayed in the preview (if the "Show key" option is enabled in preferences). Supports Italian notation (Do, Re, Mi…) and English notation (C, D, E…) with accidentals (`#`, `b`).

```chordpro
{key: A minor}
{key: Am}
{key: F#}
```

---

### `capo`

**Syntax:** `{capo: N}`

Indicates the **capo** position (barre). N is the fret number. Displayed in the preview as a text indication.

```chordpro
{capo: 3}
```

---

## 5. Page layout

### `new_page` / `np`

**Syntax:** `{new_page}` or `{np}`

Forces a **page break** at the point where it appears. In print and preview the song is split exactly at that point. Particularly useful for long songs or multi-page songbooks.

```chordpro
{sov: Verse 1}
...
{eov}
{new_page}
{sov: Verse 2}
...
{eov}
```

> **Note:** Lines commented with `#` that contain `{new_page}` are ignored and produce no break.

---

### `column_break` / `colb`

**Syntax:** `{column_break}` or `{colb}`

Forces a **column break** when printing is configured in multi-column mode. The next block is placed at the start of the following column. In single-column print, the effect is equivalent to a page break.

```chordpro
{sov: Verse 1}
...
{eov}
{colb}
{sov: Verse 2}
...
{eov}
```

---

## 6. Musical directives

Tempo indications are displayed in the preview according to the mode chosen in preferences (*Tools → Preferences → Preview → Tempo display*):

| Mode | Description |
|---|---|
| `0` (text) | Shows the numeric value as text (e.g. "♩ = 120") |
| `1` (graphic note) | Shows the note icon + numeric value |
| `2` (text only) | Shows only the number without a symbol |
| `3` (metronome) | Shows a metronome icon |
| `-1` (hidden) | The metadata is stored but not displayed |

---

### `tempo`

**Syntax:** `{tempo: N}`

Indicates the **tempo** in BPM referenced to the **quarter note** (♩ = N). This is the most common tempo command.

```chordpro
{tempo: 120}
```

---

### `tempo_m`

**Syntax:** `{tempo_m: N}`

Tempo referenced to the **half note** (𝅗𝅥 = N). Used for pieces in cut time (2/2, alla breve).

```chordpro
{tempo_m: 60}
```

---

### `tempo_s`

**Syntax:** `{tempo_s: N}`

Synonym for `tempo`: tempo referenced to the **quarter note** (♩ = N). Useful to disambiguate when multiple tempo indications are used in the same file.

```chordpro
{tempo_s: 96}
```

---

### `tempo_c`

**Syntax:** `{tempo_c: N}`

Tempo referenced to the **eighth note** (♪ = N). Used for pieces in 6/8, 9/8, 12/8.

```chordpro
{tempo_c: 176}
```

---

### `tempo_sp`

**Syntax:** `{tempo_sp: N}`

Tempo referenced to the **dotted quarter note** (♩. = N). Common in simple ternary time signatures.

```chordpro
{tempo_sp: 72}
```

---

### `tempo_cp`

**Syntax:** `{tempo_cp: N}`

Tempo referenced to the **dotted eighth note** (♪. = N).

```chordpro
{tempo_cp: 116}
```

---

### `time`

**Syntax:** `{time: N/D}`

Indicates the **time signature** of the song. N is the number of beats per bar, D is the note value of the reference beat. Displayed in the preview (if the "Show time signature" option is enabled).

```chordpro
{time: 4/4}
{time: 3/4}
{time: 6/8}
```

---

### `beats_time`

**Syntax:** `{beats_time: CHORD=beats CHORD=beats ...}`

Associates a number of **beats** with each chord on the immediately following line. Tokens have the form `CHORD=N`, where `N` is a positive integer. Chords are written in uppercase; a flat is written with a hyphen (`La-` = A♭ in Italian notation).

The association is **positional**: the first token refers to the first `[...]` chord on the line, the second to the second, and so on. If the number of tokens is fewer than the number of chords, the remaining chords receive no duration.

```chordpro
{beats_time: C=4 G=2 Am=2}
[C]First [G]part [Am]brief
```

Duration values are shown in the preview next to the chords (if the **Show beat durations** option is enabled in the View menu). Colour, size and display mode are configurable in *Preferences → Format → Beat durations*.

> The directive acts only on the next line; it has no effect on more distant lines. For the overall duration of the song use `{duration:}` (section 4).

---

## 7. Text formatting

These commands change the appearance of the sung text from the point where they appear. Values apply for the rest of the song or until a new command of the same type. Used without a value, they **restore the default**.

### `textsize`

**Syntax:** `{textsize: N}` or `{textsize}` to reset

Sets the **font size** of the text in typographic points. The value must be a positive integer.

```chordpro
{textsize: 14}
Larger text
{textsize}
Normal-size text
```

---

### `textfont`

**Syntax:** `{textfont: FontName}` or `{textfont}` to reset

Sets the **font** of the sung text. The name must exactly match a font installed on the system.

```chordpro
{textfont: Georgia}
Text with serif font
{textfont}
```

---

### `textcolour` / `textcolor`

**Syntax:** `{textcolour: #RRGGBB}` or `{textcolour: colour_name}`

Sets the **colour** of the sung text. Accepts CSS hex values (`#FF0000`) or English colour names (`red`, `blue`, etc.).

```chordpro
{textcolour: #CC0000}
Red text
{textcolour: black}
```

---

### `linespacing`

**Syntax:** `{linespacing: N}` or as an attribute in `{start_of_grid}`

Sets the **extra spacing** in pixels between text lines. When used as an attribute of `{start_of_grid}`, it applies only to that grid block.

```chordpro
{linespacing: 6}
```

---

## 8. Chord formatting

### `chordsize`

**Syntax:** `{chordsize: N}` or `{chordsize}` to reset

Sets the **font size** of the chords in typographic points. Like `textsize`, it applies from that point forward.

```chordpro
{chordsize: 11}
[C]Smaller [G]chord
{chordsize}
```

---

### `chordfont`

**Syntax:** `{chordfont: FontName}` or `{chordfont}` to reset

Sets the **font** of the chords. Useful to visually distinguish chords and text with different typeface families.

```chordpro
{chordfont: Arial Bold}
```

---

### `chordcolour` / `chordcolor`

**Syntax:** `{chordcolour: #RRGGBB}` or `{chordcolour: colour_name}`

Sets the **colour** of the chords. Same format as `textcolour`.

```chordpro
{chordcolour: #0055AA}
[C]Blue [G]chord
{chordcolour: black}
```

---

### `chordtopspacing`

**Syntax:** `{chordtopspacing: N}` or as an attribute in `{start_of_grid}`

Sets the **extra space in pixels between the chord row and the text** below it. Increasing it creates more visual breathing room. When used as an attribute of `{start_of_grid}`, it applies only to that grid block.

```chordpro
{chordtopspacing: 8}
```

---

## 9. Diagrams and images

### `define`

**Syntax:** `{define: ChordName base-fret N frets X N N N N N}`

Defines a custom **guitar chord diagram**. The format follows the ChordPro standard:
- `base-fret N` indicates the starting fret of the diagram
- `frets` lists the finger position on each string (from lowest to highest): `X` = muted string, `0` = open string, number = fret

```chordpro
{define: C base-fret 1 frets X 3 2 0 1 0}
{define: Barre7 base-fret 7 frets 1 1 1 1 1 1}
```

The diagram is displayed in the preview (if the "Show guitar diagrams" option is enabled) above the first occurrence of the chord in the song.

---

### `taste`

**Syntax:** `{taste: ChordName}`

Shows the **piano keyboard** with the chord notes highlighted (Klavier function). It is the keyboard equivalent of `define`. The keyboard is rendered graphically with the pressed keys coloured.

```chordpro
{taste: Cmaj7}
{taste: Am}
```

> The colour of the highlighted keys is configurable in *Preferences → Format → Klavier key colour*.

---

### `fingering`

**Syntax:** `{fingering: ChordName N=Note [N=Note ...]}`

Shows the **piano keyboard** of a chord with **numbered fingering**: the finger number is displayed above each pressed key. Extends `{taste}` by adding a finger→note map.

The format is: chord name, followed by `finger_number=note` pairs (e.g. `1=C`, `2=E`, `3=G`). The KlavierRenderer interprets the map and draws the numbers on the keys. The colour of the numbers is configurable in preferences.

```chordpro
{fingering: Am 1=C 2=E 3=A}
{fingering: C 1=E 2=G 3=C}
```

> The `{taste}` and `{fingering}` commands use the same internal list (`klavier_list`): they can coexist freely in the same file.

---

### `image`

**Syntax:**
```
{image: path/file.png [width=N] [height=N] [scale=N] [align=left|center|right] [border[=N]]}
```

Inserts an **image** in the body of the song. The path can be absolute or relative to the location of the `.crd` file. Optional parameters:

| Parameter | Description | Default |
|---|---|---|
| `width=N` | Width in logical points (0 = automatic) | `0` |
| `height=N` | Height in logical points (0 = automatic) | `0` |
| `scale=N` | Scale factor (e.g. `0.5` = 50%, `2` = 200%) | `1.0` |
| `align=left\|center\|right` | Horizontal alignment | `center` |
| `border` / `border=N` | Adds a border; N is the thickness (without N, default = 1) | no border |

The keywords `left`, `center`, `right` can also be used alone without the `align=` prefix.

```chordpro
{image: img/logo.png width=200 align=center}
{image: photo.jpg scale=0.5 border=2}
{image: cover.png left}
```

---

## 10. Inline chords

Chords are not `{...}` commands but are inserted in **square brackets** `[...]` directly in the text, at the exact point where they fall on the last syllable.

**Syntax:** `[Chord]text`

```chordpro
[C]Text of the [G]song with [Am]inline [F]chords
```

**Supported notations:**
- **English:** `C`, `Dm`, `G7`, `Am/E`, `F#m`, `Bb`, `Cmaj7`, `Csus4`, etc.
- **Italian:** `Do`, `Rem`, `Sol7`, `Lam/Mi`, `Fa#m`, `Sib`, etc.

Chords are displayed **above** the text (or below, if configured in preferences). The vertical position is defined by the *Chords above/below* option in the Format menu.

---

## 11. Line comments

Lines beginning with `#` are **comments** and are completely ignored by the renderer. They can be used for internal file notes or to temporarily disable a line.

```chordpro
# This line is not displayed
# {new_page} — this page break is disabled
{t: My Song}
```

A `#` appearing **inside a line** (not at the beginning) is treated as an inline comment: everything after the `#` (outside `[...]` and `{...}`) is ignored.

---

## 12. Application preferences

Preferences are opened from the **Tools → Preferences** menu (or with the corresponding shortcut). The window is organised in seven tabs.

---

### General tab

#### Group: Editor font

| Setting | Type | Default | Description |
|---|---|---|---|
| **Editor font** | ComboBox | system monospace font | Font used in the text editor for typing ChordPro code. |
| **Size** | ComboBox | 12 | Font size in points for the editor (values: 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20). |
| **Editor background colour** | Colour (#HEX) | `#FFFFFF` | Background colour of the editor text area. The **Pick…** button opens the colour picker with a saved custom palette. |
| **Selection colour** | Colour (#HEX) | `#C0C0C0` | Highlight colour of selected text in the editor. |
| **Editor panel bar colour** | Colour (#HEX) | `#4682C8` | Base colour of the **Editor** panel title bar. The active/inactive gradient is calculated automatically from this colour. |
| **Preview panel bar colour** | Colour (#HEX) | `#329B82` | Base colour of the **Preview** panel title bar. |

A live preview area shows in real time how the text looks with the current font, background and selection settings.

#### Group: Song

| Setting | Type | Default | Description |
|---|---|---|---|
| **Default notation** | Choice | English | Default musical notation for chords: English (C, D, E…) or Italian (Do, Re, Mi…). Used for automatic recognition and transposition. |
| **Default file extension** | Choice | `crd` | Default extension for saving files: `crd`, `cho`, `chordpro`, `chopro`, `pro`, `tab`. |
| **Language** | ComboBox with flag | system | Interface language of Songpress++. The change takes effect on the next restart. |

#### Group: General

| Setting | Type | Default | Description |
|---|---|---|---|
| **Clear recent files** | Button | — | Immediately clears the list of recently opened files from the File menu. |
| **Show print preview before printing** | Checkbox | ✔ active | If active, opens the print preview before sending to the printer. |
| **Enable multi-cursor (Alt+Click, Ctrl+D)** | Checkbox | ✗ inactive | Enables multi-cursor mode in the editor: Alt+Click adds a cursor, Ctrl+D selects the next occurrence of the selected word. |
| **Save window size and position on exit** | Checkbox | ✔ active | If active, saves the size, position and maximised state of the main window on close and restores them on reopen. |

---

### Auto-corrections tab (AutoAdjust)

Songpress++ can offer automatic corrections when it detects certain patterns in pasted or typed text.

| Setting | Type | Default | Description |
|---|---|---|---|
| **Suggest removal of spurious blank lines** | Checkbox | ✔ active | If pasted text contains spurious blank lines (typical of songs copied from websites), Songpress++ suggests removing them automatically. |
| **Suggest conversion from tab format** | Checkbox | ✔ active | If it detects that the text is in tab format (chords on one line, text on the next), suggests automatic conversion to ChordPro. |
| **Suggest transposition to simplify chords** | Checkbox | ✗ inactive | If the song uses difficult chords and a simpler key exists, suggests automatic transposition. |

Below the three checkboxes is a scrollable panel with configurable **easy chord groups**, with a slider for each group (e.g. open chords, barre chords at fret I, etc.). Each slider indicates how much "weight" to assign to that group in the difficulty calculation.

---

### Format tab

#### Group: Title and structure

| Setting | Type | Range | Default | Description |
|---|---|---|---|---|
| **Title underline thickness** | SpinCtrl | 1–5 | 4 | Thickness in pixels of the decorative line below the song title in the preview. |
| **Verse number box thickness** | SpinCtrl | 1–5 | 1 | Thickness in pixels of the box around the verse number in the preview. |

#### Group: Chords and tempo

| Setting | Type | Default | Description |
|---|---|---|---|
| **Klavier key colour** | Colour (#HEX) | `#D23C3C` | Colour of the highlighted keys on the Klavier keyboard (piano diagram rendered by `{taste:}`). |
| **Tempo icon size** | RadioButton | 24×24 | Size of the graphic tempo icons (`{tempo:`, etc.) in the preview. Values: 16×16, 24×24, 32×32 pixels. |

#### Group: Chord grid — `{start_of_grid}`

| Setting | Type | Default | Description |
|---|---|---|---|
| **Display mode** | RadioButton | Pipe table | Display mode for chord grids (see below). |
| **Default grid label** | TextCtrl | `Grid` | Label shown next to the grid block when `{start_of_grid}` does not specify an explicit label. |
| **Space bar inserts \| (pipe mode)** | Checkbox | ✔ active | When active, pressing the Space bar inside a `{start_of_grid}` block inserts the `|` character instead of a space, making pipe-mode typing easier. |
| **size=N applies to** | RadioButton | Width and height | Controls which cell dimensions the `size=N` multiplier of the `{start_of_grid}` directive applies to: width and height, width only, or height only. |

**Grid display modes:**

| Option | Appearance | Description |
|---|---|---|
| **Pipe table** | `\| C \| G \| Am \| F \|` | Bars are separated by `\|` characters. Default mode. |
| **Plain spacing** | `C   G   Am  F` | Cells are side by side with proportional spacing, without separators. |
| **Bordered table** | cells with graphic borders | Each bar is enclosed in a cell with a visible graphic border. |

---

### Preview tab (Songpress++ Preview)

These settings control the behaviour of the real-time preview panel.

| Setting | Type | Default | Description |
|---|---|---|---|
| **Show page indicator (e.g. 'Page 1 of 3')** | Checkbox | ✔ active | Shows or hides the page counter in the top-right corner of the preview panel (e.g. "Page 1 of 3"). |
| **Grey background in preview (page style)** | Checkbox | ✔ active | Shows the preview on a grey background with the white page in the centre, simulating a printed sheet. If disabled, the background is plain white. |
| **Delay preview update while typing** | Checkbox | ✔ active | Delays the preview redraw until a brief pause in typing, improving performance on long files. If disabled, the preview updates on every key press. |
| **Double-click in preview jumps to source line** | Checkbox | ✔ active | Double-clicking on a word or chord in the preview moves the editor cursor to the corresponding line in the ChordPro source. |
| **Set minimum preview panel size on startup (370×520)** | Checkbox | ✔ active | Prevents the preview panel from being resized below 370×520 pixels. Useful to avoid the preview becoming too small to read. |

---

### Quick guide tab

Configures the built-in Songpress++ quick guide viewer.

#### Group: Markdown viewer

| Setting | Type | Default | Description |
|---|---|---|---|
| **Markdown viewer** | Choice | Automatic | Engine used to render the Markdown guide: **Automatic** (tries python-markdown, then mistune, then the built-in parser), **python-markdown**, **mistune**, **Built-in parser**. |

#### Group: Image paths

| Setting | Type | Default | Description |
|---|---|---|---|
| **Use absolute image paths in Markdown** | Checkbox | ✗ inactive | If active, image paths in the guide are rewritten as full absolute paths (`../src/songpress/img/GUIDE/...`). Useful for viewing the guide in external Markdown editors. |

---

### Context menu tab

Allows customising which items appear in the **context menu** (right-click) of the editor. Each item can be enabled or disabled individually.

#### Group: History

| Item | Default |
|---|---|
| Undo | ✔ |
| Redo | ✔ |

#### Group: Edit

| Item | Default |
|---|---|
| Cut | ✔ |
| Copy | ✔ |
| Paste | ✔ |
| Delete | ✔ |

#### Group: Special actions

| Item | Default | Description |
|---|---|---|
| Paste chords | ✔ | Pastes only the chords from the copied text, overwriting any present. |
| Propagate verse chords | ✔ | Propagates the chord pattern of the current verse to all verses with the same pattern. |
| Propagate chorus chords | ✔ | Same as above, for the chorus. |
| Copy text only | ✔ | Copies the text without chords to the clipboard. |

#### Group: Selection

| Item | Default |
|---|---|
| Select all | ✔ |

---

### File associations tab

Available **on Windows only**. Allows associating ChordPro file extensions with Songpress++ for the current user, so that double-clicking a file opens the application directly.

| Extension | Description |
|---|---|
| `.crd` | Main Songpress++ format |
| `.cho` | Classic ChordPro |
| `.chordpro` | Extended ChordPro |
| `.chopro` | ChordPro variant |
| `.pro` | ChordPro abbreviation |
| `.tab` | Tab format |

The **Associate all** and **Remove all** buttons select or deselect all extensions in a single click.

> File association changes take effect immediately and apply only to the current Windows user (no administrator privileges required).

---

### Format menu settings

Some settings are not found in the Preferences window but in the **Format** menu of the main menu bar. They are saved automatically when the application closes.

#### Chord display (toolbar slider)

Controls how many verses are shown with chords in the preview.

| Slider position | Behaviour |
|---|---|
| 0 — No chords | No verse shows chords. Useful for text-only printing. |
| 1 — One verse per pattern | Only the first verse of each chord pattern is shown with chords. Identical verses are shown without chords for readability. |
| 2 — Whole song | All chords in all verses are always visible. |

#### Verse labels (toolbar button)

| Setting | Description |
|---|---|
| **Show verse labels** (toggle) | Shows or hides numbered verse labels and chorus boxes in the preview and in print. |

#### Chord position

| Setting | Description |
|---|---|
| **Chords above** | Chords are displayed above the corresponding text line (default behaviour). |
| **Chords below** | Chords are displayed below the text line. |

#### Tempo indication `{tempo:}` — display mode

Accessible from **Format → Tempo indication** (or by clicking the indication in the preview). Controls how the tempo value is represented.

| Mode | Internal value | Description |
|---|---|---|
| Note icon + number | `1` | Shows the graphic icon of the reference note followed by the BPM value (e.g. ♩ = 120). |
| Text only | `2` | Shows only the BPM number without a graphic symbol. |
| Metronome icon | `3` | Shows a metronome icon with the BPM value. |
| Plain text | `0` | Shows the text in compact form (e.g. "♩=120") without a separate icon. |
| Metadata only (hidden) | `-1` | The value is stored in the file but not displayed in the preview or in print. |

#### Time signature `{time:}` — visibility

| Setting | Description |
|---|---|
| **Show time signature** | If active, the time signature (e.g. 4/4, 3/4) is displayed in the preview. |
| **Metadata only** | The time signature is stored in the file but not displayed. |

#### Key `{key:}` — visibility

| Setting | Description |
|---|---|
| **Show key** | If active, the key is displayed in the preview. |
| **Metadata only** | The key is stored in the file but not displayed. |

---

## 13. Final summary

| Command | Abbreviation | Category | Brief description |
|---|---|---|---|
| `{title: ...}` | `{t:}` | Structure | Song title |
| `{subtitle: ...}` | `{st:}` | Structure | Subtitle |
| `{start_of_verse}` / `{end_of_verse}` | `{sov}` / `{eov}` | Structure | Delimits a verse with automatic numbering |
| `{start_verse}` / `{end_verse}` | — | Structure | Alternative variant of start_of_verse |
| `{start_verse_num}` / `{end_verse_num}` | — | Structure | Verse with forced numbering |
| `{start_of_chorus}` / `{end_of_chorus}` | `{soc}` / `{eoc}` | Structure | Delimits a chorus |
| `{start_chorus}` / `{end_chorus}` | — | Structure | Alternative variant of start_of_chorus |
| `{start_of_bridge}` / `{end_of_bridge}` | `{sob}` / `{eob}` | Structure | Delimits a bridge |
| `{start_bridge}` / `{end_bridge}` | — | Structure | Alternative variant of start_of_bridge |
| `{start_chord}` / `{end_chord}` | — | Structure | Generic block with custom label |
| `{start_of_part}` / `{end_of_part}` | `{sop}` / `{eop}` | Structure | Generic ChordPro 6 section (not numbered) |
| `{verse: ...}` | — | Structure | Verse block with specific label |
| `{row}` | `{r}` | Structure | Blank separator row |
| `{new_song}` | — | Structure | Complete renderer reset |
| `{start_of_tab}` / `{end_of_tab}` | `{sot}` / `{eot}` | Tab/Grid | ASCII tablature block with monospace font |
| `{start_of_grid}` / `{end_of_grid}` | `{sog}` / `{eog}` | Tab/Grid | Chord grid block per bar |
| `{grid}` | — | Tab/Grid | Opens a grid block (synonym for `{sog}`) |
| `{comment: ...}` | `{c:}` | Annotations | Visible comment in normal style |
| `{comment_italic: ...}` | `{ci:}` | Annotations | Comment in italics |
| `{comment_box: ...}` | `{cb:}` | Annotations | Comment in a box |
| `{artist: ...}` | — | Metadata | Artist name |
| `{composer: ...}` | — | Metadata | Composer name |
| `{lyricist: ...}` | — | Metadata | Lyricist name — displayed with prefix "Lyrics:" |
| `{arranger: ...}` | — | Metadata | Arranger name — displayed with prefix "Arrangement:" |
| `{album: ...}` | — | Metadata | Album title |
| `{year: ...}` | — | Metadata | Year of publication |
| `{duration: ...}` | — | Metadata | Song duration (pure metadata, not displayed) |
| `{ccli: ...}` | — | Metadata | CCLI licence number |
| `{copyright: ...}` | — | Metadata | Copyright text |
| `{key: ...}` | — | Metadata | Song key |
| `{capo: N}` | — | Metadata | Capo position |
| `{new_page}` | `{np}` | Layout | Page break |
| `{column_break}` | `{colb}` | Layout | Column break |
| `{tempo: N}` | — | Musical | Tempo in BPM (quarter note) |
| `{tempo_m: N}` | — | Musical | Tempo in BPM (half note) |
| `{tempo_s: N}` | — | Musical | Tempo in BPM (quarter note, synonym) |
| `{tempo_c: N}` | — | Musical | Tempo in BPM (eighth note) |
| `{tempo_sp: N}` | — | Musical | Tempo in BPM (dotted quarter note) |
| `{tempo_cp: N}` | — | Musical | Tempo in BPM (dotted eighth note) |
| `{time: N/D}` | — | Musical | Time signature |
| `{beats_time: CH=N ...}` | — | Musical | Beat duration of chords on the next line |
| `{textsize: N}` | — | Text | Text font size |
| `{textfont: ...}` | — | Text | Text font |
| `{textcolour: ...}` | `{textcolor:}` | Text | Text colour |
| `{linespacing: N}` | — | Text | Extra line spacing |
| `{chordsize: N}` | — | Chords | Chord font size |
| `{chordfont: ...}` | — | Chords | Chord font |
| `{chordcolour: ...}` | `{chordcolor:}` | Chords | Chord colour |
| `{chordtopspacing: N}` | — | Chords | Space between chords and text |
| `{define: ...}` | — | Diagrams | Custom guitar chord diagram |
| `{taste: ...}` | — | Diagrams | Piano keyboard (Klavier) |
| `{fingering: ...}` | — | Diagrams | Piano keyboard with numbered fingering |
| `{image: ...}` | — | Images | Inserts an image |
| `[Chord]` | — | Inline chords | Chord positioned in the text |
| `# text` | — | Comments | Comment line (ignored) |
