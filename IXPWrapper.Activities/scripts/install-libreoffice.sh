#!/bin/bash
# install-libreoffice.sh
# Run this script ONCE on your Linux robot template to install LibreOffice.
# Requires sudo / root privileges.

echo "Installing LibreOffice..."

apt-get update -y && apt-get install -y libreoffice

if [ $? -eq 0 ]; then
    echo "LibreOffice installed successfully."
    echo "soffice binary: $(which soffice)"
else
    echo "Installation failed. Try: sudo apt-get install -y libreoffice"
    exit 1
fi
