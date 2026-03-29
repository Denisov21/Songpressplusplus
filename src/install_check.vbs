' ===========================================================================
' Songpress++ - Installazione e verifica dipendenze
' Compatibile con Windows 7/10/11
' Eseguire come Amministratore per installazioni di sistema
' ===========================================================================

Option Explicit

' ---------------------------------------------------------------------------
' Costanti
' ---------------------------------------------------------------------------
Const PYTHON_MIN_MAJOR = 3
Const PYTHON_MIN_MINOR = 12
Const APP_NAME        = "Songpress++"
Const APP_VERSION     = "1.0.0"

' Dipendenze: nome pip | import Python | versione minima | versione massima (esclusa)
' Formato array: nome_pip, import_name, ver_min, ver_max
Dim DEPS(7, 3)
DEPS(0,0) = "wxPython      " : DEPS(0,1) = "wxPython      " : DEPS(0,2) = "4.2.4  " : DEPS(0,3) = "5.0.0"
DEPS(1,0) = "requests      " : DEPS(1,1) = "requests      " : DEPS(1,2) = "2.32.4 " : DEPS(1,3) = "3.0.0"
DEPS(2,0) = "python-pptx   " : DEPS(2,1) = "python-pptx   " : DEPS(2,2) = "1.0.2  " : DEPS(2,3) = "2.0.0"
DEPS(3,0) = "pyshortcuts   " : DEPS(3,1) = "pyshortcuts   " : DEPS(3,2) = "1.9.5  " : DEPS(3,3) = "2.0.0"
DEPS(4,0) = "reportlab     " : DEPS(4,1) = "reportlab     " : DEPS(4,2) = "4.0.0  " : DEPS(4,3) = "5.0.0"
DEPS(5,0) = "pypdf         " : DEPS(5,1) = "pypdf         " : DEPS(5,2) = "6.0.0  " : DEPS(5,3) = "7.0.0"
DEPS(6,0) = "markdown      " : DEPS(6,1) = "markdown      " : DEPS(6,2) = "3.4    " : DEPS(6,3) = "4.0.0"
DEPS(7,0) = "mistune       " : DEPS(7,1) = "mistune       " : DEPS(7,2) = "3.0.0  " : DEPS(7,3) = "4.0.0"
' ---------------------------------------------------------------------------
' Oggetti globali
' ---------------------------------------------------------------------------
Dim oShell, oFSO, oExec
Set oShell = CreateObject("WScript.Shell")
Set oFSO   = CreateObject("Scripting.FileSystemObject")

' ---------------------------------------------------------------------------
' MAIN
' ---------------------------------------------------------------------------
Dim answer
answer = MsgBox(APP_NAME & " " & APP_VERSION & Chr(13) & Chr(13) & _
    "Questo script:" & Chr(13) & _
    "  1. Verifica che Python >= 3.12 sia installato" & Chr(13) & _
    "  2. Installa o aggiorna le dipendenze mancanti" & Chr(13) & _
    "  3. Verifica che tutte le dipendenze siano nel range corretto" & Chr(13) & Chr(13) & _
    "Continuare?", _
    vbYesNo + vbQuestion, APP_NAME & " - Installazione dipendenze")

If answer = vbNo Then
    WScript.Quit 0
End If

' --- Step 1: cerca Python ---
Dim pythonExe
pythonExe = FindPython()
If pythonExe = "" Then
    MsgBox "Python 3.12 o superiore non trovato." & Chr(13) & Chr(13) & _
        "Scarica Python da https://www.python.org/downloads/" & Chr(13) & _
        "e riavvia questo script.", _
        vbCritical, APP_NAME & " - Python non trovato"
    WScript.Quit 1
End If

' --- Step 2: aggiorna pip e installa tutte le dipendenze in background ---
MsgBox "Python trovato: " & pythonExe & Chr(13) & Chr(13) & _
    "Le dipendenze verranno installate in background." & Chr(13) & _
    "Potrebbe richiedere qualche minuto. Clicca OK per iniziare.", _
    vbInformation, APP_NAME

' Costruisce un batch temporaneo con tutti i comandi in sequenza
Dim batPath, oFile, i, pipSpec
batPath = oFSO.GetSpecialFolder(2) & "\sp_install_" & Int(Timer*1000) & ".bat"
Set oFile = oFSO.OpenTextFile(batPath, 2, True)
oFile.WriteLine "@echo off"
oFile.WriteLine pythonExe & " -m pip install --upgrade pip"
Dim j
For j = 0 To 7
    pipSpec = DEPS(j,0) & ">=" & DEPS(j,2) & ",<" & DEPS(j,3)
    oFile.WriteLine pythonExe & " -m pip install """ & pipSpec & """"
Next
oFile.Close

oShell.Run "cmd /c """ & batPath & """", 0, True

On Error Resume Next
oFSO.DeleteFile batPath
On Error GoTo 0

' --- Step 4: verifica ---
Dim report, allOk
report = "=== Verifica dipendenze " & APP_NAME & " ===" & Chr(13) & Chr(13)
allOk = True

' Verifica Python
Dim pyVer
pyVer = FirstLine(GetCmdOutput(pythonExe & " --version"))
report = report & "[Python]  " & Trim(pyVer) & Chr(13)

' Verifica ogni pacchetto
Dim installed, pkgVer, status
For i = 0 To 7
    pkgVer = GetInstalledVersion(pythonExe, DEPS(i,1))
    If pkgVer = "" Then
        status = "NON TROVATO"
        allOk = False
    ElseIf Not VersionInRange(pkgVer, DEPS(i,2), DEPS(i,3)) Then
        status = "VERSIONE ERRATA (trovata: " & pkgVer & ", richiesta: >=" & DEPS(i,2) & ",<" & DEPS(i,3) & ")"
        allOk = False
    Else
        status = "OK  (" & pkgVer & ")"
    End If
    report = report & "[" & DEPS(i,0) & "]  " & status & Chr(13)
Next

' --- Step 5: risultato finale ---
report = report & Chr(13)
Dim icon, title
If allOk Then
    report = report & "Tutte le dipendenze sono soddisfatte. " & APP_NAME & " e' pronto."
    icon  = vbInformation
    title = APP_NAME & " - Installazione completata"
Else
    report = report & "ATTENZIONE: alcune dipendenze non sono soddisfatte." & Chr(13) & _
        "Prova a eseguire lo script come Amministratore oppure" & Chr(13) & _
        "installale manualmente con:  pip install <pacchetto>"
    icon  = vbExclamation
    title = APP_NAME & " - Problemi rilevati"
End If

MsgBox report, icon, title

WScript.Quit IIf(allOk, 0, 2)

' ===========================================================================
' FUNZIONI
' ===========================================================================

' ---------------------------------------------------------------------------
' FindPython: restituisce il percorso dell'eseguibile Python >= 3.12
' ---------------------------------------------------------------------------
Function FindPython()
    FindPython = ""
    Dim candidates(4)
    candidates(0) = "python"
    candidates(1) = "python3"
    candidates(2) = "py -3.12"
    candidates(3) = "py -3"
    candidates(4) = "python3.12"

    Dim c, ver, major, minor
    For Each c In candidates
        ver = GetCmdOutput(c & " --version")
        If InStr(ver, "Python") > 0 Then
            If ExtractPythonVersion(ver, major, minor) Then
                If major > PYTHON_MIN_MAJOR Or (major = PYTHON_MIN_MAJOR And minor >= PYTHON_MIN_MINOR) Then
                    FindPython = c
                    Exit Function
                End If
            End If
        End If
    Next
End Function

' ---------------------------------------------------------------------------
' ExtractPythonVersion: analizza "Python 3.12.4" → major=3, minor=12
' ---------------------------------------------------------------------------
Function ExtractPythonVersion(verStr, ByRef major, ByRef minor)
    ExtractPythonVersion = False
    Dim parts, nums
    parts = Split(Trim(verStr))
    If UBound(parts) < 1 Then Exit Function
    nums = Split(parts(1), ".")
    If UBound(nums) < 1 Then Exit Function
    On Error Resume Next
    major = CInt(nums(0))
    minor = CInt(nums(1))
    If Err.Number <> 0 Then Exit Function
    On Error GoTo 0
    ExtractPythonVersion = True
End Function

' ---------------------------------------------------------------------------
' GetInstalledVersion: restituisce la versione installata di un pacchetto
' ---------------------------------------------------------------------------
Function GetInstalledVersion(pyExe, pkgName)
    GetInstalledVersion = ""
    Dim output, lines, line, prefix, ver
    output = GetCmdOutput(pyExe & " -m pip show " & pkgName)
    If output = "" Then Exit Function
    lines = Split(output, Chr(10))
    prefix = "version:"
    For Each line In lines
        If LCase(Left(Trim(line), Len(prefix))) = prefix Then
            ver = Trim(Mid(Trim(line), Len(prefix) + 1))
            ver = Replace(ver, Chr(13), "")
            GetInstalledVersion = Trim(ver)
            Exit Function
        End If
    Next
End Function

' ---------------------------------------------------------------------------
' VersionInRange: True se ver >= minVer e ver < maxVer
' ---------------------------------------------------------------------------
Function VersionInRange(ver, minVer, maxVer)
    VersionInRange = (CompareVersions(ver, minVer) >= 0) And (CompareVersions(ver, maxVer) < 0)
End Function

' ---------------------------------------------------------------------------
' CompareVersions: restituisce -1, 0, +1
' ---------------------------------------------------------------------------
Function CompareVersions(v1, v2)
    Dim p1, p2, n1, n2, i, max
    p1 = Split(v1, ".")
    p2 = Split(v2, ".")
    max = UBound(p1)
    If UBound(p2) > max Then max = UBound(p2)
    For i = 0 To max
        n1 = 0 : n2 = 0
        If i <= UBound(p1) Then
            On Error Resume Next
            n1 = CInt(p1(i))
            If Err.Number <> 0 Then n1 = 0
            On Error GoTo 0
        End If
        If i <= UBound(p2) Then
            On Error Resume Next
            n2 = CInt(p2(i))
            If Err.Number <> 0 Then n2 = 0
            On Error GoTo 0
        End If
        If n1 < n2 Then CompareVersions = -1 : Exit Function
        If n1 > n2 Then CompareVersions =  1 : Exit Function
    Next
    CompareVersions = 0
End Function

' ---------------------------------------------------------------------------
' GetCmdOutput: esegue un comando e restituisce stdout
' ---------------------------------------------------------------------------
Function GetCmdOutput(cmd)
    GetCmdOutput = ""
    On Error Resume Next
    Set oExec = oShell.Exec("cmd /c " & cmd & " 2>&1")
    If Err.Number <> 0 Then Exit Function
    On Error GoTo 0
    Dim output
    output = oExec.StdOut.ReadAll()
    output = Replace(output, Chr(13) & Chr(10), Chr(10))
    output = Replace(output, Chr(13), Chr(10))
    GetCmdOutput = Trim(output)
End Function

Function FirstLine(s)
    Dim lines, l
    lines = Split(s, Chr(10))
    For Each l In lines
        l = Trim(l)
        If l <> "" Then
            FirstLine = l
            Exit Function
        End If
    Next
    FirstLine = ""
End Function

' ---------------------------------------------------------------------------
' IIf inline
' ---------------------------------------------------------------------------
Function IIf(cond, valTrue, valFalse)
    If cond Then IIf = valTrue Else IIf = valFalse
End Function
