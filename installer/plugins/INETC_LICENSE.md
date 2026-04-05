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

---

## Current usage in Songpress++

**INetC is no longer used.** Both installers now use **NScurl**, which is bundled
with NSIS by default (both amd64-unicode and x86-unicode). No external DLL is required.

| Installer | Plugin | External DLL |
|-----------|--------|--------------|
| **64-bit** (`songpressx64.nsi`) | NScurl (built-in NSIS) | none |
| **32-bit** (`songpressx86.nsi`) | NScurl (built-in NSIS) | none |

INetC was previously used for the internet connection check, but was replaced by NScurl
because it is already included in NSIS, works identically on both 32-bit and 64-bit,
and requires no extra files in the project.

The `plugins/` folder and `!addplugindir` directives have been removed from both scripts.

---

## NScurl — replacement syntax

```nsi
NScurl::http GET "http://1.1.1.1/" "$INSTDIR\nettest.tmp" /TIMEOUT 10000 /END
Pop $0   ; "OK" or error string
Delete "$INSTDIR\nettest.tmp"

${If} $0 == "OK"
    ; connection OK
${Else}
    ; $0 contains the error description
${EndIf}
```

---

## INetC command reference (kept for historical reference)

### `inetc::get` — File download

```nsi
inetc::get [options] URL local_file [URL2 local_file2 ...] [/END]
Pop $0  ; "OK" or error string
```

| Option | Description |
|--------|-------------|
| `/SILENT` | Hides progress bar and popup |
| `/CONNECTTIMEOUT seconds` | Connection timeout |
| `/RECEIVETIMEOUT seconds` | Receive timeout |
| `/NOPROXY` | Disables proxy |
| `/PROXY IP:PORT` | Explicit proxy address |
| `/NOCANCEL` | Prevents cancellation |
| `/WEAKSECURITY` | Ignores unknown/revoked certificates |
| `/TOSTACK` | Writes response to NSIS stack |
| `/RESUME question` | Retry dialog on error |

### `inetc::head` — HTTP headers only

Same as `get` but downloads headers only. Unreliable on Windows 10/11 —
use `inetc::get` or NScurl instead.

---

## Return values (both INetC and NScurl)

| Value | Meaning |
|-------|---------|
| `"OK"` | Operation succeeded |
| any other string | Error description (e.g. `"Host not found"`, `"Connection refused"`) |
