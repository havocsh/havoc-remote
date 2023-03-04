@echo off
echo "Stopping HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe stop HavocRemoteOperator

echo "Uninstalling HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe remove HavocRemoteOperator confirm

echo "Backing up link.ini to link.ini.bak"
copy link.ini link.ini.bak

echo "Deleting all files and directories except the link.ini backup"
rmdir /S /Q __pycache__
rmdir /S /Q havoc-pkg
rmdir /S /Q Lib
rmdir /S /Q nssm-2.24
rmdir /S /Q Scripts

echo "Uninstall complete"
echo "If you are not concerned with keeping the backup ini file, feel free to delete the havoc-remote-main directory."
timeout /t 15

for /f %%F in ('dir /b /a-d ^| findstr /vile ".bak"') do del "%%F"