#!/bin/bash
set -e

echo "🏗️  Building AI Terminal Assistant Debian Package"

# Clean previous builds
rm -rf debian/ai-terminal-assistant*
rm -f ../ai-terminal-assistant_*.deb
rm -f ../ai-terminal-assistant_*.changes
rm -f ../ai-terminal-assistant_*.dsc
rm -f ../ai-terminal-assistant_*.tar.xz

# Create source package
dpkg-source --build .

# Build binary package
dpkg-buildpackage -us -uc -b

echo "✅ Package built successfully!"

# Move package to dist directory
mkdir -p dist
mv ../ai-terminal-assistant_*.deb dist/

echo "📦 Package available at: dist/ai-terminal-assistant_1.0.0-1_all.deb"
echo ""
echo "🚀 To install:"
echo "  sudo dpkg -i dist/ai-terminal-assistant_1.0.0-1_all.deb"
echo "  sudo apt-get install -f  # Fix any dependency issues"
echo ""
echo "🔧 After installation:"
echo "  ai --config              # Configure API key"
echo "  ai 'find python files'   # Test the assistant"