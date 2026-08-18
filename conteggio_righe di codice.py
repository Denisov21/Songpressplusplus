#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


# ============================================================
# CONFIGURAZIONE
# ============================================================

LANGUAGES = {
    # Linguaggi C-like
    ".c": "C",
    ".h": "C/C++ Header",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".hh": "C++ Header",
    ".hxx": "C++ Header",
    ".cs": "C#",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".scala": "Scala",
    ".dart": "Dart",
    ".groovy": "Groovy",
    ".m": "Objective-C",
    ".mm": "Objective-C++",

    # Scripting
    ".py": "Python",
    ".pyw": "Python",
    ".rb": "Ruby",
    ".php": "PHP",
    ".pl": "Perl",
    ".pm": "Perl",
    ".lua": "Lua",
    ".r": "R",
    ".R": "R",
    ".jl": "Julia",

    # JavaScript / Web
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".svelte": "Svelte",

    # Web
    ".html": "HTML",
    ".htm": "HTML",
    ".xhtml": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",

    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Fish",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    ".cmd": "Batch",

    # Database
    ".sql": "SQL",

    # Config / Data
    ".xml": "XML",
    ".xsl": "XML",
    ".xslt": "XML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",

    # Functional
    ".hs": "Haskell",
    ".lhs": "Haskell",
    ".fs": "F#",
    ".fsx": "F#",
    ".fsi": "F#",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",

    # Altri
    ".asm": "Assembly",
    ".s": "Assembly",
    ".sol": "Solidity",
    ".proto": "Protocol Buffers",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
}


# Directory che normalmente non contiene codice sorgente
DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".bzr",

    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",

    "node_modules",
    "bower_components",

    "venv",
    ".venv",
    "env",
    ".env",

    "build",
    "dist",
    "out",
    "target",

    ".idea",
    ".vscode",

    "coverage",
    ".coverage",

    "vendor",
    "packages",

    "bin",
    "obj",

    ".terraform",
    ".next",
    ".nuxt",
}


# ============================================================
# DEFINIZIONE DELLE REGOLE DEI LINGUAGGI
# ============================================================

LANGUAGE_RULES = {
    "C": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "C/C++ Header": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "C++": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "C++ Header": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "C#": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Java": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Kotlin": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Go": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Rust": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Swift": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Scala": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Dart": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Groovy": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Objective-C": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Objective-C++": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Python": {
        "line": ["#"],
        "block": [("'''", "'''"), ('"""', '"""')],
    },

    "Ruby": {
        "line": ["#"],
        "block": [("=begin", "=end")],
    },

    "PHP": {
        "line": ["//", "#"],
        "block": [("/*", "*/")],
    },

    "Perl": {
        "line": ["#"],
        "block": [],
    },

    "Lua": {
        "line": ["--"],
        "block": [("--[[", "]]")],
    },

    "R": {
        "line": ["#"],
        "block": [],
    },

    "Julia": {
        "line": ["#"],
        "block": [("#=", "=#")],
    },

    "JavaScript": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "TypeScript": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Vue": {
        "line": ["//"],
        "block": [("/*", "*/"), ("<!--", "-->")],
    },

    "Svelte": {
        "line": ["//"],
        "block": [("/*", "*/"), ("<!--", "-->")],
    },

    "HTML": {
        "line": [],
        "block": [("<!--", "-->")],
    },

    "CSS": {
        "line": [],
        "block": [("/*", "*/")],
    },

    "SCSS": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Sass": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Less": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Shell": {
        "line": ["#"],
        "block": [],
    },

    "Fish": {
        "line": ["#"],
        "block": [],
    },

    "PowerShell": {
        "line": ["#"],
        "block": [("<#", "#>")],
    },

    "Batch": {
        "line": ["REM ", "rem ", "::"],
        "block": [],
    },

    "SQL": {
        "line": ["--"],
        "block": [("/*", "*/")],
    },

    "XML": {
        "line": [],
        "block": [("<!--", "-->")],
    },

    "JSON": {
        "line": [],
        "block": [],
    },

    "YAML": {
        "line": ["#"],
        "block": [],
    },

    "TOML": {
        "line": ["#"],
        "block": [],
    },

    "Haskell": {
        "line": ["--"],
        "block": [("{-", "-}")],
    },

    "F#": {
        "line": ["//"],
        "block": [("(*", "*)")],
    },

    "Clojure": {
        "line": [";"],
        "block": [],
    },

    "ClojureScript": {
        "line": [";"],
        "block": [],
    },

    "Elixir": {
        "line": ["#"],
        "block": [],
    },

    "Erlang": {
        "line": ["%"],
        "block": [],
    },

    "Assembly": {
        "line": [";", "#"],
        "block": [],
    },

    "Solidity": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "Protocol Buffers": {
        "line": ["//"],
        "block": [("/*", "*/")],
    },

    "GraphQL": {
        "line": ["#"],
        "block": [('"""', '"""')],
    },
}


# ============================================================
# FUNZIONI DI SUPPORTO
# ============================================================

def is_binary(path):
    """
    Determina approssimativamente se un file è binario.
    """
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)

        if b"\x00" in chunk:
            return True

        return False

    except OSError:
        return True


def read_file(path):
    """
    Legge un file cercando di gestire diverse codifiche.
    """
    encodings = [
        "utf-8",
        "utf-8-sig",
        "latin-1",
        "cp1252",
    ]

    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
        except OSError:
            return None

    return None


def strip_strings(line):
    """
    Rimuove in modo approssimativo le stringhe da una riga.

    Serve a evitare casi come:

        print("Questo non è un // commento")

    """
    result = []
    i = 0
    quote = None
    escaped = False

    while i < len(line):
        char = line[i]

        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None

            result.append(" ")
            i += 1
            continue

        if char in ('"', "'"):
            quote = char
            result.append(" ")
            i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def classify_lines(lines, language):
    """
    Classifica le righe in:
        code
        comments
        blanks

    Una riga contenente sia codice sia commento viene
    considerata una riga di codice.
    """

    rules = LANGUAGE_RULES.get(
        language,
        {"line": [], "block": []}
    )

    line_comments = rules["line"]
    block_comments = rules["block"]

    code = 0
    comments = 0
    blanks = 0

    block_end = None

    for original_line in lines:

        if not original_line.strip():
            blanks += 1
            continue

        line = original_line.rstrip("\r\n")

        has_code = False
        has_comment = False

        i = 0

        while i < len(line):

            # ---------------------------------------------
            # Dentro un commento a blocco
            # ---------------------------------------------

            if block_end:
                end_pos = line.find(block_end, i)

                if end_pos == -1:
                    has_comment = True
                    i = len(line)
                    break

                has_comment = True
                i = end_pos + len(block_end)
                block_end = None
                continue

            # ---------------------------------------------
            # Ignora stringhe
            # ---------------------------------------------

            if line[i] in ('"', "'"):
                quote = line[i]

                # Triple quote
                if (
                    i + 2 < len(line)
                    and line[i:i + 3] == quote * 3
                ):
                    triple = quote * 3
                    end = line.find(triple, i + 3)

                    if end == -1:
                        block_end = triple
                        has_comment = True
                        i = len(line)
                        break

                    i = end + 3
                    has_code = True
                    continue

                i += 1

                while i < len(line):
                    if line[i] == "\\":
                        i += 2
                        continue

                    if line[i] == quote:
                        i += 1
                        break

                    i += 1

                has_code = True
                continue

            # ---------------------------------------------
            # Commenti a blocco
            # ---------------------------------------------

            found_block = False

            for start, end in block_comments:
                if line.startswith(start, i):

                    found_block = True
                    has_comment = True

                    end_pos = line.find(
                        end,
                        i + len(start)
                    )

                    if end_pos == -1:
                        block_end = end
                        i = len(line)
                        break

                    i = end_pos + len(end)
                    break

            if found_block:
                continue

            # ---------------------------------------------
            # Commenti a riga
            # ---------------------------------------------

            found_line_comment = False

            for marker in line_comments:

                if line.startswith(marker, i):

                    # Gestione REM: deve essere una parola
                    if marker.strip().lower() == "rem":
                        before = line[:i]

                        if before.strip():
                            has_code = True
                            i += 1
                            continue

                    has_comment = True
                    i = len(line)
                    found_line_comment = True
                    break

            if found_line_comment:
                break

            # ---------------------------------------------
            # Carattere normale
            # ---------------------------------------------

            if not line[i].isspace():
                has_code = True

            i += 1

        # ---------------------------------------------
        # Classificazione finale
        # ---------------------------------------------

        if has_code:
            code += 1
        elif has_comment:
            comments += 1
        else:
            blanks += 1

    return code, comments, blanks


# ============================================================
# ANALISI DEI FILE
# ============================================================

def analyze_file(path, language):
    """
    Analizza un singolo file.
    """

    if is_binary(path):
        return None

    lines = read_file(path)

    if lines is None:
        return None

    code, comments, blanks = classify_lines(
        lines,
        language
    )

    return {
        "code": code,
        "comments": comments,
        "blank": blanks,
        "total": len(lines),
    }


# ============================================================
# SCANSIONE CARTELLA
# ============================================================

def scan_directory(
    root,
    excluded_dirs,
    include_hidden=False,
):
    """
    Scansiona ricorsivamente una directory.
    """

    root = Path(root).resolve()

    results = defaultdict(
        lambda: {
            "files": 0,
            "code": 0,
            "comments": 0,
            "blank": 0,
            "total": 0,
        }
    )

    errors = []

    for current_root, dirs, files in os.walk(root):

        # ---------------------------------------------
        # Esclusione directory
        # ---------------------------------------------

        dirs[:] = [
            d for d in dirs
            if d not in excluded_dirs
            and (
                include_hidden
                or not d.startswith(".")
                or d in {".", ".."}
            )
        ]

        for filename in files:

            path = Path(current_root) / filename

            # -----------------------------------------
            # File nascosti
            # -----------------------------------------

            if (
                not include_hidden
                and filename.startswith(".")
            ):
                continue

            # -----------------------------------------
            # Estensione
            # -----------------------------------------

            suffix = path.suffix

            if suffix not in LANGUAGES:
                continue

            language = LANGUAGES[suffix]

            try:
                result = analyze_file(
                    path,
                    language
                )

                if result is None:
                    continue

                data = results[language]

                data["files"] += 1
                data["code"] += result["code"]
                data["comments"] += result["comments"]
                data["blank"] += result["blank"]
                data["total"] += result["total"]

            except Exception as e:
                errors.append(
                    f"{path}: {e}"
                )

    return results, errors


# ============================================================
# OUTPUT TABELLA
# ============================================================

def print_table(results):
    """
    Stampa una tabella simile a cloc.
    """

    rows = []

    for language, data in results.items():
        rows.append(
            (
                language,
                data["files"],
                data["blank"],
                data["comments"],
                data["code"],
                data["total"],
            )
        )

    rows.sort(
        key=lambda x: x[4],
        reverse=True
    )

    total_files = sum(x[1] for x in rows)
    total_blank = sum(x[2] for x in rows)
    total_comments = sum(x[3] for x in rows)
    total_code = sum(x[4] for x in rows)
    total_lines = sum(x[5] for x in rows)

    headers = [
        "Language",
        "Files",
        "Blank",
        "Comment",
        "Code",
        "Total",
    ]

    widths = [
        max(
            len(headers[0]),
            *(len(str(x[0])) for x in rows)
        ) if rows else len(headers[0]),

        max(
            len(headers[1]),
            *(len(str(x[1])) for x in rows)
        ) if rows else len(headers[1]),

        max(
            len(headers[2]),
            *(len(str(x[2])) for x in rows)
        ) if rows else len(headers[2]),

        max(
            len(headers[3]),
            *(len(str(x[3])) for x in rows)
        ) if rows else len(headers[3]),

        max(
            len(headers[4]),
            *(len(str(x[4])) for x in rows)
        ) if rows else len(headers[4]),

        max(
            len(headers[5]),
            *(len(str(x[5])) for x in rows)
        ) if rows else len(headers[5]),
    ]

    print()
    print(
        "Language".ljust(widths[0]),
        "Files".rjust(widths[1]),
        "Blank".rjust(widths[2]),
        "Comment".rjust(widths[3]),
        "Code".rjust(widths[4]),
        "Total".rjust(widths[5]),
    )

    print("-" * (sum(widths) + 5 * 2))

    for row in rows:
        print(
            str(row[0]).ljust(widths[0]),
            str(row[1]).rjust(widths[1]),
            str(row[2]).rjust(widths[2]),
            str(row[3]).rjust(widths[3]),
            str(row[4]).rjust(widths[4]),
            str(row[5]).rjust(widths[5]),
        )

    print("-" * (sum(widths) + 5 * 2))

    print(
        "SUM".ljust(widths[0]),
        str(total_files).rjust(widths[1]),
        str(total_blank).rjust(widths[2]),
        str(total_comments).rjust(widths[3]),
        str(total_code).rjust(widths[4]),
        str(total_lines).rjust(widths[5]),
    )

    print()


# ============================================================
# OUTPUT JSON
# ============================================================

def export_json(results, output):
    """
    Esporta i risultati in JSON.
    """

    total = {
        "files": sum(
            x["files"] for x in results.values()
        ),
        "blank": sum(
            x["blank"] for x in results.values()
        ),
        "comments": sum(
            x["comments"] for x in results.values()
        ),
        "code": sum(
            x["code"] for x in results.values()
        ),
        "total": sum(
            x["total"] for x in results.values()
        ),
    }

    data = {
        "languages": dict(results),
        "total": total,
    }

    with open(
        output,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# OUTPUT CSV
# ============================================================

def export_csv(results, output):
    """
    Esporta i risultati in CSV.
    """

    with open(
        output,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "Language",
            "Files",
            "Blank",
            "Comments",
            "Code",
            "Total",
        ])

        for language, data in sorted(
            results.items()
        ):
            writer.writerow([
                language,
                data["files"],
                data["blank"],
                data["comments"],
                data["code"],
                data["total"],
            ])


# ============================================================
# ARGOMENTI COMMAND LINE
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Piccolo clone di cloc scritto in Python. "
            "Conta file, righe di codice, commenti e righe vuote."
        )
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Cartella da analizzare (default: .)",
    )

    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help=(
            "Directory aggiuntive da escludere. "
            "Esempio: --exclude test docs tmp"
        ),
    )

    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include file e directory nascosti.",
    )

    parser.add_argument(
        "--json",
        metavar="FILE",
        help="Esporta i risultati in JSON.",
    )

    parser.add_argument(
        "--csv",
        metavar="FILE",
        help="Esporta i risultati in CSV.",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Non mostra la tabella a video.",
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():
    args = parse_args()

    root = Path(args.directory)

    if not root.exists():
        print(
            f"Errore: la cartella '{root}' non esiste.",
            file=sys.stderr,
        )
        return 1

    if not root.is_dir():
        print(
            f"Errore: '{root}' non è una cartella.",
            file=sys.stderr,
        )
        return 1

    excluded = set(DEFAULT_EXCLUDED_DIRS)
    excluded.update(args.exclude)

    print(f"Analisi di: {root.resolve()}")

    results, errors = scan_directory(
        root,
        excluded,
        args.include_hidden,
    )

    if not results:
        print(
            "\nNessun file di codice riconosciuto."
        )
        return 0

    if not args.quiet:
        print_table(results)

    if args.json:
        export_json(
            results,
            args.json
        )
        print(
            f"JSON salvato in: {args.json}"
        )

    if args.csv:
        export_csv(
            results,
            args.csv
        )
        print(
            f"CSV salvato in: {args.csv}"
        )

    if errors:
        print(
            f"\nFile non analizzati: {len(errors)}",
            file=sys.stderr,
        )

        for error in errors[:10]:
            print(
                f"  {error}",
                file=sys.stderr,
            )

        if len(errors) > 10:
            print(
                f"  ... e altri {len(errors) - 10}",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())