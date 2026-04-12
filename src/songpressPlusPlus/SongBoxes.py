###############################################################
# Name:                SoongBoxes.py
# Purpose:      Elements that make up a song
# Author:           Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-02-21
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
###############################################################

import wx

from .SongFormat import *


class SongBox(object):
     def __init__(self, x, y, w, h):
          object.__init__(self)
          self.x = x
          self.y = y
          self.w = w
          self.h = h
          self.marginLeft = 0
          self.marginRight = 0
          self.marginTop = 0
          self.marginBottom = 0
          self.boxes = []

     def RelocateBox(self, box):
          self.w = max(self.w, box.x + box.GetTotalWidth())
          self.h = max(self.h, box.y + box.GetTotalHeight())
          
     def AddBox(self, box):
          self.boxes.append(box)
          box.parent = self
          self.RelocateBox(box)
          
     def SetMargin(self, top, right, bottom, left):
          self.marginTop = top
          self.marginRight = right
          self.marginBottom = bottom
          self.marginLeft = left
          
     def GetTotalHeight(self):
          return self.h + self.marginTop + self.marginBottom

     def GetTotalWidth(self):
          return self.w + self.marginLeft + self.marginRight

     
class SongSong(SongBox):
     def __init__(self, format):
          SongBox.__init__(self, 0, 0, 0, 0)
          self.format = format
          self.verseCount = 0
          self.chorusCount = 0
          self.labelCount = 0
          self.drawWholeSong = False
          self.chordsBelow = False


class SongBlock(SongBox):
     # types
     verse = 1
     chorus = 2
     title = 3
     subtitle = 4

     def __init__(self, type, format):
          SongBox.__init__(self, 0, 0, 0, 0)
          self.type = type
          self.verseNumber = 0
          self.format = format
          self.drawBlock = False
          self.label = None
          self.chords = []
          self.pageBreakBefore = False  # True = interruzione di pagina prima di questo blocco
          self.is_tab = False           # True = contenuto {start_of_tab}
          self.is_grid = False          # True = contenuto {start_of_grid}
          
     def RemoveChordBoxes(self):
          for l in self.boxes:
               l.RemoveChordBoxes()

     def GetLastLineTextHeight(self):
          if len(self.boxes) > 0:
               return self.boxes[-1].GetTextHeight()
          return 0

               
class SongLine(SongBox):
     def __init__(self):
          SongBox.__init__(self, 0, 0, 0, 0)
          self.hasChords = False
          self.chordBaseline = 0
          self.textBaseline = 0

     def AddBox(self, text):
          if text.type == text.chord:
               self.hasChords = True
          SongBox.AddBox(self, text)
          
     def RemoveChordBoxes(self):
          self.boxes = [b for b in self.boxes if b.type != b.chord]

     def GetTextHeight(self):
          tbs = [b for b in self.boxes if b.type != b.chord]
          if len(tbs) == 0:
               return self.h
          return max(tb.h for tb in tbs)

     
class SongText(SongBox):
     text = 1
     chord = 2
     comment = 3
     title = 4
     subtitle = 5
     
     def __init__(self, text, font, type, color):
          SongBox.__init__(self, 0, 0, 0, 0)
          self.text = text
          self.font = font
          self.type = type
          self.color = color


class SongImageBox(SongBox):
     """Box autonomo che rappresenta una direttiva {image: ...} di ChordPro.

     Attributi:
         path   -- percorso assoluto o relativo al file immagine
         width  -- larghezza richiesta in punti logici (0 = auto)
         height -- altezza richiesta in punti logici (0 = auto)
         scale  -- fattore di scala (1.0 = nessuna scala; 0.5 = 50%)
         align  -- 'left' | 'center' | 'right'
         border -- spessore bordo in px logici (0 = nessun bordo)
     """

     def __init__(self, path, width=0, height=0, scale=1.0, align='center', border=0):
          SongBox.__init__(self, 0, 0, 0, 0)
          self.path = path
          # Se path è un data: URI (immagine embedded in base64), _temp_path
          # viene popolato la prima volta che serve il file fisico e viene
          # riutilizzato per i render successivi finché l'oggetto è vivo.
          self._temp_path = None
          self.img_width = width    # larghezza richiesta (0 = auto)
          self.img_height = height  # altezza richiesta (0 = auto)
          self.scale = scale
          self.align = align        # 'left' | 'center' | 'right'
          self.border = border
          # Compatibilità con SongDecorator.LayoutComposeSong:
          self.drawBlock = True
          self.pageBreakBefore = False
          self.columnBreakBefore = False

     def is_embedded(self):
          """True se l'immagine è un data: URI base64 (non un percorso file)."""
          return isinstance(self.path, str) and self.path.startswith('data:')

     def resolve_path(self):
          """Restituisce il percorso fisico usabile da wx.Image.

          Per immagini embedded decodifica il base64 in un file temporaneo
          (creato una sola volta, riutilizzato nei render successivi).
          Per immagini normali restituisce self.path direttamente.
          """
          if not self.is_embedded():
               return self.path
          if self._temp_path and __import__('os').path.isfile(self._temp_path):
               return self._temp_path
          import base64, tempfile, os
          try:
               # Formato: data:<mime>;base64,<dati>
               header, b64data = self.path.split(',', 1)
               raw = base64.b64decode(b64data)
               mime = header.split(':')[1].split(';')[0].lower() if ':' in header else 'image/png'
               ext_map = {'image/png': '.png', 'image/jpeg': '.jpg',
                          'image/gif': '.gif', 'image/bmp': '.bmp',
                          'image/tiff': '.tif', 'image/webp': '.webp'}
               ext = ext_map.get(mime, '.png')
               tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
               tmp.write(raw)
               tmp.close()
               self._temp_path = tmp.name
               return self._temp_path
          except Exception:
               return self.path

     def __del__(self):
          """Rimuove il file temporaneo quando l'oggetto viene distrutto."""
          if self._temp_path:
               try:
                    __import__('os').unlink(self._temp_path)
               except Exception:
                    pass

     # Necessario per RelocateBox / GetLastLineTextHeight chiamati su song.boxes
     def GetLastLineTextHeight(self):
          return 0


class SongGridBox(SongBox):
     """Box autonomo che rappresenta un blocco {start_of_grid}.

     Attributi:
         rows         -- lista di liste di stringhe: ogni lista è una riga di battute
                         es. [['C', 'G'], ['Am', 'F']]
         display_mode -- 'pipe' | 'plain' | 'table'
         font         -- wx.Font da usare per il testo delle celle
         label        -- etichetta del blocco (es. 'Grid' o etichetta personalizzata)
         cell_w       -- larghezza cella calcolata da LayoutComposeGrid (px)
         cell_h       -- altezza cella calcolata da LayoutComposeGrid (px)
         col_count    -- numero massimo di colonne
     """

     def __init__(self, rows, display_mode='pipe', font=None, label='Grid', size=1,
                  chordTopSpacing=None, lineSpacing=None, sizeDir='both',
                  chord_font=None, chord_color=None):
          SongBox.__init__(self, 0, 0, 0, 0)
          self.rows = rows            # list[list[str]]
          self.display_mode = display_mode
          self.font = font
          self.chord_font = chord_font    # wx.Font per il testo degli accordi nelle celle
          self.chord_color = chord_color  # wx.Colour per il testo degli accordi nelle celle
          self.label = label
          self.size = max(1.0, float(size))  # moltiplicatore celle (da size=N nella direttiva, float)
          self.sizeDir = sizeDir if sizeDir in ('both', 'horizontal', 'vertical') else 'both'
          self.cell_w = 0
          self.cell_h = 0
          self.col_count = 0
          self._pad_x = int(8 * (self.size if self.sizeDir in ('both', 'horizontal') else 1.0))
          self._pad_y = int(4 * (self.size if self.sizeDir in ('both', 'vertical')   else 1.0))
          # Spaziatura opzionale (None = usa i valori globali del SongFormat)
          self.chordTopSpacing = chordTopSpacing  # spazio extra sopra ogni riga (px)
          self.lineSpacing = lineSpacing          # spazio extra sotto ogni riga (px)
          # Compatibilità con SongDecorator.LayoutComposeSong:
          self.drawBlock = True
          self.pageBreakBefore = False
          self.columnBreakBefore = False

     def GetLastLineTextHeight(self):
          return 0
