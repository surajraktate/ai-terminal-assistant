"""
Configuration management for AI Terminal Assistant
Author: surajraktate
"""

import os
import yaml
import getpass
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess


class ConfigManager:
    """Manages system and user configuration"""

    SYSTEM_CONFIG_PATH = Path("/etc/ai-terminal-assistant/config.yaml")
    USER_CONFIG_DIR = Path.home() / ".config" / "ai-terminal-assistant"
    USER_CONFIG_PATH = USER_CONFIG_DIR / "config.yaml"

    DEFAULT_CONFIG = {
        "api": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "timeout": 30,
            "max_tokens": 200
        },
        "security": {
            "require_confirmation": True,
            "block_dangerous_commands": True,
            "log_commands": True,
            "max_command_length": 1000
        },
        "ui": {
            "color_output": True,
            "show_progress": True,
            "truncate_output": 50
        }
    }

    def __init__(self):
        self.user_config_dir = self.USER_CONFIG_DIR
        self.user_config_path = self.USER_CONFIG_PATH
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure user config directory exists"""
        self.user_config_dir.mkdir(parents=True, exist_ok=True)
        # Set secure permissions
        os.chmod(self.user_config_dir, 0o700)

    def setup_config(self):
        """Interactive configuration setup"""
        print("🔧 AI Terminal Assistant Configuration")
        print("=" * 50)

        config = self.get_config()

        # API Key configuration
        print("\n📡 API Configuration")
        print("The assistant needs an OpenAI API key to function.")
        print("Get your key from: https://platform.openai.com/api-keys")

        current_key = self.get_api_key()
        if current_key:
            print(f"Current API key: {current_key[:8]}...{current_key[-4:]}")
            if input("Keep current API key? (y/N): ").lower() != 'y':
                current_key = None

        if not current_key:
            while True:
                api_key = getpass.getpass("Enter your OpenAI API key: ").strip()
                if api_key:
                    if self._validate_api_key(api_key):
                        self._store_api_key(api_key)
                        print("✅ API key validated and stored securely")
                        break
                    else:
                        print("❌ Invalid API key. Please try again.")
                else:
                    print("API key cannot be empty.")

        # Model selection
        print("\n🤖 Model Configuration")
        models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        current_model = config["api"]["model"]

        print(f"Current model: {current_model}")
        print("Available models:")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")

        choice = input(f"Select model (1-{len(models)}) or press Enter to keep current: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            config["api"]["model"] = models[int(choice) - 1]

        # Security settings
        print("\n🛡️  Security Configuration")

        confirm = input(f"Require confirmation for file operations? (Y/n): ").strip().lower()
        config["security"]["require_confirmation"] = confirm != 'n'

        dangerous = input(f"Block dangerous commands? (Y/n): ").strip().lower()
        config["security"]["block_dangerous_commands"] = dangerous != 'n'

        logging = input(f"Log all commands for security? (Y/n): ").strip().lower()
        config["security"]["log_commands"] = logging != 'n'

        # Save configuration
        self._save_config(config)
        print("\n✅ Configuration saved successfully!")
        print("\nYou can now use the AI assistant:")
        print("  ai 'find files containing error'")
        print("  ai 'show disk usage' --explain")
        print("  ai --interactive")

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key by making a test request"""
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            # Test with a minimal request
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False

    def _store_api_key(self, api_key: str):
        """Store API key securely"""
        key_file = self.user_config_dir / "api_key"
        with open(key_file, 'w') as f:
            f.write(api_key)
        # Secure permissions
        os.chmod(key_file, 0o600)

    def get_api_key(self) -> Optional[str]:
        """Get stored API key"""
        key_file = self.user_config_dir / "api_key"
        if key_file.exists():
            try:
                with open(key_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                return None
        return None

    def get_config(self) -> Dict[str, Any]:
        """Get merged configuration (system + user)"""
        config = self.DEFAULT_CONFIG.copy()

        # Load system config if exists
        if self.SYSTEM_CONFIG_PATH.exists():
            try:
                with open(self.SYSTEM_CONFIG_PATH, 'r') as f:
                    system_config = yaml.safe_load(f)
                    if system_config:
                        self._deep_merge(config, system_config)
            except Exception:
                pass

        # Load user config if exists
        if self.user_config_path.exists():
            try:
                with open(self.user_config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._deep_merge(config, user_config)
            except Exception:
                pass

        return config

    def _save_config(self, config: Dict[str, Any]):
        """Save user configuration"""
        with open(self.user_config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        os.chmod(self.user_config_path, 0o600)

    def _deep_merge(self, base: dict, override: dict):
        """Deep merge two dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def is_configured(self) -> bool:
        """Check if the assistant is properly configured"""
        return self.get_api_key() is not None

    def reset_config(self):
        """Reset configuration to defaults"""
        if self.user_config_path.exists():
            self.user_config_path.unlink()

        key_file = self.user_config_dir / "api_key"
        if key_file.exists():
            key_file.unlink()