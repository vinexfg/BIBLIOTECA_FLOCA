If InStr(LCase(WScript.FullName), "cscript") > 0 Then
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.Run "wscript """ & WScript.ScriptFullName & """", 0, False
    WScript.Quit
End If

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ROOT = fso.GetParentFolderName(WScript.ScriptFullName) & "\"
script = ROOT & "src\biblioteca_tk.py"

venv_pw = ROOT & ".venv\Scripts\pythonw.exe"
If fso.FileExists(venv_pw) Then
    WshShell.Run """" & venv_pw & """ """ & script & """", 0, False
    WScript.Quit
End If

WshShell.Run "pythonw """ & script & """", 0, False
