; ============================================================
;  Songpress++ - Installer LOCALE (da sorgente)
;  Richiede nella cartella installer\:
;    uv.exe           - Windows x64 binary di uv
;    plugins\INetC.dll - plugin NSIS per test connessione (versione amd64-unicode)
; ============================================================

!define PRODUCT_NAME      "Songpress++"
!define PRODUCT_PUBLISHER "Denisov21 (fork di Luca Allulli - Skeed)"
!define PRODUCT_WEB_SITE  "http://www.skeed.it"
!define PRODUCT_DIR_REGKEY   "Software\Microsoft\Windows\CurrentVersion\App Paths\songpress.exe"
!define PRODUCT_UNINST_KEY   "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKCU"
!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"

!define SRCDIR ".."
!searchparse /file "${SRCDIR}\pyproject.toml" `version = "` PRODUCT_VERSION `"`
!ifndef PRODUCT_VERSION
  !error "Impossibile leggere la versione da pyproject.toml."
!endif

; URL usato per testare la connessione: IP Cloudflare, risponde sempre
!define NET_TEST_URL "http://1.1.1.1/"

RequestExecutionLevel user
SetCompressor lzma

!addplugindir /amd64-unicode "plugins"
!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"

!macro APP_ASSOCIATE EXT PROGID DESC ICON VERB CMDLINE
  WriteRegStr HKCU "Software\Classes\.${EXT}"        ""          "${PROGID}"
  WriteRegStr HKCU "Software\Classes\${PROGID}"      ""          "${DESC}"
  WriteRegStr HKCU "Software\Classes\${PROGID}\DefaultIcon" ""   "${ICON}"
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

!define MUI_ABORTWARNING
!define MUI_ICON   "songpressplusplus.ico"
!define MUI_UNICON "songpressplusplus.ico"
!define MUI_LANGDLL_REGISTRY_ROOT      "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_LANGDLL_REGISTRY_KEY       "${PRODUCT_UNINST_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "NSIS:Language"

Var SongpressExe
Var UvPath
Var ProjDir
Var IsPortable
Var AssocExt
Var hwndNormal
Var hwndPortable
Var hwndAssoc
Var hwndCheckNet
Var CheckNet
Var hwndDesktop
Var DesktopShortcut
Var ICONS_GROUP

!define MUI_WELCOMEPAGE_TEXT "$(STR_WELCOME_TEXT)"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${SRCDIR}\license.txt"
Page custom InstallTypePage InstallTypePageLeave
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
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "English"

; --- Stringhe Italian ---
LangString STR_LAUNCH_SONGPRESS    ${LANG_ITALIAN} "Avvia Songpress++"
LangString STR_INSTALLING          ${LANG_ITALIAN} "Installazione Songpress++ dalla sorgente locale..."
LangString STR_INSTALL_SUCCESS     ${LANG_ITALIAN} "Installazione completata con successo."
LangString STR_CRITICAL_ERROR      ${LANG_ITALIAN} "Errore critico: Songpress++ non installato."
LangString STR_CRITICAL_DETAIL     ${LANG_ITALIAN} "Dettagli:"
LangString STR_UV_CHECK            ${LANG_ITALIAN} "Estrazione uv.exe..."
LangString STR_UV_NOTFOUND         ${LANG_ITALIAN} "uv.exe non trovato nell'installer. Reinstalla."
LangString STR_UV_OK               ${LANG_ITALIAN} "uv pronto:"
LangString STR_SRCDIR_CHECK        ${LANG_ITALIAN} "Verifica cartella sorgente..."
LangString STR_SRCDIR_NOTFOUND     ${LANG_ITALIAN} "pyproject.toml non trovato. Verifica che SRCDIR punti alla radice del progetto."
LangString STR_ASSOC_EXT           ${LANG_ITALIAN} "Associa estensioni (.crd .pro .chopro .chordpro .cho)"
LangString STR_CHECK_NET           ${LANG_ITALIAN} "Verifica connessione internet prima di installare (consigliato)"
LangString STR_DESKTOP_SHORTCUT    ${LANG_ITALIAN} "Crea collegamento sul Desktop"
LangString STR_PORTABLE            ${LANG_ITALIAN} "Installazione portabile"
LangString STR_PORTABLE_DESC       ${LANG_ITALIAN} "Installa Songpress++ in una cartella autonoma. Nessuna voce nel registro, nessuna scorciatoia. La cartella puo' essere spostata su qualsiasi PC o chiavetta USB."
LangString STR_INSTALL_NORMAL      ${LANG_ITALIAN} "Installazione standard (consigliata)"
LangString STR_INSTALL_NORMAL_DESC ${LANG_ITALIAN} "Installa Songpress++ nella cartella User dell'utente corrente, crea scorciatoie nel menu Start e associa i tipi di file. Non richiede privilegi di amministratore."
LangString STR_INSTALL_TYPE        ${LANG_ITALIAN} "Tipo di installazione"
LangString STR_NET_CHECKING        ${LANG_ITALIAN} "Verifica connessione internet in corso..."
LangString STR_NET_OK              ${LANG_ITALIAN} "Connessione internet: OK."
LangString STR_NET_FAIL            ${LANG_ITALIAN} "Connessione internet non disponibile (errore: $0).$\r$\n$\r$\nL'installazione richiede una connessione attiva per scaricare i pacchetti.$\r$\n$\r$\nVuoi riprovare?"
LangString STR_NET_ABORT           ${LANG_ITALIAN} "Installazione annullata: connessione internet non disponibile."
LangString STR_WELCOME_TEXT        ${LANG_ITALIAN} "Il programma di installazione ti guiderà nell'installazione di $(^Name) versione ${PRODUCT_VERSION}.$\r$\n$\r$\nATTENZIONE: è richiesta una connessione a Internet attiva durante l'installazione per scaricare i pacchetti necessari.$\r$\n$\r$\nChiudi tutte le altre applicazioni prima di continuare."
LangString UninstallComplete       ${LANG_ITALIAN} "$(^Name) e' stato rimosso con successo."
LangString UninstallConfirm        ${LANG_ITALIAN} "Sei sicuro di voler rimuovere $(^Name)?"
LangString STR_PREV_FOUND          ${LANG_ITALIAN} "E' stata trovata una versione precedente di ${PRODUCT_NAME} (versione $0).$\r$\nVuoi rimuoverla prima di procedere con l'installazione?"
LangString STR_PREV_UNINSTALLING   ${LANG_ITALIAN} "Rimozione versione precedente in corso..."
LangString STR_PREV_UNINSTALL_FAIL ${LANG_ITALIAN} "La rimozione della versione precedente non e' riuscita.$\r$\nVuoi continuare comunque con l'installazione?"
LangString STR_PREV_SKIP           ${LANG_ITALIAN} "Hai scelto di non rimuovere la versione precedente.$\r$\nVuoi continuare comunque con l'installazione?"

; --- Stringhe English ---
LangString STR_LAUNCH_SONGPRESS    ${LANG_ENGLISH} "Launch Songpress++"
LangString STR_INSTALLING          ${LANG_ENGLISH} "Installing Songpress++ from local source..."
LangString STR_INSTALL_SUCCESS     ${LANG_ENGLISH} "Installation completed successfully."
LangString STR_CRITICAL_ERROR      ${LANG_ENGLISH} "Critical error: Songpress++ not installed."
LangString STR_CRITICAL_DETAIL     ${LANG_ENGLISH} "Details:"
LangString STR_UV_CHECK            ${LANG_ENGLISH} "Extracting uv.exe..."
LangString STR_UV_NOTFOUND         ${LANG_ENGLISH} "uv.exe not found in installer. Please reinstall."
LangString STR_UV_OK               ${LANG_ENGLISH} "uv ready:"
LangString STR_SRCDIR_CHECK        ${LANG_ENGLISH} "Checking source folder..."
LangString STR_SRCDIR_NOTFOUND     ${LANG_ENGLISH} "pyproject.toml not found. Check that SRCDIR points to the project root."
LangString STR_ASSOC_EXT           ${LANG_ENGLISH} "Associate file extensions (.crd .pro .chopro .chordpro .cho)"
LangString STR_CHECK_NET           ${LANG_ENGLISH} "Check internet connection before installing (recommended)"
LangString STR_DESKTOP_SHORTCUT    ${LANG_ENGLISH} "Create Desktop shortcut"
LangString STR_PORTABLE            ${LANG_ENGLISH} "Portable installation"
LangString STR_PORTABLE_DESC       ${LANG_ENGLISH} "Installs Songpress++ in a standalone folder. No registry entries, no shortcuts. The folder can be moved to any PC or USB drive."
LangString STR_INSTALL_NORMAL      ${LANG_ENGLISH} "Standard installation (recommended)"
LangString STR_INSTALL_NORMAL_DESC ${LANG_ENGLISH} "Installs Songpress++ in the current user's folder, creates Start menu shortcuts and associates file types. Does not require administrator privileges."
LangString STR_INSTALL_TYPE        ${LANG_ENGLISH} "Installation type"
LangString STR_NET_CHECKING        ${LANG_ENGLISH} "Checking internet connection..."
LangString STR_NET_OK              ${LANG_ENGLISH} "Internet connection: OK."
LangString STR_NET_FAIL            ${LANG_ENGLISH} "Internet connection not available (error: $0).$\r$\n$\r$\nInstallation requires an active connection to download packages.$\r$\n$\r$\nDo you want to retry?"
LangString STR_NET_ABORT           ${LANG_ENGLISH} "Installation cancelled: internet connection not available."
LangString STR_WELCOME_TEXT        ${LANG_ENGLISH} "This wizard will guide you through the installation of $(^Name) version ${PRODUCT_VERSION}.$\r$\n$\r$\nNOTE: An active Internet connection is required during installation to download the necessary packages.$\r$\n$\r$\nPlease close all other applications before continuing."
LangString UninstallComplete       ${LANG_ENGLISH} "$(^Name) has been successfully removed."
LangString UninstallConfirm        ${LANG_ENGLISH} "Are you sure you want to remove $(^Name)?"
LangString STR_PREV_FOUND          ${LANG_ENGLISH} "A previous version of ${PRODUCT_NAME} (version $0) was found.$\r$\nDo you want to remove it before proceeding with the installation?"
LangString STR_PREV_UNINSTALLING   ${LANG_ENGLISH} "Removing previous version..."
LangString STR_PREV_UNINSTALL_FAIL ${LANG_ENGLISH} "The previous version could not be removed.$\r$\nDo you want to continue with the installation anyway?"
LangString STR_PREV_SKIP           ${LANG_ENGLISH} "You chose not to remove the previous version.$\r$\nDo you want to continue with the installation anyway?"

Name    "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "songpress++-setup.exe"
InstallDir "$LOCALAPPDATA\Songpress++"
InstallDirRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
AutoCloseWindow false

Function InstallTypePage
  !insertmacro MUI_HEADER_TEXT "$(STR_INSTALL_TYPE)" ""
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}
  ${NSD_CreateRadioButton} 10u 4u 280u 14u "$(STR_INSTALL_NORMAL)"
  Pop $hwndNormal
  ${NSD_Check} $hwndNormal
  ${NSD_CreateLabel} 22u 18u 268u 18u "$(STR_INSTALL_NORMAL_DESC)"
  Pop $0
  ${NSD_CreateHLine} 10u 38u 280u 1u ""
  Pop $0
  ${NSD_CreateRadioButton} 10u 42u 280u 14u "$(STR_PORTABLE)"
  Pop $hwndPortable
  ${NSD_CreateLabel} 22u 56u 268u 18u "$(STR_PORTABLE_DESC)"
  Pop $0
  ${NSD_CreateHLine} 10u 76u 280u 1u ""
  Pop $0
  ${NSD_CreateCheckbox} 10u 80u 280u 14u "$(STR_ASSOC_EXT)"
  Pop $hwndAssoc
  ${NSD_CreateHLine} 10u 96u 280u 1u ""
  Pop $0
  ${NSD_CreateCheckbox} 10u 100u 280u 14u "$(STR_CHECK_NET)"
  Pop $hwndCheckNet
  ${NSD_Check} $hwndCheckNet  ; spuntato di default
  ${NSD_CreateHLine} 10u 116u 280u 1u ""
  Pop $0
  ${NSD_CreateCheckbox} 10u 120u 280u 14u "$(STR_DESKTOP_SHORTCUT)"
  Pop $hwndDesktop
  ${NSD_Check} $hwndDesktop  ; spuntato di default

  nsDialogs::Show
FunctionEnd

Function InstallTypePageLeave
  ${NSD_GetState} $hwndPortable $IsPortable
  ${NSD_GetState} $hwndAssoc   $AssocExt
  ${NSD_GetState} $hwndCheckNet $CheckNet
  ${NSD_GetState} $hwndDesktop  $DesktopShortcut
  ${If} $IsPortable == ${BST_CHECKED}
    StrCpy $INSTDIR "$DESKTOP\Songpress++"
  ${Else}
    StrCpy $INSTDIR "$LOCALAPPDATA\Songpress-local"
  ${EndIf}
FunctionEnd

Function FinishRun
  Exec "$SongpressExe"
FunctionEnd

; ---------------------------------------------------------------
;  onInit: lingua + gestione versione precedente
;  Flusso:
;    trovata versione precedente
;      -> Sì (disinstalla)
;           -> OK: procede
;           -> Fallita: Continua/Annulla
;      -> No: Continua/Annulla
; ---------------------------------------------------------------
Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY

  ReadRegStr $0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"
  ${If} $0 != ""
    ; Chiede se vuole disinstallare la versione precedente
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON1 "$(STR_PREV_FOUND)" IDYES prev_uninst IDNO prev_skip

    prev_skip:
      ; Utente non vuole disinstallare: continua o annulla
      MessageBox MB_ICONEXCLAMATION|MB_YESNO|MB_DEFBUTTON2 "$(STR_PREV_SKIP)" IDYES prev_done IDNO prev_abort
      Goto prev_abort

    prev_uninst:
      ReadRegStr $1 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
      ${If} $1 != ""
        DetailPrint "$(STR_PREV_UNINSTALLING)"
        ExecWait '"$1" /S _?=$INSTDIR'
        ; Verifica se la disinstallazione e' riuscita
        ReadRegStr $2 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"
        ${If} $2 != ""
          ; Disinstallazione fallita: continua o annulla
          MessageBox MB_ICONEXCLAMATION|MB_YESNO|MB_DEFBUTTON2 "$(STR_PREV_UNINSTALL_FAIL)" IDYES prev_done IDNO prev_abort
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
;  CheckInternet: scarica un file minimo da pypi.org con INetC.
;  Richiede plugins\INetC.dll (amd64-unicode) nella cartella installer\plugins;  INetC restituisce "OK" se il download ha avuto successo,
;  oppure una stringa di errore (es. "Connection refused",
;  "Host not found", "SSL error", ...).
;  Timeout connessione: 10 secondi.
;  In caso di errore: Riprova / Annulla.
; ---------------------------------------------------------------
Function CheckInternet
  DetailPrint "$(STR_NET_CHECKING)"

  net_retry:
  CreateDirectory "$INSTDIR"
  inetc::get /SILENT /CONNECTTIMEOUT 10000 /RECEIVETIMEOUT 10000 \
    "${NET_TEST_URL}" "$INSTDIR\nettest.tmp"
  Pop $0
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
  File "/oname=$PLUGINSDIR\uv.exe" "uv.exe"
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
  nsExec::ExecToStack '"$UvPath" tool install --force "$ProjDir"'
  Pop $0
  Pop $1

  ; 6. Verifica
  ${Unless} ${FileExists} "$INSTDIR\bin\songpress.exe"
    DetailPrint "$(STR_CRITICAL_ERROR)"
    MessageBox MB_ICONSTOP "$(STR_CRITICAL_ERROR)$\n$\n$(STR_CRITICAL_DETAIL)$\n$1"
    Abort
  ${EndUnless}
  DetailPrint "$(STR_INSTALL_SUCCESS)"
  StrCpy $SongpressExe "$INSTDIR\bin\songpress.exe"

  ; 7. Pulizia cache
  RMDir /r "$INSTDIR\cache"
FunctionEnd

Section "Songpress++" SongpressSection
  SectionIn RO
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

  ${If} $IsPortable != ${BST_CHECKED}
    ${If} $AssocExt == ${BST_CHECKED}
      !insertmacro APP_ASSOCIATE "crd"      "Songpress.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "Open" '"$SongpressExe" "%1"'
      !insertmacro APP_ASSOCIATE "pro"      "Songpress.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "Open" '"$SongpressExe" "%1"'
      !insertmacro APP_ASSOCIATE "chopro"   "Songpress.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "Open" '"$SongpressExe" "%1"'
      !insertmacro APP_ASSOCIATE "chordpro" "Songpress.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "Open" '"$SongpressExe" "%1"'
      !insertmacro APP_ASSOCIATE "cho"      "Songpress.ChordPro" "ChordPro" "$INSTDIR\songpressplusplus.ico,0" "Open" '"$SongpressExe" "%1"'
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
  ${EndIf}
SectionEnd

Section -Post
  ${If} $IsPortable != ${BST_CHECKED}
    WriteUninstaller "$INSTDIR\uninst.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName"     "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon"     "$INSTDIR\songpressplusplus.ico"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion"  "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout"    "${PRODUCT_WEB_SITE}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher"       "${PRODUCT_PUBLISHER}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "SourceDir"       "$EXEDIR"
  ${EndIf}
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(UninstallComplete)"
FunctionEnd

Function un.onInit
  !insertmacro MUI_UNGETLANGUAGE
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "$(UninstallConfirm)" IDYES +2
  Abort
FunctionEnd

Section Uninstall
  !insertmacro APP_UNASSOCIATE "crd"      "Songpress.ChordPro"
  !insertmacro APP_UNASSOCIATE "pro"      "Songpress.ChordPro"
  !insertmacro APP_UNASSOCIATE "chopro"   "Songpress.ChordPro"
  !insertmacro APP_UNASSOCIATE "chordpro" "Songpress.ChordPro"
  !insertmacro APP_UNASSOCIATE "cho"      "Songpress.ChordPro"
  !insertmacro UPDATEFILEASSOC

  !insertmacro MUI_STARTMENU_GETFOLDER "Application" $ICONS_GROUP
  Delete "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk"
  RMDir  "$SMPROGRAMS\$ICONS_GROUP"
  Delete "$DESKTOP\Songpress++.lnk"

  RMDir /r "$INSTDIR\bin"
  RMDir /r "$INSTDIR\tools"
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\cache"
  Delete "$INSTDIR\songpressplusplus.ico"
  Delete "$INSTDIR\uninst.exe"
  RMDir  "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  SetAutoClose true
SectionEnd
