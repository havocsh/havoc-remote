#!/usr/bin/env bash

git_bin=$(which git)
if [ ! "${git_bin}" ]; then
    echo "Could not find git. Please install git before continuing."
    exit
fi

python3_bin=$(which python3)
if [ ! "${python3_bin}" ]; then
    echo "Could not find python3. Please install python3 before continuing."
    exit
fi


echo "Installing ./HAVOC remote operator task:"
echo " - Creating directory structure in /opt/havoc_remote."
mkdir /opt/havoc_remote
shopt -s dotglob
cp -r * /opt/havoc_remote
shopt -u dotglob
cd /opt/havoc_remote
mkdir arsenal
mkdir data

echo " - Creating Python virtual environment."
${python3_bin} -m venv ./venv
pip_bin=./venv/bin/pip3

echo " - Getting ./HAVOC version info."
requested_version=$(grep "requested_version = " .havoc/havoc.cfg | awk '{ print $NF }')
deployment_version=$(curl -s http://releases.havoc.sh/${requested_version}.html)
if [ -z "${deployment_version}" ]; then
    echo "Reqested version not found."
    exit
fi
perl -pi -e "s/deployment_version = .*/deployment_version = ${deployment_version}/g" .havoc/havoc.cfg
echo " - Requested version: ${deployment_version}."
echo " - Installing requirements."
${pip_bin} --disable-pip-version-check install -q -r requirements.txt
echo " - Installing the ./HAVOC module."
${pip_bin} --disable-pip-version-check install -q "havoc @ git+https://github.com/havocsh/havoc-pkg.git@${deployment_version}"
current_git_branch=$(git status | awk 'FNR == 1 { print $3 }')
target_git_branch=$(git branch --contains tags/${deployment_version} | awk '{ print $NF }')
if [[ ! ${current_git_branch} == ${target_git_branch} ]]; then
    git checkout ${target_git_branch}
fi

echo " - Installing havoc_remote service."
cp havoc_remote.service /etc/systemd/system/havoc_remote.service
systemctl enable havoc_remote.service

echo "Installation complete."
echo "Modify /opt/havoc_remote/link.ini and start the ./HAVOC remote operator task service with the following command:"
echo "  systemctl start havoc_remote.service"