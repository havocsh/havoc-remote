#!/usr/bin/env bash

echo "Updating ./HAVOC remote operator task:"

echo " - Getting ./HAVOC version info."
requested_version=$(grep "requested_version = " .havoc/havoc.cfg | awk '{ print $NF }')
deployment_version=$(curl -s http://releases.havoc.sh/${requested_version}.html)
if [ -z "${deployment_version}" ]; then
    echo "Reqested version not found."
    exit
fi
perl -pi -e "s/deployment_version = .*/deployment_version = ${deployment_version}/g" .havoc/havoc.cfg

echo " - Applying updates for version ${deployment_version}."
echo " - Updating local files."
havoc_orig_hash=$(shasum -a 256 update.sh | awk '{ print $1 }')
git pull > /dev/null 2>&1
current_git_branch=$(git status | awk 'FNR == 1 { print $3 }')
target_git_branch=$(git branch --contains tags/${deployment_version} | awk '{ print $NF }')
if [[ ! ${current_git_branch} == ${target_git_branch} ]]; then
    git checkout ${target_git_branch}
fi
havoc_new_hash=$(shasum -a 256 update.sh | awk '{ print $1 }')
if [[ ! ${havoc_orig_hash} == ${havoc_new_hash} ]]; then
    echo ""
    echo "This update included a change to the update script."
    echo "The update script will restart so that the changes can take affect."
    echo "The update will continue automatically upon restart."
    echo ""
    exec ./update.sh
fi
echo " - Updating the ./HAVOC module."
./venv/bin/pip3 --disable-pip-version-check install -q "havoc @ git+https://github.com/havocsh/havoc-pkg.git@${deployment_version}" --upgrade --force-reinstall

echo " - Restarting the ./HAVOC remote operator task service."
systemctl restart havoc_remote.service

echo "Update complete."