; ============================================================
;  Songpress++ - Installer LOCALE (da sorgente)
;  Richiede nella cartella installer\:
;    uv.exe           - Windows x64 binary di uv
;    plugins\x86-bit\INetC.dll - plugin NSIS per test connessione (versione x86-unicode)
; ============================================================

!define PRODUCT_NAME      "Songpress++"
!define PRODUCT_PUBLISHER "Denisov21 (fork of Songpress by Luca Allulli / Skeed)"
!define PRODUCT_WEB_SITE  "https://github.com/Denisov21/Songpressplusplus"
!define PRODUCT_DIR_REGKEY   "Software\Microsoft\Windows\CurrentVersion\App Paths\SongPressPlusPlus.exe"
!define PRODUCT_UNINST_KEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKCU"
!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"

!define SRCDIR "${__FILEDIR__}\.."
!searchparse /file "${SRCDIR}\pyproject.toml" `version = "` PRODUCT_VERSION `"`
!ifndef PRODUCT_VERSION
  !error "Impossibile leggere la versione da pyproject.toml."
!endif

; URL usato per testare la connessione: IP Cloudflare, risponde sempre
!define NET_TEST_URL "http://1.1.1.1/"

RequestExecutionLevel user
SetCompressor lzma
Unicode true

;!addplugindir /amd64-unicode "plugins/64-bit"
; INetC sostituito con NScurl (plugin NSIS built-in amd64)
!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "WinMessages.nsh"
!include "FileFunc.nsh"
!insertmacro GetParent

; ---------------------------------------------------------------
;  Font FreeSerif: individua in fase di build la cartella con i .ttf.
;  Metti i file in installer\fonts\ (FreeSerif.ttf, FreeSerifBold.ttf,
;  FreeSerifItalic.ttf, FreeSerifBoldItalic.ttf) oppure passa
;  /D FREESERIF_SRCDIR=... a makensis per un percorso personalizzato.
; ---------------------------------------------------------------
!ifndef FREESERIF_SRCDIR
  !if /FileExists "${SRCDIR}\installer\fonts\FreeSerif.ttf"
    !define FREESERIF_SRCDIR "${SRCDIR}\installer\fonts"
  !else if /FileExists "${SRCDIR}\src\songpress\templates\fonts\FreeSerif.ttf"
    !define FREESERIF_SRCDIR "${SRCDIR}\src\songpress\templates\fonts"
  !else if /FileExists ".\fonts\FreeSerif.ttf"
    !define FREESERIF_SRCDIR ".\fonts"
  !else
    !define FREESERIF_SRCDIR "${SRCDIR}\installer\fonts"
    !warning "FreeSerif: nessun .ttf trovato nei percorsi noti. Metti i font in installer\fonts\ o usa /D FREESERIF_SRCDIR=..."
  !endif
!endif

!macro APP_ASSOCIATE EXT PROGID DESC ICON VERB CMDLINE
  WriteRegStr HKCU "Software\Classes\.${EXT}"        ""          "${PROGID}"
  WriteRegStr HKCU "Software\Classes\${PROGID}"      ""          "${DESC}"
  WriteRegStr HKCU "Software\Classes\${PROGID}\DefaultIcon" ""   "${ICON}"
  WriteRegStr HKCU "Software\Classes\${PROGID}\shell"                    ""        "${VERB}"
  WriteRegStr HKCU "Software\Classes\${PROGID}\shell\${VERB}"            "MUIVerb" "Songpress++"
  WriteRegStr HKCU "Software\Classes\${PROGID}\shell\${VERB}"            "Icon"    "${ICON}"
  WriteRegStr HKCU "Software\Classes\${PROGID}\shell\${VERB}\command"    ""        '${CMDLINE}'
!macroend

!macro APP_UNASSOCIATE EXT PROGID
  DeleteRegKey HKCU "Software\Classes\.${EXT}"
  DeleteRegKey HKCU "Software\Classes\${PROGID}"
!macroend

!macro UPDATEFILEASSOC
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, i 0, i 0)'
!macroend

; ---------------------------------------------------------------
;  InstallUserFont: installa un singolo font TrueType per l'utente
;  corrente (Windows 10 1809+), senza diritti di amministratore.
;  Copia il .ttf in %LOCALAPPDATA%\Microsoft\Windows\Fonts e lo
;  registra in HKCU. Richiede $R9 = cartella font utente.
; ---------------------------------------------------------------
!macro InstallUserFont FILENAME REGNAME
  !if /FileExists "${FREESERIF_SRCDIR}\${FILENAME}"
    File "/oname=$PLUGINSDIR\${FILENAME}" "${FREESERIF_SRCDIR}\${FILENAME}"
    ${If} ${FileExists} "$PLUGINSDIR\${FILENAME}"
      CopyFiles /SILENT "$PLUGINSDIR\${FILENAME}" "$R9\${FILENAME}"
      WriteRegStr HKCU "Software\Microsoft\Windows NT\CurrentVersion\Fonts" "${REGNAME}" "$R9\${FILENAME}"
      DetailPrint "Font: ${FILENAME} -> ${REGNAME}"
    ${EndIf}
  !else
    !warning "FreeSerif: file mancante in build: ${FREESERIF_SRCDIR}\${FILENAME}"
  !endif
!macroend

!define MUI_ABORTWARNING
!define MUI_ICON   "songpressplusplus.ico"
!define MUI_UNICON "songpressplusplus.ico"
; Icona dell'eseguibile dell'installer stesso:
Icon "songpressplusplus.ico"
!define MUI_LANGDLL_REGISTRY_ROOT      "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_LANGDLL_REGISTRY_KEY       "${PRODUCT_UNINST_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "NSIS:Language"

Var SongpressExe
Var UvPath
Var ProjDir
Var AssocExt
Var hwndAssoc
Var hwndCheckNet
Var CheckNet
Var hwndDesktop
Var DesktopShortcut
Var ICONS_GROUP
Var hwndProgress
Var UvLog
Var UvLogPos

!define MUI_WELCOMEPAGE_TEXT "$(STR_WELCOME_TEXT)"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${SRCDIR}\license.txt"
Page custom InstallTypePage InstallTypePageLeave
!define MUI_DIRECTORYPAGE_TEXT_TOP "$(STR_DIR_TOP)"
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE DirectoryLeave
!insertmacro MUI_PAGE_DIRECTORY
!define MUI_STARTMENUPAGE_DEFAULTFOLDER   "Songpress++"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT   "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_KEY    "${PRODUCT_UNINST_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "${PRODUCT_STARTMENU_REGVAL}"
!insertmacro MUI_PAGE_STARTMENU Application $ICONS_GROUP
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN_FUNCTION  FinishRun
!define MUI_FINISHPAGE_RUN_TEXT      "$(STR_LAUNCH_SONGPRESS)"
!define MUI_FINISHPAGE_RUN           ""
!define MUI_FINISHPAGE_TEXT "$(STR_REBOOT_HINT)"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "English"

; --- Stringhe Italian ---
LangString STR_LAUNCH_SONGPRESS    ${LANG_ITALIAN} "Avvia Songpress++"
LangString STR_INSTALLING          ${LANG_ITALIAN} "Installazione in corso... (l'output di uv scorrerà qui sotto)"
LangString STR_UV_OUTPUT_START     ${LANG_ITALIAN} "--- Output uv (download e installazione pacchetti) ---"
LangString STR_UV_OUTPUT_END       ${LANG_ITALIAN} "--- Fine output uv ---"
LangString STR_WAIT_SPIN           ${LANG_ITALIAN} "Installazione in corso, attendere... "
LangString STR_INSTALL_SUCCESS     ${LANG_ITALIAN} "Installazione completata con successo."
LangString STR_CRITICAL_ERROR      ${LANG_ITALIAN} "Errore critico: Songpress++ non installato."
LangString STR_CRITICAL_DETAIL     ${LANG_ITALIAN} "Dettagli:"
LangString STR_UV_CHECK            ${LANG_ITALIAN} "Estrazione uv.exe..."
LangString STR_UV_NOTFOUND         ${LANG_ITALIAN} "uv.exe non trovato nell'installer. Reinstalla."
LangString STR_UV_OK               ${LANG_ITALIAN} "uv pronto:"
LangString STR_SRCDIR_CHECK        ${LANG_ITALIAN} "Verifica cartella sorgente..."
LangString STR_SRCDIR_NOTFOUND     ${LANG_ITALIAN} "pyproject.toml non trovato. Verifica che SRCDIR punti alla radice del progetto."
LangString STR_ASSOC_EXT           ${LANG_ITALIAN} "Associa estensioni (.crd .pro .chopro .chordpro .cho .tab .sng)"
LangString STR_CHECK_NET           ${LANG_ITALIAN} "Verifica connessione internet prima di installare (consigliato)"
LangString STR_DESKTOP_SHORTCUT    ${LANG_ITALIAN} "Crea collegamento sul Desktop"
LangString STR_INSTALL_TYPE        ${LANG_ITALIAN} "Opzioni di installazione"
LangString STR_NET_CHECKING        ${LANG_ITALIAN} "Verifica connessione internet in corso..."
LangString STR_NET_OK              ${LANG_ITALIAN} "Connessione internet: OK."
LangString STR_NET_FAIL            ${LANG_ITALIAN} "Connessione internet non disponibile (errore: $0).$\r$\n$\r$\nL'installazione richiede una connessione attiva per scaricare i pacchetti.$\r$\n$\r$\nVuoi riprovare?"
LangString STR_NET_ABORT           ${LANG_ITALIAN} "Installazione annullata: connessione internet non disponibile."
LangString STR_WELCOME_TEXT        ${LANG_ITALIAN} "Il programma di installazione ti guiderà nell'installazione di $(^Name) $\r$\n$\r$\nATTENZIONE: è richiesta una connessione a Internet attiva durante l'installazione per scaricare i pacchetti necessari.$\r$\n$\r$\nChiudi tutte le altre applicazioni prima di continuare."
LangString UninstallComplete       ${LANG_ITALIAN} "$(^Name) è stato rimosso con successo."
LangString UninstallConfirm        ${LANG_ITALIAN} "Sei sicuro di voler rimuovere $(^Name)?"
LangString STR_PREV_FOUND          ${LANG_ITALIAN} "È stata trovata una versione precedente di ${PRODUCT_NAME} (versione $0).$\r$\nVerrà rimossa prima di procedere con l'installazione.$\r$\n$\r$\nI tuoi template e font personalizzati verranno conservati."
LangString STR_PREV_UNINSTALLING   ${LANG_ITALIAN} "Rimozione versione precedente in corso..."
LangString STR_PREV_UNINSTALL_FAIL ${LANG_ITALIAN} "La rimozione della versione precedente non è riuscita.$\r$\n$\r$\nL'installazione verrà annullata. Chiudi Songpress++ se è in esecuzione, rimuovi la versione precedente da Impostazioni > App e riprova."
LangString STR_COPY_ASSETS         ${LANG_ITALIAN} "Copia template e font in cartella utente..."
LangString STR_INSTALL_FONTS       ${LANG_ITALIAN} "Installazione font FreeSerif (per l'utente corrente)..."
LangString STR_COPY_ASSETS_WARN    ${LANG_ITALIAN} "Attenzione: template o font non trovati nel pacchetto installato.$\r$\nPercorso atteso:$\r$\n$0"
LangString STR_REBOOT_HINT         ${LANG_ITALIAN} "Per completare l'installazione e visualizzare Songpress++ nel menu Start, è consigliato riavviare il computer."
LangString STR_UNINST_APPDATA      ${LANG_ITALIAN} "⚠ Rimuovere anche i template e font personalizzati in %APPDATA%\Songpress++?$\r$\n$\r$\nQuesta operazione non può essere annullata.$\r$\n(Scegli No per conservare le tue personalizzazioni)"
LangString STR_NO_PROGRAMFILES     ${LANG_ITALIAN} "⚠ ATTENZIONE: non installare Songpress++ nella cartella «Programmi» o «Programmi (x86)».$\r$\n$\r$\nSongpress++ è un'applicazione per singolo utente e va installata in una cartella personale (predefinita: $LOCALAPPDATA\Songpress++).$\r$\n$\r$\nScegli un'altra cartella di destinazione."
LangString STR_DIR_TOP             ${LANG_ITALIAN} "Questa procedura installerà ${PRODUCT_NAME} nella cartella indicata sotto.$\r$\n$\r$\n⚠ ATTENZIONE: non installare in «Programmi» o «Programmi (x86)». Songpress++ è un'applicazione per singolo utente: mantieni la cartella personale predefinita."

; --- Stringhe English ---
LangString STR_LAUNCH_SONGPRESS    ${LANG_ENGLISH} "Launch Songpress++"
LangString STR_INSTALLING          ${LANG_ENGLISH} "Installing... (uv output will scroll below)"
LangString STR_UV_OUTPUT_START     ${LANG_ENGLISH} "--- uv output (downloading and installing packages) ---"
LangString STR_UV_OUTPUT_END       ${LANG_ENGLISH} "--- End of uv output ---"
LangString STR_WAIT_SPIN           ${LANG_ENGLISH} "Installing, please wait... "
LangString STR_INSTALL_SUCCESS     ${LANG_ENGLISH} "Installation completed successfully."
LangString STR_CRITICAL_ERROR      ${LANG_ENGLISH} "Critical error: Songpress++ not installed."
LangString STR_CRITICAL_DETAIL     ${LANG_ENGLISH} "Details:"
LangString STR_UV_CHECK            ${LANG_ENGLISH} "Extracting uv.exe..."
LangString STR_UV_NOTFOUND         ${LANG_ENGLISH} "uv.exe not found in installer. Please reinstall."
LangString STR_UV_OK               ${LANG_ENGLISH} "uv ready:"
LangString STR_SRCDIR_CHECK        ${LANG_ENGLISH} "Checking source folder..."
LangString STR_SRCDIR_NOTFOUND     ${LANG_ENGLISH} "pyproject.toml not found. Check that SRCDIR points to the project root."
LangString STR_ASSOC_EXT           ${LANG_ENGLISH} "Associate file extensions (.crd .pro .chopro .chordpro .cho .tab .sng)"
LangString STR_CHECK_NET           ${LANG_ENGLISH} "Check internet connection before installing (recommended)"
LangString STR_DESKTOP_SHORTCUT    ${LANG_ENGLISH} "Create Desktop shortcut"
LangString STR_INSTALL_TYPE        ${LANG_ENGLISH} "Installation options"
LangString STR_NET_CHECKING        ${LANG_ENGLISH} "Checking internet connection..."
LangString STR_NET_OK              ${LANG_ENGLISH} "Internet connection: OK."
LangString STR_NET_FAIL            ${LANG_ENGLISH} "Internet connection not available (error: $0).$\r$\n$\r$\nInstallation requires an active connection to download packages.$\r$\n$\r$\nDo you want to retry?"
LangString STR_NET_ABORT           ${LANG_ENGLISH} "Installation cancelled: internet connection not available."
LangString STR_WELCOME_TEXT        ${LANG_ENGLISH} "This wizard will guide you through the installation of $(^Name) version ${PRODUCT_VERSION}.$\r$\n$\r$\nNOTE: An active Internet connection is required during installation to download the necessary packages.$\r$\n$\r$\nPlease close all other applications before continuing."
LangString UninstallComplete       ${LANG_ENGLISH} "$(^Name) has been successfully removed."
LangString UninstallConfirm        ${LANG_ENGLISH} "Are you sure you want to remove $(^Name)?"
LangString STR_PREV_FOUND          ${LANG_ENGLISH} "⚠ A previous version of ${PRODUCT_NAME} (version $0) was found.$\r$\nIt will be removed before proceeding with the installation.$\r$\n$\r$\nYour custom templates and fonts will be kept."
LangString STR_PREV_UNINSTALLING   ${LANG_ENGLISH} "Removing previous version..."
LangString STR_PREV_UNINSTALL_FAIL ${LANG_ENGLISH} "The previous version could not be removed.$\r$\n$\r$\nThe installation will be cancelled. Close Songpress++ if it is running, remove the previous version from Settings > Apps and try again."
LangString STR_COPY_ASSETS         ${LANG_ENGLISH} "Copying templates and fonts to user folder..."
LangString STR_INSTALL_FONTS       ${LANG_ENGLISH} "Installing FreeSerif fonts (current user)..."
LangString STR_COPY_ASSETS_WARN    ${LANG_ENGLISH} "Warning: templates or fonts not found in the installed package.$\r$\nExpected path:$\r$\n$0"
LangString STR_REBOOT_HINT         ${LANG_ENGLISH} "To complete the installation and make Songpress++ appear in the Start menu, it is recommended to restart your computer."
LangString STR_UNINST_APPDATA      ${LANG_ENGLISH} "⚠ Also remove custom templates and fonts in %APPDATA%\Songpress++?$\r$\n$\r$\nThis cannot be undone.$\r$\n(Choose No to keep your customizations)"
LangString STR_NO_PROGRAMFILES     ${LANG_ENGLISH} "⚠ WARNING: do not install Songpress++ in the «Program Files» or «Program Files (x86)» folder.$\r$\n$\r$\nSongpress++ is a per-user application and must be installed in a personal folder (default: $LOCALAPPDATA\Songpress++).$\r$\n$\r$\nPlease choose a different destination folder."
LangString STR_DIR_TOP             ${LANG_ENGLISH} "This wizard will install ${PRODUCT_NAME} in the folder shown below.$\r$\n$\r$\n⚠ WARNING: do not install in «Program Files» or «Program Files (x86)». Songpress++ is a per-user application: keep the default personal folder."

Name    "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "songpress++x86-setup.exe"
InstallDir "$LOCALAPPDATA\Songpress++"
InstallDirRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
AutoCloseWindow false

; ---------------------------------------------------------------
;  DirectoryLeave: blocca l'installazione in Programmi / Program Files (x86)
;  Songpress++ è per-utente (RequestExecutionLevel user) e va in $LOCALAPPDATA.
;  StrCmp è case-insensitive; su Windows 32-bit $PROGRAMFILES64 = cartella Programmi.
; ---------------------------------------------------------------
Function DirectoryLeave
  StrLen $R1 "$PROGRAMFILES64"
  StrCpy $R2 "$INSTDIR" $R1
  StrCmp $R2 "$PROGRAMFILES64" pf_block 0

  StrLen $R1 "$PROGRAMFILES32"
  StrCpy $R2 "$INSTDIR" $R1
  StrCmp $R2 "$PROGRAMFILES32" pf_block 0

  Return

  pf_block:
    MessageBox MB_ICONEXCLAMATION|MB_OK "$(STR_NO_PROGRAMFILES)"
    Abort
FunctionEnd

Function InstallTypePage
  !insertmacro MUI_HEADER_TEXT "$(STR_INSTALL_TYPE)" ""
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}
  ${NSD_CreateCheckbox} 10u 10u 280u 14u "$(STR_ASSOC_EXT)"
  Pop $hwndAssoc
  ${NSD_Check} $hwndAssoc  ; spuntato di default
  ${NSD_CreateHLine} 10u 28u 280u 1u ""
  Pop $0
  ${NSD_CreateCheckbox} 10u 32u 280u 14u "$(STR_CHECK_NET)"
  Pop $hwndCheckNet
  ${NSD_Check} $hwndCheckNet  ; spuntato di default
  ${NSD_CreateHLine} 10u 50u 280u 1u ""
  Pop $0
  ${NSD_CreateCheckbox} 10u 54u 280u 14u "$(STR_DESKTOP_SHORTCUT)"
  Pop $hwndDesktop
  ${NSD_Check} $hwndDesktop  ; spuntato di default

  nsDialogs::Show
FunctionEnd

Function InstallTypePageLeave
  ${NSD_GetState} $hwndAssoc   $AssocExt
  ${NSD_GetState} $hwndCheckNet $CheckNet
  ${NSD_GetState} $hwndDesktop  $DesktopShortcut
FunctionEnd

Function FinishRun
  Exec "$SongpressExe"
FunctionEnd

; ---------------------------------------------------------------
;  onInit: lingua + gestione versione precedente
;  Flusso:
;    trovata versione precedente
;      -> avviso con OK / Annulla (rimozione obbligatoria)
;           -> OK: disinstalla (cartella ricavata da UninstallString)
;                -> riuscita: procede
;                -> fallita: errore e installazione annullata
;           -> Annulla: esce
;      -> modalità /S: nessun avviso, disinstalla direttamente
; ---------------------------------------------------------------
Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY

  ReadRegStr $0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"
  ${If} $0 != ""
    ; Rimozione obbligatoria: OK = procedi, Annulla = esci.
    ; In modalità silenziosa (/S) nessun messaggio: si rimuove direttamente.
    ${IfNot} ${Silent}
      MessageBox MB_ICONEXCLAMATION|MB_OKCANCEL "$(STR_PREV_FOUND)" IDOK prev_uninst
      Goto prev_abort
    ${EndIf}

    prev_uninst:
      ReadRegStr $1 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
      ${If} $1 != ""
        ; Cartella della vecchia versione = cartella che contiene uninst.exe
        ; (non $INSTDIR, che in .onInit può puntare altrove)
        ${GetParent} "$1" $R0
        DetailPrint "$(STR_PREV_UNINSTALLING)"
        ExecWait '"$1" /S _?=$R0'
        ; Verifica se la disinstallazione è riuscita
        ReadRegStr $2 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"
        ${If} $2 != ""
          ; Disinstallazione fallita: l'installazione viene annullata
          MessageBox MB_ICONSTOP|MB_OK "$(STR_PREV_UNINSTALL_FAIL)" /SD IDOK
          Goto prev_abort
        ${EndIf}
      ${EndIf}
      Goto prev_done

    prev_abort:
      Abort

    prev_done:
  ${EndIf}
FunctionEnd

; ---------------------------------------------------------------
;  CheckInternet: verifica connessione con NScurl (built-in NSIS amd64).
;  NScurl::http restituisce codice HTTP in $0 e status in $1.
;  Timeout connessione: 10 secondi.
;  In caso di errore: Riprova / Annulla.
; ---------------------------------------------------------------
Function CheckInternet
  DetailPrint "$(STR_NET_CHECKING)"

  net_retry:
  NScurl::http GET "${NET_TEST_URL}" "$INSTDIR\nettest.tmp" /TIMEOUT 10000 /END
  Pop $0   ; status string: "OK" oppure messaggio di errore
  Delete "$INSTDIR\nettest.tmp"

  ${If} $0 == "OK"
    DetailPrint "$(STR_NET_OK)"
  ${Else}
    MessageBox MB_ICONEXCLAMATION|MB_RETRYCANCEL "$(STR_NET_FAIL)" \
      IDRETRY net_retry IDCANCEL net_cancel
    net_cancel:
    DetailPrint "$(STR_NET_ABORT)"
    Abort
  ${EndIf}
FunctionEnd

; ---------------------------------------------------------------
;  CopyAssetsToAppData
;  Copia la cartella templates dal pacchetto uv nella destinazione corretta:
;    - Installazione standard:  %APPDATA%\Songpress++\templates
;    - Installazione portabile: $INSTDIR\templates  (accanto all'exe)
;  Sorgente: $INSTDIR\tools\songpressplusplus\Lib\site-packages\songpressplusplus\
; ---------------------------------------------------------------
Function CopyAssetsToAppData
  DetailPrint "$(STR_COPY_ASSETS)"

  ; Percorso base del pacchetto installato da uv
  StrCpy $R0 "$INSTDIR\tools\songpressplusplus\Lib\site-packages\songpressplusplus"

  ; Verifica che il percorso esista prima di procedere
  ${Unless} ${FileExists} "$R0\*.*"
    StrCpy $0 "$R0"
    MessageBox MB_ICONEXCLAMATION "$(STR_COPY_ASSETS_WARN)"
    Return
  ${EndUnless}

  ; Scegli la cartella di destinazione in base alla modalità
  SetShellVarContext current
  StrCpy $R1 "$APPDATA\Songpress++\templates"
  CreateDirectory "$R1"

  ; Copia tutta la cartella templates (ricorsiva: include songs, slides, fonts
  ; e qualsiasi altra sottocartella futura), sovrascrive senza chiedere conferma
  nsExec::ExecToLog 'xcopy "$R0\templates" "$R1" /E /I /Y /Q'
FunctionEnd

; ---------------------------------------------------------------
;  InstallFonts: installa la famiglia FreeSerif per l'utente corrente
;  e notifica a Windows il cambiamento dei font.
; ---------------------------------------------------------------
Function InstallFonts
  DetailPrint "$(STR_INSTALL_FONTS)"
  SetShellVarContext current
  StrCpy $R9 "$LOCALAPPDATA\Microsoft\Windows\Fonts"
  CreateDirectory "$R9"

  !insertmacro InstallUserFont "FreeSerif.ttf"           "FreeSerif (TrueType)"
  !insertmacro InstallUserFont "FreeSerifBold.ttf"       "FreeSerif Bold (TrueType)"
  !insertmacro InstallUserFont "FreeSerifItalic.ttf"     "FreeSerif Italic (TrueType)"
  !insertmacro InstallUserFont "FreeSerifBoldItalic.ttf" "FreeSerif Bold Italic (TrueType)"

  ; Notifica a tutte le finestre che l'elenco font e' cambiato
  SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0 /TIMEOUT=1000
FunctionEnd

; ---------------------------------------------------------------
;  BusyBarStart / BusyBarStop: durante l'esecuzione di uv (che puo' durare
;  minuti) la barra di avanzamento passa in modalita' "marquee": scorre
;  all'infinito, cosi' l'installer non sembra bloccato.
;    PBS_MARQUEE = 0x08, PBM_SETMARQUEE = WM_USER+10 = 0x040A
;  Il controllo della pagina InstFiles ha ID 1004.
; ---------------------------------------------------------------
Function BusyBarStart
  Push $0
  Push $1
  FindWindow $0 "#32770" "" $HWNDPARENT
  GetDlgItem $hwndProgress $0 1004
  ${If} $hwndProgress != 0
    System::Call 'user32::GetWindowLong(i $hwndProgress, i -16) i .r1'
    IntOp $1 $1 | 0x08
    System::Call 'user32::SetWindowLong(i $hwndProgress, i -16, i $1)'
    SendMessage $hwndProgress 0x040A 1 30
  ${EndIf}
  Pop $1
  Pop $0
FunctionEnd

Function BusyBarStop
  Push $1
  ${If} $hwndProgress != ""
  ${AndIf} $hwndProgress != 0
    SendMessage $hwndProgress 0x040A 0 0
    System::Call 'user32::GetWindowLong(i $hwndProgress, i -16) i .r1'
    IntOp $1 $1 & 0xFFFFFFF7
    System::Call 'user32::SetWindowLong(i $hwndProgress, i -16, i $1)'
  ${EndIf}
  Pop $1
FunctionEnd

; ---------------------------------------------------------------
;  UvLogPump: legge dal file di log di uv le righe complete arrivate
;  dall'ultima volta e le mostra nel log dell'installer (DetailPrint).
;  $UvLogPos tiene l'offset gia' letto; una riga incompleta viene
;  rimandata al giro successivo.
; ---------------------------------------------------------------
Function UvLogPump
  Push $0
  Push $1
  Push $2
  ; uv tiene il file aperto in scrittura: FileOpen (che condivide solo in
  ; lettura) fallirebbe. Ne leggo una copia, rifatta a ogni giro.
  System::Call 'kernel32::CopyFile(t "$UvLog", t "$UvLog.rd", i 0)'
  FileOpen $0 "$UvLog.rd" r
  ${If} $0 != ""
    FileSeek $0 $UvLogPos SET
    pump_next:
      FileRead $0 $1
      ${If} $1 == ""
        Goto pump_end
      ${EndIf}
      StrCpy $2 $1 1 -1
      ${If} $2 == "$\n"
        StrCpy $1 $1 -1
        StrCpy $2 $1 1 -1
        ${If} $2 == "$\r"
          StrCpy $1 $1 -1
        ${EndIf}
        ${If} $1 != ""
          DetailPrint "$1"
        ${EndIf}
        FileSeek $0 0 CUR $UvLogPos
        Goto pump_next
      ${EndIf}
    pump_end:
    FileClose $0
  ${EndIf}
  Pop $2
  Pop $1
  Pop $0
FunctionEnd

; ---------------------------------------------------------------
;  RunUvSpinner: lancia uv in modo asincrono (ExecDos) e, finche' non
;  termina, aggiorna una rotella di testo (| / - \) nel sottotitolo
;  della finestra (controllo 1038). uv scrive su un file di log che
;  UvLogPump rilegge di continuo, cosi' l'elenco pacchetti scorre nel log.
;  Ritorna il codice di uscita in $0. Se ExecDos non parte, ripiega
;  su nsExec (senza rotella).
; ---------------------------------------------------------------
Function RunUvSpinner
  Push $2
  Push $3
  Push $4
  Push $5
  Push $6

  GetDlgItem $6 $HWNDPARENT 1038

  StrCpy $UvLog "$PLUGINSDIR\uv_install.log"
  StrCpy $UvLogPos 0
  Delete "$UvLog"
  ExecDos::exec /NOUNLOAD /ASYNC 'cmd.exe /c ""$UvPath" tool install --force "$ProjDir" > "$UvLog" 2>&1"' "" ""
  Pop $3   ; handle del processo
  ${If} $3 == ""
  ${OrIf} $3 == "error"
    nsExec::ExecToLog '"$UvPath" tool install --force "$ProjDir"'
    Pop $0
    Goto spin_exit
  ${EndIf}

  StrCpy $2 0
  spin_loop:
    ExecDos::isdone /NOUNLOAD $3
    Pop $4
    ${If} $4 == 1
      Goto spin_done
    ${EndIf}
    IntOp $2 $2 + 1
    IntOp $5 $2 % 4
    ${If} $5 == 0
      StrCpy $5 "|"
    ${ElseIf} $5 == 1
      StrCpy $5 "/"
    ${ElseIf} $5 == 2
      StrCpy $5 "-"
    ${Else}
      StrCpy $5 "\"
    ${EndIf}
    SendMessage $6 ${WM_SETTEXT} 0 "STR:$(STR_WAIT_SPIN)$5"
    Call UvLogPump
    Sleep 120
    Goto spin_loop

  spin_done:
  Call UvLogPump
  ExecDos::wait $3
  Pop $0
  ; ripristina il sottotitolo originale della pagina
  SendMessage $6 ${WM_SETTEXT} 0 "STR:$(MUI_TEXT_INSTALLING_SUBTITLE)"

  spin_exit:
  Pop $6
  Pop $5
  Pop $4
  Pop $3
  Pop $2
FunctionEnd

; ---------------------------------------------------------------
;  Installazione core
; ---------------------------------------------------------------
Function DoInstallLocal
  ; 0. Calcola ProjDir (padre di $EXEDIR)
  StrCpy $ProjDir $EXEDIR
  ${DoUntil} $ProjDir == ""
    StrCpy $0 $ProjDir "" -1
    ${If} $0 == "\"
      StrLen $0 $ProjDir
      IntOp $0 $0 - 1
      StrCpy $ProjDir $ProjDir $0
      ${Break}
    ${EndIf}
    StrLen $0 $ProjDir
    IntOp $0 $0 - 1
    StrCpy $ProjDir $ProjDir $0
  ${Loop}

  ; 1. Test connessione internet (solo se richiesto dall'utente)
  ${If} $CheckNet == ${BST_CHECKED}
    Call CheckInternet
  ${EndIf}

  ; 2. Estrai uv.exe
  DetailPrint "$(STR_UV_CHECK)"
  File "/oname=$PLUGINSDIR\uv.exe" "uv-i686\uv.exe"
  ${If} ${FileExists} "$PLUGINSDIR\uv.exe"
    StrCpy $UvPath "$PLUGINSDIR\uv.exe"
    DetailPrint "$(STR_UV_OK) $UvPath"
  ${Else}
    MessageBox MB_ICONSTOP "$(STR_UV_NOTFOUND)"
    Abort
  ${EndIf}

  ; 3. Verifica pyproject.toml
  DetailPrint "$(STR_SRCDIR_CHECK)"
  ${Unless} ${FileExists} "$ProjDir\pyproject.toml"
    MessageBox MB_ICONSTOP "$(STR_SRCDIR_NOTFOUND)$\n$ProjDir"
    Abort
  ${EndUnless}

  ; 4. Variabili d'ambiente uv
  System::Call 'kernel32::SetEnvironmentVariable(t "UV_TOOL_BIN_DIR",       t "$INSTDIR\bin")'
  System::Call 'kernel32::SetEnvironmentVariable(t "UV_TOOL_DIR",           t "$INSTDIR\tools")'
  System::Call 'kernel32::SetEnvironmentVariable(t "UV_PYTHON_INSTALL_DIR", t "$INSTDIR\python")'
  System::Call 'kernel32::SetEnvironmentVariable(t "UV_CACHE_DIR",          t "$INSTDIR\cache")'

  ; 5. Installa
  DetailPrint "$(STR_INSTALLING)"
  DetailPrint "$(STR_UV_OUTPUT_START)"
  Call BusyBarStart
  Call RunUvSpinner
  Call BusyBarStop
  StrCpy $1 ""   ; ExecToLog non restituisce stdout
  DetailPrint "$(STR_UV_OUTPUT_END)"

  ; 6. Verifica
  ${Unless} ${FileExists} "$INSTDIR\bin\SongPressPlusPlus.exe"
    DetailPrint "$(STR_CRITICAL_ERROR)"
    MessageBox MB_ICONSTOP "$(STR_CRITICAL_ERROR)$\n$\n$(STR_CRITICAL_DETAIL)$\n$1"
    Abort
  ${EndUnless}
  DetailPrint "$(STR_INSTALL_SUCCESS)"
  StrCpy $SongpressExe "$INSTDIR\bin\SongPressPlusPlus.exe"

  ; 6b. Incorpora icona nell'exe tramite rcedit
  !if /FileExists "${SRCDIR}\installer\tools\rcedit-i686.exe"
    File "/oname=$PLUGINSDIR\rcedit.exe" "${SRCDIR}\installer\tools\rcedit-i686.exe"
  !else if /FileExists ".\tools\rcedit-i686.exe"
    File "/oname=$PLUGINSDIR\rcedit.exe" ".\tools\rcedit-i686.exe"
  !else
    !warning "rcedit-i686.exe non trovato: l'icona non verrà incorporata nell'exe."
  !endif
  ${If} ${FileExists} "$PLUGINSDIR\rcedit.exe"
    DetailPrint "Incorporazione icona nell'exe..."
    nsExec::ExecToLog '"$PLUGINSDIR\rcedit.exe" "$SongpressExe" --set-icon "$INSTDIR\songpressplusplus.ico"'
    Pop $0
    ${If} $0 == 0
      DetailPrint "Icona incorporata con successo."
    ${Else}
      DetailPrint "Avviso: rcedit ha restituito codice $0. L'icona potrebbe non essere stata incorporata."
    ${EndIf}
  ${EndIf}

  ; 6c. Copia templates\songs e fonts in %APPDATA%\Songpress++
  Call CopyAssetsToAppData
  Call InstallFonts

  ; 7. Pulizia cache
  RMDir /r "$INSTDIR\cache"
FunctionEnd

Section "Songpress++" SongpressSection
  SectionIn RO
  AddSize 255000  ; spazio stimato: ~250 MB (uv + Python + pacchetti)
  SetOutPath "$INSTDIR"

  !if /FileExists "${SRCDIR}\src\songpress\songpressplusplus.ico"
    File "/oname=songpressplusplus.ico" "${SRCDIR}\src\songpress\songpressplusplus.ico"
  !else if /FileExists "${SRCDIR}\songpressplusplus.ico"
    File "/oname=songpressplusplus.ico" "${SRCDIR}\songpressplusplus.ico"
  !else if /FileExists ".\songpressplusplus.ico"
    File "/oname=songpressplusplus.ico" ".\songpressplusplus.ico"
  !else
    !warning "songpressplusplus.ico non trovato."
  !endif

  Call DoInstallLocal

  ; --- Pulizia ProgID legacy (Songpress.crd) da installazioni precedenti ---
  DeleteRegKey HKCU "Software\Classes\Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.crd\OpenWithProgids" "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.pro\OpenWithProgids" "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.chopro\OpenWithProgids" "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.chordpro\OpenWithProgids" "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.cho\OpenWithProgids" "Songpress.crd"
  ; --- Pulizia ProgID legacy (Songpress.ChordPro) da installazioni precedenti ---
  DeleteRegKey HKCU "Software\Classes\Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.crd\OpenWithProgids" "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.pro\OpenWithProgids" "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.chopro\OpenWithProgids" "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.chordpro\OpenWithProgids" "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.cho\OpenWithProgids" "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.tab\OpenWithProgids" "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.tab\OpenWithProgids" "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.sng\OpenWithProgids" "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.sng\OpenWithProgids" "Songpress.ChordPro"

  ${If} $AssocExt == ${BST_CHECKED}
    !insertmacro APP_ASSOCIATE "crd"      "SongpressPlusPlus.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "open" '"$SongpressExe" "%1"'
    !insertmacro APP_ASSOCIATE "pro"      "SongpressPlusPlus.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "open" '"$SongpressExe" "%1"'
    !insertmacro APP_ASSOCIATE "chopro"   "SongpressPlusPlus.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "open" '"$SongpressExe" "%1"'
    !insertmacro APP_ASSOCIATE "chordpro" "SongpressPlusPlus.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "open" '"$SongpressExe" "%1"'
    !insertmacro APP_ASSOCIATE "cho"      "SongpressPlusPlus.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "open" '"$SongpressExe" "%1"'
    !insertmacro APP_ASSOCIATE "tab"      "SongpressPlusPlus.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "open" '"$SongpressExe" "%1"'
    !insertmacro APP_ASSOCIATE "sng"      "SongpressPlusPlus.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "open" '"$SongpressExe" "%1"'
    !insertmacro UPDATEFILEASSOC
  ${EndIf}

  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
    ${If} ${FileExists} "$INSTDIR\songpressplusplus.ico"
      CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk" \
        "$SongpressExe" "" "$INSTDIR\songpressplusplus.ico" 0
    ${Else}
      CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk" "$SongpressExe"
    ${EndIf}
  !insertmacro MUI_STARTMENU_WRITE_END

  ${If} $DesktopShortcut == ${BST_CHECKED}
    ${If} ${FileExists} "$INSTDIR\songpressplusplus.ico"
      CreateShortCut "$DESKTOP\Songpress++.lnk" \
        "$SongpressExe" "" "$INSTDIR\songpressplusplus.ico" 0
    ${Else}
      CreateShortCut "$DESKTOP\Songpress++.lnk" "$SongpressExe"
    ${EndIf}
  ${EndIf}
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName"     "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon"     "$INSTDIR\songpressplusplus.ico"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"  "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout"    "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher"       "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "SourceDir"       "$EXEDIR"

  ; --- Fallback: ricrea il collegamento nel menu Start se mancante ---
  ; (può succedere se DoInstallLocal ha chiamato Abort prima della Section principale)
  ${If} $SongpressExe == ""
    StrCpy $SongpressExe "$INSTDIR\bin\SongPressPlusPlus.exe"
  ${EndIf}
  !insertmacro MUI_STARTMENU_GETFOLDER Application $ICONS_GROUP
  ${Unless} ${FileExists} "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk"
    CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
    ${If} ${FileExists} "$INSTDIR\songpressplusplus.ico"
      CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk" \
        "$SongpressExe" "" "$INSTDIR\songpressplusplus.ico" 0
    ${Else}
      CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk" "$SongpressExe"
    ${EndIf}
  ${EndUnless}
  ${If} $DesktopShortcut == ${BST_CHECKED}
    ${Unless} ${FileExists} "$DESKTOP\Songpress++.lnk"
      ${If} ${FileExists} "$INSTDIR\songpressplusplus.ico"
        CreateShortCut "$DESKTOP\Songpress++.lnk" \
          "$SongpressExe" "" "$INSTDIR\songpressplusplus.ico" 0
      ${Else}
        CreateShortCut "$DESKTOP\Songpress++.lnk" "$SongpressExe"
      ${EndIf}
    ${EndUnless}
  ${EndIf}

SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(UninstallComplete)"
FunctionEnd

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
  MessageBox MB_ICONEXCLAMATION|MB_YESNO|MB_DEFBUTTON2 "$(UninstallConfirm)" /SD IDYES IDYES +2
  Abort
FunctionEnd

Section Uninstall
  ; --- Rimuovi ProgID legacy Songpress.crd e voci OpenWithProgids ---
  DeleteRegKey   HKCU "Software\Classes\Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.crd\OpenWithProgids"      "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.pro\OpenWithProgids"      "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.chopro\OpenWithProgids"   "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.chordpro\OpenWithProgids" "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.cho\OpenWithProgids"      "Songpress.crd"
  ; --- Rimuovi ProgID legacy Songpress.ChordPro e voci OpenWithProgids ---
  DeleteRegKey   HKCU "Software\Classes\Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.crd\OpenWithProgids"      "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.pro\OpenWithProgids"      "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.chopro\OpenWithProgids"   "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.chordpro\OpenWithProgids" "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.cho\OpenWithProgids"      "Songpress.ChordPro"
  DeleteRegValue HKCU "Software\Classes\.tab\OpenWithProgids"      "Songpress.crd"
  DeleteRegValue HKCU "Software\Classes\.tab\OpenWithProgids"      "Songpress.ChordPro"
  ; --- Rimuovi associazioni SongpressPlusPlus.ChordPro ---
  !insertmacro APP_UNASSOCIATE "crd"      "SongpressPlusPlus.ChordPro"
  !insertmacro APP_UNASSOCIATE "pro"      "SongpressPlusPlus.ChordPro"
  !insertmacro APP_UNASSOCIATE "chopro"   "SongpressPlusPlus.ChordPro"
  !insertmacro APP_UNASSOCIATE "chordpro" "SongpressPlusPlus.ChordPro"
  !insertmacro APP_UNASSOCIATE "cho"      "SongpressPlusPlus.ChordPro"
  !insertmacro APP_UNASSOCIATE "tab"      "SongpressPlusPlus.ChordPro"
  !insertmacro APP_UNASSOCIATE "sng"      "SongpressPlusPlus.ChordPro"
  !insertmacro UPDATEFILEASSOC

    ; --- Rimuovi font FreeSerif installati per l'utente corrente ---
    SetShellVarContext current
    DeleteRegValue HKCU "Software\Microsoft\Windows NT\CurrentVersion\Fonts" "FreeSerif (TrueType)"
    DeleteRegValue HKCU "Software\Microsoft\Windows NT\CurrentVersion\Fonts" "FreeSerif Bold (TrueType)"
    DeleteRegValue HKCU "Software\Microsoft\Windows NT\CurrentVersion\Fonts" "FreeSerif Italic (TrueType)"
    DeleteRegValue HKCU "Software\Microsoft\Windows NT\CurrentVersion\Fonts" "FreeSerif Bold Italic (TrueType)"
    Delete "$LOCALAPPDATA\Microsoft\Windows\Fonts\FreeSerif.ttf"
    Delete "$LOCALAPPDATA\Microsoft\Windows\Fonts\FreeSerifBold.ttf"
    Delete "$LOCALAPPDATA\Microsoft\Windows\Fonts\FreeSerifItalic.ttf"
    Delete "$LOCALAPPDATA\Microsoft\Windows\Fonts\FreeSerifBoldItalic.ttf"
    SendMessage ${HWND_BROADCAST} ${WM_FONTCHANGE} 0 0 /TIMEOUT=1000

  !insertmacro MUI_STARTMENU_GETFOLDER "Application" $ICONS_GROUP
  Delete "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk"
  RMDir  "$SMPROGRAMS\$ICONS_GROUP"
  Delete "$DESKTOP\Songpress++.lnk"

  RMDir /r "$INSTDIR\bin"
  RMDir /r "$INSTDIR\tools"
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\cache"
  RMDir /r "$INSTDIR\logs"   ; log di impaginazione (PrintDialog.py)
  Delete "$INSTDIR\songpressplusplus.ico"
  Delete "$INSTDIR\uninst.exe"
  RMDir  "$INSTDIR"

  ; Rimuovi %APPDATA%\Songpress++ solo se confermato dall'utente
  SetShellVarContext current
  ${If} ${FileExists} "$APPDATA\Songpress++\*.*"
    MessageBox MB_ICONEXCLAMATION|MB_YESNO|MB_DEFBUTTON2 \
      "$(STR_UNINST_APPDATA)" /SD IDNO IDYES uninst_appdata IDNO uninst_skip_appdata
    uninst_appdata:
      RMDir /r "$APPDATA\Songpress++"
    uninst_skip_appdata:
  ${EndIf}

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  SetAutoClose true
SectionEnd
