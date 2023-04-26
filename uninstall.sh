#!/usr/bin/env bash

echo "Uninstalling ./HAVOC remote operator task:"
echo " - Stopping and removing havoc_remote service."
systemctl stop havoc_remote.service
systemctl disable havoc_remote.service
rm /etc/systemd/system/havoc_remote.service

echo "Uninstall complete."
echo "If you would like to remove all traces of the ./HAVOC remote operator task, delete the local havoc-remote directory."