Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pyScriptPath = fso.GetAbsolutePathName(scriptDir & "\..\..\songpressplusplus\src\main.py")

' Trova pythonw.exe dinamicamente dal registro (tutte le versioni 3.x)
pythonPath = ""
On Error Resume Next

' Prova le versioni comuni di Python 3
Dim versions(10)
versions(0) = "3.14"
versions(1) = "3.13"
versions(2) = "3.12"
versions(3) = "3.11"
versions(4) = "3.10"
versions(5) = "3.9"
versions(6) = "3.8"
versions(7) = "3.7"
versions(8) = "3.6"
versions(9) = "3.5"
versions(10) = "3.4"

Dim i
For i = 0 To 10
    If pythonPath = "" Then
        pythonPath = WshShell.RegRead("HKLM\SOFTWARE\Python\PythonCore\" & versions(i) & "\InstallPath\ExecutablePath")
    End If
    If pythonPath = "" Then
        pythonPath = WshShell.RegRead("HKCU\SOFTWARE\Python\PythonCore\" & versions(i) & "\InstallPath\ExecutablePath")
    End If
Next

On Error GoTo 0

' Sostituisce python.exe con pythonw.exe
If pythonPath <> "" Then
    pythonPath = Replace(pythonPath, "python.exe", "pythonw.exe")
End If

' Verifica che i file esistano
If Not fso.FileExists(pythonPath) Then
    MsgBox "pythonw.exe non trovato:" & vbCrLf & pythonPath, vbCritical
    WScript.Quit 1
End If
If Not fso.FileExists(pyScriptPath) Then
    MsgBox "Script Python non trovato:" & vbCrLf & pyScriptPath, vbCritical
    WScript.Quit 1
End If

WshShell.Run """" & pythonPath & """ """ & pyScriptPath & """", 1, False
