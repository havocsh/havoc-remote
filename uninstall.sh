#!/usr/bin/env bash

echo "Uninstalling ./HAVOC remote operator task:"
echo " - Stopping and removing havoc_remote service."
systemctl stop havoc_remote.service
systemctl disable havoc_remote.service
rm /etc/systemd/system/havoc_remote.service

echo " - Deleting local ./HAVOC remote operator task files."
cd $OLDPWD
rm -rf /opt/havoc_remote

echo "Uninstall complete."