Set fso = CreateObject("Scripting.FileSystemObject")
Set WshShell = CreateObject("WScript.Shell")

' ตั้งค่า Working Directory ให้เป็นโฟลเดอร์โปรเจกต์ปัจจุบันเสมอ
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' สั่งรัน pythonw.exe แบบซ่อนหน้าต่าง (เลข 0 = ซ่อนหน้าต่าง 100%)
WshShell.Run """" & currentDir & "\.venv\Scripts\pythonw.exe"" main.py", 0, False 