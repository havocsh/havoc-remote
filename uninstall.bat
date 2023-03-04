@echo off
echo Uninstalling ./HAVOC remote_operator task:
echo  
echo - Stopping HavocRemoteOperator service
echo  
nssm-2.24\nssm-2.24\win64\nssm.exe stop HavocRemoteOperator

echo - Uninstalling HavocRemoteOperator service
echo  
nssm-2.24\nssm-2.24\win64\nssm.exe remove HavocRemoteOperator confirm 

echo - Backing up link.ini to link.ini.bak
echo  
copy link.ini link.ini.bak >nul

echo - Deleting all files and directories except the link.ini backup
echo  
rmdir /S /Q __pycache__ >nul
rmdir /S /Q havoc-pkg >nul
rmdir /S /Q Lib >nul
rmdir /S /Q nssm-2.24 >nul
rmdir /S /Q Scripts >nul

echo Uninstall complete
echo If you are not concerned with keeping the backup ini file, feel free to delete the havoc-remote-main directory.
timeout /t 15 >nul

for /f %%F in ('dir /b /a-d ^| findstr /vile ".bak"') do del "%%F" >nul