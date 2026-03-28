# Songpress++

Songpress++ is a free and easy-to-use program for typesetting songs on Windows (and Linux), generating high-quality songbooks.

Songpress++ is focused on song formatting. Once the song is ready, you can copy/paste it into your favorite application to give your songbook the look you want. Alternatively, you can print it or create a "Song Book".

## Installation on Windows

## Prerequisites

Internet connection required to download the necessary Python packages!

### Python 3

Songpress++ requires **Python 3** installed on your system.

1. Download Python 3 from [https://www.python.org](https://www.python.org)
1. During installation, make sure to check **"Add Python to PATH"**
1. Complete the installation normally

### End Users

Download and run the `songpress-local-setup.exe` file. The installer (requires an internet connection) guides the user through the installation step by step. Available as either a portable or installable version.

All files are installed in a single folder within the current user's _User_ directory, allowing a clean uninstallation through its own uninstaller.

### Development

You can also download the entire package and launch src/Avvio SONGPRESS.vbs or Avvio SONGPRESS2.vbs

There are two differences, both significant:

1. Python detection

`Avvio SONGPRESS2.vbs`: uses a static array of hardcoded versions (3.4 → 3.14) and tries them one by one with RegRead. Simple but fragile — if Python 3.15 is released, it won't be found.
`Avvio SONGPRESS.vbs`: uses reg query to dynamically query the registry, finding any installed 3.x version without a hardcoded list. More robust. Uses **"Add Python to PATH"** to detect the version in use.

1. Error messages

`Avvio SONGPRESS2.vbs`: short, technical messages (shows the raw path), with no title in the window.
`Avvio SONGPRESS.vbs`: more user-friendly messages, with the title "Songpress - Startup Error" and, if Python is missing, suggests where to download it (python.org) and what to do during installation.

In summary: `Avvio SONGPRESS2.vbs` is the development/debug version, `Avvio SONGPRESS.vbs` is the polished end-user version.

## Installation on Linux

(Never tested)

## Installation on MAC

(Never tested)

## Languages Interface

- English
- Italian

## Main Features

- Production of **high-quality guitar charts** (lyrics and chords)
- **Easy** to learn, fast to use
- Ability to **paste formatted songs** into any Linux and Windows application to lay out the songbook with maximum flexibility (Affinity, Microsoft Word, LibreOffice, Microsoft Publisher, Inkscape, etc.)
- **Export** of formatted songs to PNG and HTML (web pages and fragments)
- **Chord transposition** with automatic key detection
- **Chord simplification** for beginner guitarists: identifies the easiest key to play and automatically transposes the song
- Support for various **chord notations**: American (C, D, E), Italian (Do, Re, Mi), French, German, and Portuguese; with notation conversion
- Support for **ChordPro and Tab** chord formats (on two lines)
- **Cleanup** of messy songs with spurious blank lines (such as those copied and pasted from web pages) and inconsistent chord notations
- **Print Preview** displays a print preview.
- **Print** allows you to print or export to PDF.
- **Create Songbook** allows you to create a collection in PDF format, with all the songs in a specific folder.
- **Other Commands** many new and interesting commands to discover.
- **Multi-Cursor Support** allows you to create and work with multiple cursors simultaneously.
- **Chord Positioning** displays chords either above or below the lyrics.
- **Window Position and Size** Saves and remembers the last position of the window.

## Change program name and version

![Songpress++ change name and version](src/songpress/img/GUIDE/Versione_en.png)

## Known Issues

### Linux: SVG export and display scaling

When the system display scale factor is not set to 1, the SVG output produced by the Copy as Image function may be incorrectly formatted. This is a known issue in the current version of wxPython. The underlying problem [has already been fixed upstream in wxWidgets](https://github.com/wxWidgets/wxWidgets/issues/25707) and will be automatically corrected as soon as the next version of wxPython is available.

## Credits

Songpress++ is a fork of Songpress by Luca Allulli - Skeed, maintained and extended by Denisov21.

- Original project website: <http://www.skeed.it/songpress>
- Fork repository: <https://github.com/Denisov21/Songpressplusplus>
