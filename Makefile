# Makefile for AI Terminal Assistant

PACKAGE_NAME = ai-terminal-assistant
VERSION = 1.0.0
ARCH = all

.PHONY: all build install clean test

all: build

# Build the Debian package
build:
	@echo "Building $(PACKAGE_NAME) package..."
	./build-package.sh

# Install locally for testing
install-local:
	@echo "Installing locally for development..."
	sudo mkdir -p /usr/lib/ai-terminal-assistant
	sudo cp -r usr/lib/ai-terminal-assistant/* /usr/lib/ai-terminal-assistant/
	sudo cp usr/bin/ai /usr/bin/ai
	sudo chmod +x /usr/bin/ai
	sudo mkdir -p /etc/ai-terminal-assistant
	sudo cp etc/ai-terminal-assistant/config.yaml /etc/ai-terminal-assistant/
	pip3 install --user openai rich python-dotenv pyyaml

# Uninstall local installation
uninstall-local:
	@echo "Removing local installation..."
	sudo rm -rf /usr/lib/ai-terminal-assistant
	sudo rm -f /usr/bin/ai
	sudo rm -rf /etc/ai-terminal-assistant

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf debian/ai-terminal-assistant*
	rm -rf dist/
	rm -f ../ai-terminal-assistant_*
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Test the package
test:
	@if command -v pytest >/dev/null; then \
		python3 -m pytest tests/ -v; \
	else \
		echo "pytest not found — skipping tests"; \
	fi

# Create directory structure
setup:
	@echo "Setting up directory structure..."
	mkdir -p usr/bin usr/lib/ai-terminal-assistant etc/ai-terminal-assistant
	mkdir -p debian tests dist

# Install dependencies for building
deps:
	@echo "Installing build dependencies..."
	sudo apt-get update
	sudo apt-get install -y debhelper dh-python python3-all python3-setuptools

# Quick install from built package
install:
	@if [ -f dist/ai-terminal-assistant_*.deb ]; then \
		echo "Installing AI Terminal Assistant..."; \
		sudo dpkg -i dist/ai-terminal-assistant_*.deb; \
		sudo apt-get install -f; \
	else \
		echo "Package not found. Run 'make build' first."; \
	fi

# Create a release
release: clean build
	@echo "Creating release..."
	tar czf ai-terminal-assistant-$(VERSION).tar.gz dist/ README.md
	@echo "Release created: ai-terminal-assistant-$(VERSION).tar.gz"