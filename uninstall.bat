echo "Stopping HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe stop HavocRemoteOperator

echo "Uninstalling HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe remove HavocRemoteOperator confirm

echo "Deleting nssm-2.24"
del nssm-2.24

echo "Backing up link.ini to link.ini.bak"
copy link.ini link.ini.bak

echo "Deleting all files except the link.ini backup"
for /f %F in ('dir /b /a-d ^| findstr /vile ".bak"') do del "%F"

echo "Uninstall complete"
echo "If you are not concerned with keeping the backup ini file, feel free to delete the havoc-remote-main directory."
c:\windows\system32\windowspowershell\v1.0\powershell.exe "Start-Sleep -s 10"