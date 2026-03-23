Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pyScriptPath = fso.GetAbsolutePathName(scriptDir & "\..\..\songpressplusplus\src\main.py")

pythonPath = ""
On Error Resume Next
pythonPath = WshShell.RegRead("HKCU\SOFTWARE\Python\PythonCore\3.14\InstallPath\ExecutablePath")
On Error GoTo 0

pythonw = Replace(pythonPath, "python.exe", "pythonw.exe")

msg = "scriptDir:      " & scriptDir & vbCrLf
msg = msg & "pyScriptPath:   " & pyScriptPath & vbCrLf
msg = msg & "python.exe:     " & pythonPath & vbCrLf
msg = msg & "pythonw.exe:    " & pythonw & vbCrLf
msg = msg & vbCrLf
msg = msg & "pythonw esiste? " & fso.FileExists(pythonw) & vbCrLf
msg = msg & "main.py esiste? " & fso.FileExists(pyScriptPath) & vbCrLf

MsgBox msg, vbInformation, "Diagnostica Songpress"
