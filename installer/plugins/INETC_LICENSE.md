# INetC NSIS Plugin — License and Usage

## Information

| Field       | Value |
|-------------|-------|
| Name        | Inetc plug-in |
| Author      | Takhir |
| Later versions | v1.0.4.4 Stuart "Afrow UK" Welch · v1.0.5.0–1.0.5.3 Anders |
| License     | zlib/libpng |
| Official download | https://nsis.sourceforge.io/mediawiki/images/c/c9/Inetc.zip (81 KB) |
| Wiki page   | https://nsis.sourceforge.io/Inetc_plug-in |
| Fork with custom colors | https://github.com/DigitalMediaServer/NSIS-INetC-plugin/releases |

---

## License (zlib/libpng)

```
INetC NSIS plug-in
Copyright (c) Takhir, Stuart "Afrow UK" Welch, Anders

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.

2. Altered source versions must be plainly marked as such, and must not
   be misrepresented as being the original software.

3. This notice may not be removed or altered from any source distribution.
```

> The zlib license is compatible with GNU GPL v2 (the license of Songpress++).
> INetC is used **by the installer only** and is not distributed with the
> application: NSIS temporarily extracts it to `$PLUGINSDIR` during
> installation, after which it is removed automatically.

---

## Installing the plugin in the project

Extract `INetC.dll` from the zip archive, from the `Plugins\x86-unicode\`
folder, and place it here:

```
installer/
└── plugins/
    └── INetC.dll    ← x86-unicode build
```

Add the following line to the `.nsi` file, **before** `!include "MUI2.nsh"`:

```nsi
!addplugindir /x86-unicode "plugins"
```

This line is already present in the project's `songpress++.nsi` file.

---

## Available commands

### `inetc::get` — File download

```nsi
inetc::get [options] URL local_file [URL2 local_file2 ...] [/END]
Pop $0  ; "OK" or error string
```

**Main options:**

| Option | Description |
|--------|-------------|
| `/SILENT` | Hides progress bar and popup |
| `/CONNECTTIMEOUT seconds` | Connection timeout (default: current IE value) |
| `/RECEIVETIMEOUT seconds` | Receive timeout |
| `/NOPROXY` | Disables proxy for this connection |
| `/PROXY IP:PORT` | Explicit proxy address |
| `/USERNAME login /PASSWORD pwd` | Proxy credentials |
| `/NOCANCEL` | Prevents the user from cancelling the download |
| `/WEAKSECURITY` | Ignores unknown or revoked certificates |
| `/POPUP alias` | Shows a detailed popup progress dialog |
| `/BANNER text` | Shows a simple popup banner (MSI style) |
| `/USERAGENT text` | Sets the HTTP User-Agent header |
| `/HEADER text` | Adds or replaces an HTTP request header |
| `/TOSTACK` | Writes the response to the NSIS stack instead of a file |
| `/TOSTACKCONV` | Like `/TOSTACK` but with encoding conversion |
| `/RESUME question` | On error, shows a retry dialog with the given question text |

---

### `inetc::head` — HTTP headers only (used in Songpress++)

```nsi
inetc::head [options] URL local_file
Pop $0  ; "OK" or error string
```

Same as `get` but retrieves **HTTP headers only**, without downloading the
response body. Much faster — ideal for connectivity checks.
Supports the same options as `get`.

**Usage in Songpress++:**

```nsi
inetc::head /SILENT /CONNECTTIMEOUT 5000 "https://pypi.org/"
Pop $0
${If} $0 == "OK"
    ; connection OK
${Else}
    ; $0 contains the error description
${EndIf}
```

---

### `inetc::post` — HTTP POST upload

```nsi
inetc::post text_to_post [options] URL response_file
Pop $0
```

Sets HTTP POST mode. The `/FILE` option allows sending the contents of a file
instead of a plain string.

---

### `inetc::put` — HTTP PUT upload

```nsi
inetc::put [options] URL local_file [URL2 local_file2 ...] [/END]
Pop $0
```

---

## Return values

All functions push a result onto the NSIS stack:

| Value | Meaning |
|-------|---------|
| `"OK"` | Operation succeeded |
| any other string | Error description (e.g. `"Host not found"`, `"Connection refused"`, `"SSL error"`) |
