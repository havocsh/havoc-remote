@echo off
FOR /F "tokens=* USEBACKQ" %%F IN (`cd`) DO (SET cwd=%%F)

echo Starting ./HAVOC remote_operator task installation:
echo - Downloading Python 3.10.10
c:\windows\system32\curl.exe -O -L -s https://www.python.org/ftp/python/3.10.10/python-3.10.10-embed-amd64.zip

echo - Extracting Python package contents
c:\windows\system32\windowspowershell\v1.0\powershell.exe Expand-Archive python-3.10.10-embed-amd64.zip
move python-3.10.10-embed-amd64\* . >nul
rmdir /S /Q python-3.10.10-embed-amd64 >nul
del python-3.10.10-embed-amd64.zip >nul

echo - Downloading pip installer
c:\windows\system32\curl.exe -O -L -s https://bootstrap.pypa.io/get-pip.py

echo - Running pip installer
python.exe get-pip.py --no-warn-script-location >nul
echo Lib\site-packages>> python310._pth

echo - Installing havoc-remote requirements to embedded Python environment
python.exe -m pip install -r requirements.txt --no-warn-script-location >nul

echo - Downloading havoc-pkg
c:\windows\system32\curl.exe -O -L -s https://github.com/havocsh/havoc-pkg/archive/refs/heads/endpoint_fix.zip

echo - Extracting havoc-pkg contents
c:\windows\system32\windowspowershell\v1.0\powershell.exe Expand-Archive endpoint_fix.zip -DestinationPath havoc-pkg

echo - Installing havoc-pkg to embedded Python environment
python.exe -m pip install havoc-pkg\havoc-pkg-endpoint_fix --no-warn-script-location >nul

echo - Downloading NSSM 2.24
c:\windows\system32\curl.exe -O -L -s https://nssm.cc/release/nssm-2.24.zip

echo - Extracting NSSM package contents
c:\windows\system32\windowspowershell\v1.0\powershell.exe Expand-Archive nssm-2.24.zip
del nssm-2.24.zip >nul

echo - Installing HavocRemoteOperator service
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe install HavocRemoteOperator "%cwd%\python.exe" """%cwd%\link.py"""
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppStdout "%cwd%\link.log"
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppStderr "%cwd%\link.log"
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppStdoutCreationDisposition 4
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppStderrCreationDisposition 4
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppRotateFiles 1
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppRotateOnline 0
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppRotateSeconds 86400
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe set HavocRemoteOperator AppRotateBytes 1048576

echo - Starting HavocRemoteOperator service
echo - & nssm-2.24\nssm-2.24\win64\nssm.exe start HavocRemoteOperator

echo Install complete
timeout /t 15 >nul