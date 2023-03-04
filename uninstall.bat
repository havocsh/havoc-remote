echo "Stopping HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe stop HavocRemoteOperator

echo "Uninstalling HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe remove HavocRemoteOperator confirm

echo "Backing up link.ini to link.ini.bak"
copy link.ini link.ini.bak

echo "Deleting all files and directories except the link.ini backup"
for /f %%F in ('dir /b /a-d ^| findstr /vile ".bak"') do del "%%F"
del __pycache__
del havoc-pkg
del Lib
del nssm-2.24
del python-3.10.10-embed-amd64
del Scripts

echo "Uninstall complete"
echo "If you are not concerned with keeping the backup ini file, feel free to delete the havoc-remote-main directory."
c:\windows\system32\windowspowershell\v1.0\powershell.exe "Start-Sleep -s 10"