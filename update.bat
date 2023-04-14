@echo off
FOR /F "tokens=* USEBACKQ" %%F IN (`cd`) DO (SET cwd=%%F)

echo Starting ./HAVOC remote_operator task update:
c:\windows\system32\curl.exe -O -L -s https://github.com/havocsh/havoc-remote/archive/refs/heads/main.zip

echo - Stopping HavocRemoteOperator service
nssm-2.24\nssm-2.24\win64\nssm.exe stop HavocRemoteOperator >nul

echo - Backing up link.ini to link.ini.bak
copy link.ini link.ini.bak /Y >nul

echo - Moving link.log to link_%date:~4,2%%date:~7,2%%date:~10,4%_%time:~0,2%%time:~3,2%%time:~6,2%.log
move link.log link_%date:~4,2%%date:~7,2%%date:~10,4%_%time:~0,2%%time:~3,2%%time:~6,2%.log

echo - Extracting ./HAVOC remote_operator update contents to temporary folder
c:\windows\system32\windowspowershell\v1.0\powershell.exe Expand-Archive main.zip -DestinationPath .

echo - Moving files
copy  havoc-remote-main\* .

echo - Restoring link.ini.bak to link.ini
copy link.ini.bak link.ini /Y >nul

echo - Deleting temporary ./HAVOC remote_operator update contents
rmdir havoc-remote-main
del main.zip

echo - Starting HavocRemoteOperator service
nssm-2.24\nssm-2.24\win64\nssm.exe start HavocRemoteOperator >nul

echo Update complete
timeout /t 15 >nul