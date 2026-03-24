#!/usr/bin/env bash
# UDC DesktopAgent — Desktop environment setup script.
# Installs Chrome, LibreOffice, fonts, and other desktop requirements on Ubuntu.

set -euo pipefail

echo "=== UDC DesktopAgent: Setting up desktop environment ==="

# Create required directories
mkdir -p /var/log/supervisor
mkdir -p /root/.vnc
mkdir -p /tmp/.X11-unix

# Set VNC password (empty for no-auth in dev; override in production)
x11vnc -storepasswd "" /root/.vnc/passwd 2>/dev/null || true

# Install additional fonts for international support
apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-ubuntu \
    && rm -rf /var/lib/apt/lists/*

# Configure LXDE defaults
mkdir -p /root/.config/pcmanfm/LXDE
mkdir -p /root/Desktop

# Set Chrome as default browser
update-alternatives --set x-www-browser /usr/bin/google-chrome-stable 2>/dev/null || true

echo "=== Desktop environment setup complete ==="
