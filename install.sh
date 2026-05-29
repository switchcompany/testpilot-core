#!/bin/bash
# Forge Core CLI Installer
# Usage: curl -fsSL https://install.theswitchcompany.online | bash

set -euo pipefail

REPO="switchcompany/forge-core"
INSTALL_DIR="/usr/local/bin"
BINARY_NAME="forge-core"

# Detect OS and arch
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$OS" in
  linux)  PLATFORM="linux" ;;
  darwin) PLATFORM="darwin" ;;
  *)      echo "❌ Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
  x86_64)  ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *)       echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
esac

ARTIFACT="${BINARY_NAME}-${PLATFORM}-${ARCH}"

# Get latest release
echo "🔍 Finding latest Forge Core release..."
LATEST=$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name"' | cut -d'"' -f4)

if [ -z "$LATEST" ]; then
  echo "❌ Could not find latest release"
  exit 1
fi

echo "📦 Downloading Forge Core ${LATEST} for ${PLATFORM}/${ARCH}..."
DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${LATEST}/${ARTIFACT}"

# Download
if ! curl -fsSL -o "/tmp/${BINARY_NAME}" "$DOWNLOAD_URL"; then
  echo "❌ Download failed. Check https://github.com/${REPO}/releases"
  exit 1
fi

# Install
chmod +x "/tmp/${BINARY_NAME}"

if [ -w "$INSTALL_DIR" ]; then
  mv "/tmp/${BINARY_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
else
  echo "🔐 Installing to ${INSTALL_DIR} (requires sudo)..."
  sudo mv "/tmp/${BINARY_NAME}" "${INSTALL_DIR}/${BINARY_NAME}"
fi

echo ""
echo "✅ Forge Core ${LATEST} installed successfully!"
echo ""
echo "   Get started:"
echo "   $ forge-core login --token YOUR_API_TOKEN"
echo "   $ forge-core run ./your-project --target 90"
echo ""
echo "   Get your API token at: https://theswitchcompany.online/dashboard/settings"
