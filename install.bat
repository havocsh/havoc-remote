FOR /F "tokens=* USEBACKQ" %%F IN (`cd`) DO (SET cwd=%%F)

echo "Downloading Python 3.10.10"
c:\windows\system32\curl.exe -O -L https://www.python.org/ftp/python/3.10.10/python-3.10.10-embed-amd64.zip

echo "Extracting Python package contents"
c:\windows\system32\windowspowershell\v1.0\powershell.exe Expand-Archive python-3.10.10-embed-amd64.zip
move python-3.10.10-embed-amd64\* .
move python-3.10.10-embed-amd64\Lib .
move python-3.10.10-embed-amd64\Scripts .

echo "Downloading pip installer"
c:\windows\system32\curl.exe -O -L https://bootstrap.pypa.io/get-pip.py

echo "Running pip installer"
python.exe get-pip.py
echo Lib\site-packages>> python310._pth

echo "Installing havoc-remote requirements to embedded Python environment"
python.exe -m pip install -r requirements.txt

echo "Downloading havoc-pkg"
c:\windows\system32\curl.exe -O -L https://github.com/havocsh/havoc-pkg/archive/refs/heads/endpoint_fix.zip

echo "Extracting havoc-pkg contents"
c:\windows\system32\windowspowershell\v1.0\powershell.exe Expand-Archive endpoint_fix.zip -DestinationPath havoc-pkg

echo "Installing havoc-pkg to embedded Python environment"
python.exe -m pip install havoc-pkg\havoc-pkg-endpoint_fix

echo "Downloading NSSM 2.24"
c:\windows\system32\curl.exe -O -L https://nssm.cc/release/nssm-2.24.zip

echo "Extracting NSSM package contents"
c:\windows\system32\windowspowershell\v1.0\powershell.exe Expand-Archive nssm-2.24.zip

echo "Installing HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe install HavocRemoteOperator "%cwd%\python.exe" "%cwd%\link.py"

echo "Starting HavocRemoteOperator service"
nssm-2.24\nssm-2.24\win64\nssm.exe start HavocRemoteOperator

echo "Install complete"