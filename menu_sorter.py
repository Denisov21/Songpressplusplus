#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
menu_sorter.py  –  Ordina voci di menu in file XRC e FBP
Autore: Denisov21  |  2026
"""

import wx
import wx.lib.scrolledpanel as scrolled
import xml.etree.ElementTree as ET
import re
import os
import shutil
import io
import json as _json
import sys as _sys
from dataclasses import dataclass, field
from typing import List, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Colori di default (costanti) e infrastruttura colori dinamici
# ──────────────────────────────────────────────────────────────────────────────

DARK_BG      = "#1E1E2E"
PANEL_BG     = "#252538"
ACCENT       = "#7C6AF7"
ACCENT_LIGHT = "#A89EFF"
TEXT_MAIN    = "#CDD6F4"
TEXT_DIM     = "#00FFFF"
SUCCESS      = "#A6E3A1"
WARNING      = "#F9E2AF"
BORDER       = "#45475A"

_COLORS_DEFAULT: dict = {
    "DARK_BG":      DARK_BG,
    "PANEL_BG":     PANEL_BG,
    "ACCENT":       ACCENT,
    "ACCENT_LIGHT": ACCENT_LIGHT,
    "TEXT_MAIN":    TEXT_MAIN,
    "TEXT_DIM":     TEXT_DIM,
    "SUCCESS":      SUCCESS,
    "WARNING":      WARNING,
}

def _colors_path() -> str:
    if getattr(_sys, "frozen", False):
        base = os.path.dirname(_sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "menu_sorter_colors.json")

def _load_colors() -> dict:
    path = _colors_path()
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = _json.load(f)
            merged = dict(_COLORS_DEFAULT)
            merged.update({k: v for k, v in saved.items() if k in merged})
            return merged
        except Exception:
            pass
    return dict(_COLORS_DEFAULT)

def _save_colors(colors: dict) -> None:
    try:
        with open(_colors_path(), "w", encoding="utf-8") as f:
            _json.dump(colors, f, indent=2)
    except Exception:
        pass

_colors: dict = _load_colors()


# ──────────────────────────────────────────────────────────────────────────────
# Strutture dati
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class MenuGroup:
    """Un gruppo di voci separate da separatori."""
    items: list = field(default_factory=list)      # elementi XML (ET.Element)
    separators_before: int = 0                      # separatori prima del gruppo


@dataclass
class MenuInfo:
    """Rappresenta un menu riconosciuto nel file."""
    name: str                                       # nome/label del menu
    path: str                                       # percorso XPath-like per display
    element: ET.Element                             # ET.Element del <object class="wxMenu">
    parent_element: ET.Element | None               # genitore diretto
    file_type: str                                  # "xrc" o "fbp"
    groups: List[MenuGroup] = field(default_factory=list)
    trailing_sep: bool = False                      # separatore finale dopo l'ultimo item


# ──────────────────────────────────────────────────────────────────────────────
# Parser XRC
# ──────────────────────────────────────────────────────────────────────────────

def parse_xrc(filepath: str) -> Tuple[List[MenuInfo], ET.ElementTree]:
    tree = ET.parse(filepath)
    root = tree.getroot()
    menus: List[MenuInfo] = []

    def label_of(el) -> str:
        lbl = el.find("label")
        if lbl is not None and lbl.text:
            return lbl.text.replace("&", "").strip()
        name_attr = el.get("name", "")
        return name_attr if name_attr else "(senza nome)"

    def extract_groups(menu_el):
        """Divide le voci figlie in gruppi separati da <object class='separator'>."""
        groups: List[MenuGroup] = []
        current = MenuGroup()
        trailing_sep = False
        for child in list(menu_el):
            cls = child.get("class", "")
            if cls == "separator":
                if current.items:
                    groups.append(current)
                current = MenuGroup(separators_before=1)
                trailing_sep = True
            elif cls in ("wxMenuItem", "wxMenu"):
                current.items.append(child)
                trailing_sep = False
        if current.items:
            groups.append(current)
        return groups, trailing_sep

    def walk(el, parent, depth=0, path=""):
        cls = el.get("class", "")
        lbl = label_of(el)
        cur_path = f"{path} > {lbl}" if path else lbl

        if cls == "wxMenu":
            groups, trailing_sep = extract_groups(el)
            mi = MenuInfo(
                name=lbl,
                path=cur_path,
                element=el,
                parent_element=parent,
                file_type="xrc",
                groups=groups,
                trailing_sep=trailing_sep,
            )
            menus.append(mi)

        for child in list(el):
            walk(child, el, depth + 1, cur_path if cls == "wxMenu" else path)

    walk(root, None)
    return menus, tree


def _tag_local(child) -> str:
    """Nome locale del tag, senza namespace."""
    t = child.tag
    return t.split("}")[-1] if "}" in t else t


def apply_sort_xrc(menu_info: MenuInfo, group_indices: List[int]):
    """Ordina i gruppi selezionati e riscrive il contenuto del menu_info.element."""
    el = menu_info.element

    # Salva i figli non-<object> (es. <label> del menu) prima di rimuovere tutto
    non_obj = [c for c in list(el) if _tag_local(c) != "object"]
    # Recupera flag separatore finale dalla MenuInfo
    trailing_sep = menu_info.trailing_sep

    # Rimuovi tutti i figli
    for child in list(el):
        el.remove(child)

    # Reinserisci prima i figli non-object (es. <label>)
    for child in non_obj:
        el.append(child)

    # Ricostruisci gruppi: separatore tra gruppi + voci ordinate
    for i, group in enumerate(menu_info.groups):
        if i > 0:
            sep = ET.SubElement(el, "object")
            sep.set("class", "separator")
        if i in group_indices:
            sorted_items = sorted(group.items, key=label_of_item)
            group.items[:] = sorted_items          # ← aggiorna lista in-place
        else:
            sorted_items = group.items
        for item in sorted_items:
            el.append(item)

    # Ripristina separatore finale se presente nell'originale
    if trailing_sep:
        sep = ET.SubElement(el, "object")
        sep.set("class", "separator")


_XRC_NS = "http://www.wxwidgets.org/wxxrc"

def label_of_item(el) -> str:
    """Chiave di ordinamento: testo senza mnemonico, lowercase."""
    # Cerca <label> con e senza namespace XRC
    lbl = el.find("label") or el.find(f"{{{_XRC_NS}}}label")
    if lbl is not None and lbl.text:
        text = lbl.text.replace("&", "").replace("\t", " ").strip()
        text = re.sub(r"_([^ ])", r"\1", text)  # "E_xport" -> "Export"
        text = text.replace("_", "")
        return text.lower()
    return el.get("name", "").lower()


def display_label_xrc(el) -> str:
    """Etichetta leggibile per la GUI: testo originale senza solo il char mnemonico."""
    lbl = el.find("label") or el.find(f"{{{_XRC_NS}}}label")
    if lbl is not None and lbl.text:
        text = lbl.text.replace("&", "").replace("\t", " ").strip()
        text = re.sub(r"_([^ ])", r"\1", text)
        text = text.replace("_", "")
        return text  # mantiene maiuscole per la GUI
    return el.get("name", el.get("label", ""))


def display_label_fbp(el) -> str:
    """Etichetta leggibile per la GUI (FBP)."""
    for prop in el.findall("property"):
        if prop.get("name") == "label" and prop.text:
            return prop.text.replace("&", "").replace("\t", " ").strip()
    return el.get("name", "")


# ──────────────────────────────────────────────────────────────────────────────
# Parser FBP
# ──────────────────────────────────────────────────────────────────────────────

def parse_fbp(filepath: str) -> Tuple[List[MenuInfo], ET.ElementTree]:
    """
    wxFormBuilder usa XML con struttura <object class="wxMenuBar"> /
    <object class="wxMenu"> / <object class="wxMenuItem"> / <object class="separator">
    Stessa logica di XRC.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()
    menus: List[MenuInfo] = []

    def label_of(el) -> str:
        for prop in el.findall("property"):
            if prop.get("name") in ("label", "title"):
                if prop.text:
                    return prop.text.replace("&", "").strip()
        return el.get("name", "(senza nome)")

    def extract_groups(menu_el) -> List[MenuGroup]:
        groups: List[MenuGroup] = []
        current = MenuGroup()
        for child in list(menu_el):
            if child.tag != "object":
                continue
            cls = child.get("class", "")
            if cls == "separator":
                if current.items:
                    groups.append(current)
                current = MenuGroup(separators_before=1)
            elif cls in ("wxMenuItem", "wxMenu"):
                current.items.append(child)
        if current.items:
            groups.append(current)
        return groups

    def walk(el, parent, path=""):
        cls = el.get("class", "")
        lbl = label_of(el)
        cur_path = f"{path} > {lbl}" if path else lbl

        if cls == "wxMenu":
            groups = extract_groups(el)
            mi = MenuInfo(
                name=lbl,
                path=cur_path,
                element=el,
                parent_element=parent,
                file_type="fbp",
                groups=groups,
            )
            menus.append(mi)

        for child in list(el):
            if child.tag == "object":
                walk(child, el, cur_path if cls == "wxMenu" else path)

    walk(root, None)
    return menus, tree


def label_of_item_fbp(el) -> str:
    for prop in el.findall("property"):
        if prop.get("name") == "label":
            if prop.text:
                # Rimuove solo il char mnemonico & (non tutto ciò che segue)
                text = prop.text.replace("&", "").replace("\t", " ").strip()
                return text.lower()
    return el.get("name", "").lower()


def apply_sort_fbp(menu_info: MenuInfo, group_indices: List[int]):
    el = menu_info.element
    # Rimuovi solo i figli <object>
    for child in list(el):
        if child.tag == "object":
            el.remove(child)

    for i, group in enumerate(menu_info.groups):
        if i > 0:
            sep = ET.SubElement(el, "object")
            sep.set("class", "separator")
        if i in group_indices:
            sorted_items = sorted(group.items, key=label_of_item_fbp)
            group.items[:] = sorted_items          # ← aggiorna lista in-place
        else:
            sorted_items = group.items
        for item in sorted_items:
            el.append(item)


# ──────────────────────────────────────────────────────────────────────────────
# Salvataggio con backup
# ──────────────────────────────────────────────────────────────────────────────

def save_tree(filepath: str, tree: ET.ElementTree):
    backup = filepath + ".bak"
    shutil.copy2(filepath, backup)

    # Leggi la dichiarazione originale per preservare standalone="yes"
    # e i line endings (\r\n per FBP, \n per XRC)
    with open(filepath, "rb") as f:
        raw_orig = f.read(512)
    newline = "\r\n" if b"\r\n" in raw_orig else "\n"
    first_line = raw_orig.split(b"\n")[0].decode("utf-8", errors="replace").strip()
    if first_line.startswith("<?xml"):
        decl = re.sub(r'encoding=["\'].*?["\']', 'encoding="UTF-8"', first_line)
        xml_decl = decl if decl.endswith("?>") else decl.rstrip("> ").rstrip() + "?>"
    else:
        xml_decl = '<?xml version="1.0" encoding="UTF-8"?>'

    # Non usare ET.indent() (corrompe i text-node) né xml_declaration=True
    # (ET scrive encoding minuscolo rifiutato da wxXmlResource)
    # register_namespace qui garantisce che XRC non usi il prefisso ns0:
    ET.register_namespace("", "http://www.wxwidgets.org/wxxrc")
    buf = io.BytesIO()
    tree.write(buf, encoding="utf-8", xml_declaration=False)
    xml_body = buf.getvalue().decode("utf-8")

    with open(filepath, "w", encoding="utf-8", newline=newline) as f:
        f.write(xml_decl + "\n")
        f.write(xml_body)
        if not xml_body.endswith("\n"):
            f.write("\n")

    return backup


# ──────────────────────────────────────────────────────────────────────────────
# Dialog Opzioni – colori interfaccia
# ──────────────────────────────────────────────────────────────────────────────

_COLOR_LABELS = {
    "DARK_BG":      "Sfondo principale",
    "PANEL_BG":     "Sfondo pannelli",
    "ACCENT":       "Colore accento (pulsanti)",
    "ACCENT_LIGHT": "Accento chiaro (titoli)",
    "TEXT_MAIN":    "Testo principale",
    "TEXT_DIM":     "Testo secondario",
    "SUCCESS":      "Colore successo",
    "WARNING":      "Colore avviso",
}

class OptionsDialog(wx.Dialog):
    def __init__(self, parent: wx.Window):
        super().__init__(parent, title="Opzioni – Colori interfaccia",
                         size=(480, 420), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._pickers: dict[str, wx.ColourPickerCtrl] = {}
        self._build()
        self.Centre()

    def _build(self) -> None:
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ── Griglia colori ────────────────────────────────────────────────────
        grid = wx.FlexGridSizer(cols=3, vgap=8, hgap=10)
        grid.AddGrowableCol(1, 1)

        for key, label in _COLOR_LABELS.items():
            lbl = wx.StaticText(self, label=label)
            current = _colors.get(key, "#FFFFFF")
            picker = wx.ColourPickerCtrl(self, colour=wx.Colour(current))
            self._pickers[key] = picker
            preview = wx.Panel(self, size=(24, 24))
            preview.SetBackgroundColour(wx.Colour(current))
            picker.Bind(wx.EVT_COLOURPICKER_CHANGED,
                        lambda e, p=preview, pk=picker: self._on_color_changed(e, p, pk))
            grid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(picker, 0, wx.EXPAND)
            grid.Add(preview, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 12)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        # ── Pulsanti OK / Annulla ─────────────────────────────────────────────
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        btn_row.AddStretchSpacer()
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Annulla")
        btn_ok     = wx.Button(self, wx.ID_OK,     label="OK")
        btn_ok.Bind(wx.EVT_BUTTON, self._on_ok)
        btn_row.Add(btn_cancel, 0, wx.RIGHT, 6)
        btn_row.Add(btn_ok, 0)
        sizer.Add(btn_row, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer)

    def _on_color_changed(self, _evt: wx.Event, preview: wx.Panel,
                          picker: wx.ColourPickerCtrl) -> None:
        preview.SetBackgroundColour(picker.GetColour())
        preview.Refresh()

    def _on_ok(self, _evt: wx.Event) -> None:
        for key, picker in self._pickers.items():
            _colors[key] = picker.GetColour().GetAsString(wx.C2S_HTML_SYNTAX)
        _save_colors(_colors)
        self.EndModal(wx.ID_OK)






class MenuSorterApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None)
        frame.Show()
        self.SetTopWindow(frame)
        return True


class MainFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title="Menu Sorter – XRC / FBP", size=(900, 700))
        self.SetMinSize((700, 500))
        self._filepath: str | None = None
        self._menus: List[MenuInfo] = []
        self._tree: ET.ElementTree | None = None
        self._file_type: str | None = None

        self._build_ui()
        self._apply_colors()
        self.Centre()

    # ── costruzione UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        self.SetBackgroundColour(_colors["DARK_BG"])

        # ── Barra dei menu ────────────────────────────────────────────────────
        menubar = wx.MenuBar()

        # Menu File
        file_menu = wx.Menu()
        item_open = file_menu.Append(wx.ID_OPEN, "Apri…\tCtrl+O", "Apri un file XRC o FBP")
        file_menu.AppendSeparator()
        item_opts = file_menu.Append(wx.ID_PREFERENCES, "Opzioni…\tCtrl+,", "Modifica i colori dell'interfaccia")
        file_menu.AppendSeparator()
        item_exit = file_menu.Append(wx.ID_EXIT, "Esci\tAlt+F4", "Chiudi il programma")
        menubar.Append(file_menu, "&File")

        # Menu Guida
        help_menu = wx.Menu()
        item_credits = help_menu.Append(wx.ID_ABOUT, "Crediti…", "Informazioni sull'autore")
        menubar.Append(help_menu, "&Guida")

        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self._on_open, item_open)
        self.Bind(wx.EVT_MENU, self._on_options, item_opts)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), item_exit)
        self.Bind(wx.EVT_MENU, self._on_credits, item_credits)

        root_sizer = wx.BoxSizer(wx.VERTICAL)

        # ── Intestazione ──────────────────────────────────────────────────────
        self._header = wx.Panel(self)
        self._header.SetBackgroundColour(_colors["PANEL_BG"])
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._title_lbl = wx.StaticText(self._header, label="⟡  Menu Sorter")
        self._title_lbl.SetForegroundColour(_colors["ACCENT_LIGHT"])
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                             wx.FONTWEIGHT_BOLD)
        self._title_lbl.SetFont(title_font)

        self._sub_lbl = wx.StaticText(self._header, label="Ordina voci di menu in file XRC e FBP")
        self._sub_lbl.SetForegroundColour(_colors["TEXT_DIM"])

        h_sizer.Add(self._title_lbl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 12)
        h_sizer.Add(self._sub_lbl, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 8)
        self._header.SetSizer(h_sizer)
        root_sizer.Add(self._header, 0, wx.EXPAND)

        # ── Riga file ─────────────────────────────────────────────────────────
        self._file_panel = wx.Panel(self)
        self._file_panel.SetBackgroundColour(_colors["DARK_BG"])
        fp_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._file_lbl = wx.TextCtrl(self._file_panel, style=wx.TE_READONLY,
                                     value="Nessun file aperto…")
        self._file_lbl.SetBackgroundColour(_colors["PANEL_BG"])
        self._file_lbl.SetForegroundColour(_colors["TEXT_DIM"])

        self._btn_open = wx.Button(self._file_panel, label="📂  Apri file…")
        self._style_btn(self._btn_open, _colors["ACCENT"])
        self._btn_open.Bind(wx.EVT_BUTTON, self._on_open)

        fp_sizer.Add(self._file_lbl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 8)
        fp_sizer.Add(self._btn_open, 0, wx.RIGHT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 8)
        self._file_panel.SetSizer(fp_sizer)
        root_sizer.Add(self._file_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 4)

        # ── Splitter: albero menu | dettaglio gruppi ──────────────────────────
        self._splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self._splitter.SetBackgroundColour(_colors["DARK_BG"])

        # Pannello sinistro – lista menu rilevati
        self._left = wx.Panel(self._splitter)
        self._left.SetBackgroundColour(_colors["PANEL_BG"])
        l_sizer = wx.BoxSizer(wx.VERTICAL)

        self._lbl_l = wx.StaticText(self._left, label="Menu rilevati")
        self._lbl_l.SetForegroundColour(_colors["ACCENT_LIGHT"])
        self._lbl_l.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_BOLD))
        l_sizer.Add(self._lbl_l, 0, wx.ALL, 8)

        self._menu_list = wx.ListBox(self._left, style=wx.LB_SINGLE)
        self._menu_list.SetBackgroundColour(_colors["DARK_BG"])
        self._menu_list.SetForegroundColour(_colors["TEXT_MAIN"])
        self._menu_list.Bind(wx.EVT_LISTBOX, self._on_menu_select)
        l_sizer.Add(self._menu_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self._left.SetSizer(l_sizer)

        # Pannello destro – gruppi + voci
        self._right = wx.Panel(self._splitter)
        self._right.SetBackgroundColour(_colors["PANEL_BG"])
        r_sizer = wx.BoxSizer(wx.VERTICAL)

        self._lbl_r = wx.StaticText(self._right, label="Gruppi e voci del menu selezionato")
        self._lbl_r.SetForegroundColour(_colors["ACCENT_LIGHT"])
        self._lbl_r.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_BOLD))
        r_sizer.Add(self._lbl_r, 0, wx.ALL, 8)

        self._scroll = scrolled.ScrolledPanel(self._right)
        self._scroll.SetBackgroundColour(_colors["DARK_BG"])
        self._scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self._scroll.SetSizer(self._scroll_sizer)
        self._scroll.SetupScrolling()
        r_sizer.Add(self._scroll, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self._right.SetSizer(r_sizer)

        self._splitter.SplitVertically(self._left, self._right, 260)
        root_sizer.Add(self._splitter, 1, wx.EXPAND | wx.ALL, 6)

        # ── Barra inferiore ───────────────────────────────────────────────────
        self._bar = wx.Panel(self)
        self._bar.SetBackgroundColour(_colors["PANEL_BG"])
        b_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._status_lbl = wx.StaticText(self._bar, label="Apri un file XRC o FBP per iniziare.")
        self._status_lbl.SetForegroundColour(_colors["TEXT_DIM"])

        b_sizer.Add(self._status_lbl, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 8)

        self._btn_sort_sel = wx.Button(self._bar, label="↕  Ordina selezionati")
        self._btn_sort_all = wx.Button(self._bar, label="↕↕  Ordina tutti i menu")
        self._btn_save     = wx.Button(self._bar, label="💾  Salva (+ backup)")

        self._style_btn(self._btn_sort_sel, _colors["ACCENT"])
        self._style_btn(self._btn_sort_all, _colors["ACCENT"])
        self._style_btn(self._btn_save,     _colors["SUCCESS"])

        self._btn_sort_sel.Bind(wx.EVT_BUTTON, self._on_sort_selected)
        self._btn_sort_all.Bind(wx.EVT_BUTTON, self._on_sort_all)
        self._btn_save.Bind(wx.EVT_BUTTON, self._on_save)

        b_sizer.Add(self._btn_sort_sel, 0, wx.ALL, 6)
        b_sizer.Add(self._btn_sort_all, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 6)
        b_sizer.Add(self._btn_save,    0, wx.TOP | wx.BOTTOM | wx.RIGHT, 6)
        self._bar.SetSizer(b_sizer)
        root_sizer.Add(self._bar, 0, wx.EXPAND)

        self.SetSizer(root_sizer)

        # stato interno checkbox per i gruppi
        self._group_checks: List[wx.CheckBox] = []

    def _style_btn(self, btn: wx.Button, bg: str):
        btn.SetBackgroundColour(bg)
        btn.SetForegroundColour("#FFFFFF")

    def _apply_colors(self):
        bg   = _colors["DARK_BG"]
        pan  = _colors["PANEL_BG"]
        txt  = _colors["TEXT_MAIN"]
        dim  = _colors["TEXT_DIM"]
        acc  = _colors["ACCENT"]
        accl = _colors["ACCENT_LIGHT"]
        suc  = _colors["SUCCESS"]

        # Frame
        self.SetBackgroundColour(bg)

        # Intestazione
        self._header.SetBackgroundColour(pan)
        self._title_lbl.SetForegroundColour(accl)
        self._sub_lbl.SetForegroundColour(dim)

        # Riga file
        self._file_panel.SetBackgroundColour(bg)
        self._file_lbl.SetBackgroundColour(pan)
        self._file_lbl.SetForegroundColour(dim)
        self._style_btn(self._btn_open, acc)

        # Splitter
        self._splitter.SetBackgroundColour(bg)

        # Pannello sinistro
        self._left.SetBackgroundColour(pan)
        self._lbl_l.SetForegroundColour(accl)
        self._menu_list.SetBackgroundColour(bg)
        self._menu_list.SetForegroundColour(txt)

        # Pannello destro
        self._right.SetBackgroundColour(pan)
        self._lbl_r.SetForegroundColour(accl)
        self._scroll.SetBackgroundColour(bg)

        # Barra inferiore
        self._bar.SetBackgroundColour(pan)
        self._status_lbl.SetForegroundColour(dim)
        self._style_btn(self._btn_sort_sel, acc)
        self._style_btn(self._btn_sort_all, acc)
        self._style_btn(self._btn_save,     suc)

        # Aggiorna anche i widget dinamici nel pannello scroll (gruppi)
        idx = self._menu_list.GetSelection()
        if idx != wx.NOT_FOUND:
            self._show_groups(self._menus[idx])

        self.Refresh(True)
        self.Layout()

    # ── Gestione file ─────────────────────────────────────────────────────────

    def _on_open(self, _evt):
        dlg = wx.FileDialog(
            self,
            message="Apri file XRC o FBP",
            wildcard="File supportati (*.xrc;*.fbp)|*.xrc;*.fbp|XRC (*.xrc)|*.xrc|FBP (*.fbp)|*.fbp",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._load_file(path)
        dlg.Destroy()

    def _load_file(self, path: str):
        self._filepath = path
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".xrc":
                menus, tree = parse_xrc(path)
                self._menus, self._tree = menus, tree
                self._file_type = "xrc"
            elif ext == ".fbp":
                menus, tree = parse_fbp(path)
                self._menus, self._tree = menus, tree
                self._file_type = "fbp"
            else:
                wx.MessageBox("Formato non supportato.", "Errore", wx.ICON_ERROR)
                return
        except Exception as e:
            wx.MessageBox(f"Errore nel parsing:\n{e}", "Errore", wx.ICON_ERROR)
            return

        self._file_lbl.SetValue(path)
        self._file_lbl.SetForegroundColour(_colors["TEXT_MAIN"])
        self._populate_menu_list()
        self._status_lbl.SetLabel(
            f"{len(self._menus)} menu trovati in {os.path.basename(path)}"
        )

    def _populate_menu_list(self):
        self._menu_list.Clear()
        for mi in self._menus:
            self._menu_list.Append(mi.path)
        self._clear_groups()

    # ── Selezione menu ────────────────────────────────────────────────────────

    def _on_menu_select(self, _evt):
        idx = self._menu_list.GetSelection()
        if idx == wx.NOT_FOUND:
            return
        self._show_groups(self._menus[idx])

    def _show_groups(self, mi: MenuInfo):
        self._clear_groups()
        self._group_checks = []

        if not mi.groups:
            lbl = wx.StaticText(self._scroll, label="(Menu vuoto)")
            lbl.SetForegroundColour(_colors["TEXT_DIM"])
            self._scroll_sizer.Add(lbl, 0, wx.ALL, 10)
            self._scroll.Layout()
            return

        for gi, group in enumerate(mi.groups):
            row = wx.BoxSizer(wx.HORIZONTAL)
            cb = wx.CheckBox(self._scroll, label=f"  Gruppo {gi + 1}  ({len(group.items)} voci) – ordina")
            cb.SetForegroundColour(_colors["ACCENT_LIGHT"])
            cb.SetBackgroundColour(_colors["DARK_BG"])
            cb.SetValue(True)
            self._group_checks.append(cb)
            row.Add(cb, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
            self._scroll_sizer.Add(row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)

            line = wx.StaticLine(self._scroll)
            self._scroll_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

            for item in group.items:
                lbl_text = display_label_xrc(item) if mi.file_type == "xrc" else display_label_fbp(item)
                cls = item.get("class", "")
                icon = "▸ " if cls == "wxMenu" else "  • "
                item_lbl = wx.StaticText(self._scroll, label=f"{icon}{lbl_text}")
                item_lbl.SetForegroundColour(_colors["TEXT_MAIN"] if cls != "wxMenu" else _colors["WARNING"])
                item_lbl.SetBackgroundColour(_colors["DARK_BG"])
                self._scroll_sizer.Add(item_lbl, 0, wx.LEFT, 28)

            self._scroll_sizer.AddSpacer(6)

        self._scroll.SetupScrolling()
        self._scroll.FitInside()
        self._scroll.Layout()
        self._scroll.Refresh()

    def _clear_groups(self):
        self._scroll_sizer.Clear(True)
        self._group_checks = []
        self._scroll.Layout()
        self._scroll.Refresh()

    # ── Ordinamento ───────────────────────────────────────────────────────────

    def _on_sort_selected(self, _evt):
        idx = self._menu_list.GetSelection()
        if idx == wx.NOT_FOUND:
            wx.MessageBox("Seleziona prima un menu.", "Attenzione", wx.ICON_WARNING)
            return
        mi = self._menus[idx]
        group_indices = [i for i, cb in enumerate(self._group_checks) if cb.GetValue()]
        if not group_indices:
            wx.MessageBox("Nessun gruppo selezionato per l'ordinamento.", "Attenzione", wx.ICON_WARNING)
            return
        self._sort_menu(mi, group_indices)
        self._show_groups(mi)   # aggiorna vista
        group_nums = ", ".join(str(i + 1) for i in group_indices)
        self._status_lbl.SetLabel(f"✓ Menu '{mi.name}' ordinato (gruppi: {group_nums})")

    def _on_sort_all(self, _evt):
        if not self._menus:
            return
        for mi in self._menus:
            all_groups = list(range(len(mi.groups)))
            self._sort_menu(mi, all_groups)
        self._status_lbl.SetLabel(f"✓ Tutti i {len(self._menus)} menu ordinati")
        # Aggiorna vista se c'è una selezione
        idx = self._menu_list.GetSelection()
        if idx != wx.NOT_FOUND:
            self._show_groups(self._menus[idx])

    def _sort_menu(self, mi: MenuInfo, group_indices: List[int]):
        if mi.file_type == "xrc":
            apply_sort_xrc(mi, group_indices)
        else:
            apply_sort_fbp(mi, group_indices)

    # ── Opzioni colori ────────────────────────────────────────────────────────

    def _on_options(self, _evt):
        dlg = OptionsDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            self._apply_colors()
            self.Refresh()
        dlg.Destroy()

    # ── Crediti ───────────────────────────────────────────────────────────────

    def _on_credits(self, _evt):
        msg = (
            "Menu Sorter – XRC / FBP\n"
            "Versione 1.0\n\n"
            "Autore: Denisov21  (2026)\n\n"
            "Strumento per l'ordinamento alfabetico\n"
            "delle voci di menu nei file XRC e FBP\n"
            "utilizzati con wxWidgets / wxFormBuilder."
        )
        wx.MessageBox(msg, "Crediti", wx.ICON_INFORMATION | wx.OK, self)

    # ── Salvataggio ───────────────────────────────────────────────────────────

    def _on_save(self, _evt):
        if not self._filepath or not self._tree:
            wx.MessageBox("Nessun file caricato.", "Attenzione", wx.ICON_WARNING)
            return
        try:
            backup = save_tree(self._filepath, self._tree)
            self._status_lbl.SetLabel(f"✓ Salvato. Backup: {os.path.basename(backup)}")
            wx.MessageBox(
                f"File salvato con successo.\nBackup creato: {backup}",
                "Salvato",
                wx.ICON_INFORMATION,
            )
        except Exception as e:
            wx.MessageBox(f"Errore nel salvataggio:\n{e}", "Errore", wx.ICON_ERROR)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = MenuSorterApp(False)
    app.MainLoop()
