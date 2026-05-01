Set WshShell = CreateObject("WScript.Shell")
ROOT = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
venv_pythonw = ROOT & ".venv\Scripts\pythonw.exe"
script = ROOT & "src\biblioteca_tk.py"
If Dir(venv_pythonw) <> "" Then
    WshShell.Run """" & venv_pythonw & """ """ & script & """", 0, False
Else
    WshShell.Run "pythonw """ & script & """", 0, False
End If
