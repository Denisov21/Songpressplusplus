Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pyScriptPath = fso.GetAbsolutePathName(scriptDir & "\..\..\songpressplusplus\src\main.py")

' Trova tutte le versioni Python 3 installate tramite reg query
pythonPath = ""
On Error Resume Next

Dim oExec, sLine, sVersion
For Each hive In Array("HKLM", "HKCU")
    If pythonPath = "" Then
        Set oExec = WshShell.Exec("reg query """ & hive & "\SOFTWARE\Python\PythonCore"" /f 3. /k")
        Do While Not oExec.StdOut.AtEndOfStream
            sLine = Trim(oExec.StdOut.ReadLine())
            If InStr(sLine, "PythonCore\3.") > 0 Then
                sVersion = Mid(sLine, InStr(sLine, "PythonCore\3.") + Len("PythonCore\"))
                Dim candidate
                candidate = WshShell.RegRead(hive & "\SOFTWARE\Python\PythonCore\" & sVersion & "\InstallPath\ExecutablePath")
                If candidate <> "" Then
                    pythonPath = Replace(candidate, "python.exe", "pythonw.exe")
                End If
            End If
        Loop
    End If
Next

On Error GoTo 0

' Verifica Python
If pythonPath = "" Or Not fso.FileExists(pythonPath) Then
    MsgBox "Python 3 non trovato sul sistema." & vbCrLf & vbCrLf & _
           "Installa Python 3 da https://www.python.org" & vbCrLf & _
           "e assicurati di spuntare 'Add Python to PATH' durante l'installazione.", _
           vbCritical, "Songpress - Errore avvio"
    WScript.Quit 1
End If

' Verifica script principale
If Not fso.FileExists(pyScriptPath) Then
    MsgBox "File principale di Songpress non trovato:" & vbCrLf & vbCrLf & _
           pyScriptPath, vbCritical, "Songpress - Errore avvio"
    WScript.Quit 1
End If

WshShell.Run """" & pythonPath & """ """ & pyScriptPath & """", 1, False

