"""
Security validation for AI Terminal Assistant
Author: surajraktate
"""

import re
import time
import shlex
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

class SecurityError(Exception):
    """Raised when a command fails security validation"""
    pass

class BackupManager:
    """Manages automatic backups of configuration files"""

    def __init__(self):
        self.backup_dir = Path.home() / '.local' / 'share' / 'ai-terminal-assistant' / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger('ai_assistant.backup')

    def create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of the specified file"""
        try:
            source_path = Path(file_path).expanduser().resolve()

            if not source_path.exists():
                return None

            # Create backup filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_filename = str(source_path).replace('/', '_').lstrip('_')
            backup_filename = f"{safe_filename}_{timestamp}"
            backup_path = self.backup_dir / backup_filename

            # Copy file to backup location
            import shutil
            shutil.copy2(source_path, backup_path)

            self.logger.info(f"Created backup: {source_path} -> {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Failed to create backup of {file_path}: {e}")
            return None

    def list_backups(self, file_path: str = None) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []

        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                # Parse backup filename
                parts = backup_file.name.split('_')
                if len(parts) >= 3:
                    timestamp = f"{parts[-2]}_{parts[-1]}"
                    original_path = '_'.join(parts[:-2]).replace('_', '/')
                    if not original_path.startswith('/'):
                        original_path = '/' + original_path

                    if file_path is None or original_path == file_path:
                        backups.append({
                            "original_path": original_path,
                            "backup_path": str(backup_file),
                            "timestamp": timestamp,
                            "size": backup_file.stat().st_size
                        })

        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    def restore_backup(self, backup_path: str, target_path: str = None) -> bool:
        """Restore a backup file"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return False

            if target_path is None:
                # Extract original path from backup filename
                parts = backup_file.name.split('_')
                target_path = '_'.join(parts[:-2]).replace('_', '/')
                if not target_path.startswith('/'):
                    target_path = '/' + target_path

            target_file = Path(target_path).expanduser()

            # Create backup of current file before restore
            if target_file.exists():
                self.create_backup(str(target_file))

            # Restore the backup
            import shutil
            shutil.copy2(backup_file, target_file)

            self.logger.info(f"Restored backup: {backup_path} -> {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore backup {backup_path}: {e}")
            return False

class CommandValidator:
    """Validates commands for security before execution"""

    def __init__(self, security_config: Dict[str, Any]):
        self.config = security_config
        self.logger = logging.getLogger('ai_assistant.security')

        # Commands that should never be executed without explicit override
        self.DANGEROUS_COMMANDS = {
            'dd', 'mkfs', 'fdisk', 'parted', 'shred', 'format', 'wipefs',
            'badblocks', 'fsck', 'cfdisk', 'init', 'shutdown', 'reboot',
            'halt', 'poweroff', 'passwd', 'userdel', 'groupdel'
        }

        # Extremely dangerous patterns that are always blocked
        self.CRITICAL_PATTERNS = [
            r'rm\s+-rf\s*/',           # rm -rf /
            r'rm\s+-rf\s+/\w+',        # rm -rf /important
            r'dd\s+if=.*of=/dev/[sh]d', # dd to disk
            r':\(\)\{\s*.*\|\s*.*&\s*\}:', # Fork bombs
            r'>\s*/dev/[sh]d',         # Writing to disk devices
            r'curl.*\|\s*sh',          # Curl pipe to shell
            r'wget.*\|\s*sh',          # Wget pipe to shell
            r'echo.*>\s*/etc/passwd',  # Writing to passwd
            r'echo.*>\s*/etc/shadow',  # Writing to shadow
        ]

        # Moderate risk patterns that require confirmation
        self.WARNING_PATTERNS = [
            r'rm\s+-r[f]?\s+',         # Recursive delete
            r'chmod\s+[0-7]{3}\s+/',   # Root permissions
            r'chown\s+.*:\s*/',        # Root ownership
            r'>\s*/etc/',              # Writing to /etc (configs)
            r'>\s*/var/',              # Writing to /var
            r'>\s*/usr/',              # Writing to /usr
            r'>\s*/boot/',             # Writing to /boot
        ]

        # Commands that modify system state and need confirmation
        self.CONFIRMATION_COMMANDS = {
            # File operations
            'cp', 'mv', 'ln', 'mkdir', 'touch', 'rm', 'rmdir',
            # Permission changes
            'chmod', 'chown', 'chgrp',
            # Archives
            'tar', 'unzip', 'gzip', 'gunzip', 'zip',
            # Text editors (for config editing)
            'nano', 'vim', 'vi', 'emacs', 'gedit',
            # Package management
            'apt', 'apt-get', 'dpkg', 'snap', 'pip', 'pip3',
            # Service management
            'systemctl', 'service', 'sudo',
            # Network configuration
            'iptables', 'ufw', 'netplan',
        }

        # Safe configuration files that can be edited
        self.SAFE_CONFIG_FILES = {
            # User configs
            '~/.bashrc', '~/.bash_aliases', '~/.bash_profile', '~/.profile',
            '~/.zshrc', '~/.zsh_aliases', '~/.vimrc', '~/.nanorc',
            '~/.gitconfig', '~/.ssh/config',

            # Application configs in user space
            '~/.config/', '~/.local/',

            # System configs (require sudo)
            '/etc/nginx/', '/etc/apache2/', '/etc/httpd/',
            '/etc/mysql/', '/etc/postgresql/',
            '/etc/redis/', '/etc/memcached/',
            '/etc/php/', '/etc/python3/',
            '/etc/environment', '/etc/hosts',
            '/etc/fstab', '/etc/crontab',
            '/etc/systemd/', '/etc/ufw/',
            '/etc/iptables/', '/etc/netplan/',
            '/etc/apt/', '/etc/yum.repos.d/',
        }

        # System-critical files that need extra caution
        self.CRITICAL_FILES = {
            '/etc/passwd', '/etc/shadow', '/etc/sudoers',
            '/etc/group', '/etc/gshadow', '/boot/',
            '/proc/', '/sys/', '/dev/'
        }

    def validate_command(self, command: str) -> Dict[str, Any]:
        """Validate command for security with enhanced config editing support"""
        command = command.strip()

        if not command:
            return {"valid": False, "reason": "Empty command"}

        if len(command) > self.config.get("max_command_length", 2000):  # Increased for config editing
            return {"valid": False, "reason": "Command too long"}

        # Parse command
        try:
            command_parts = shlex.split(command)
            if not command_parts:
                return {"valid": False, "reason": "Unable to parse command"}

            base_command = command_parts[0].lower()
        except ValueError as e:
            return {"valid": False, "reason": f"Invalid syntax: {e}"}

        # Check for critical patterns (always blocked)
        for pattern in self.CRITICAL_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                self.logger.error(f"BLOCKED CRITICAL PATTERN: {pattern} in command: {command}")
                return {
                    "valid": False,
                    "reason": "Critical security pattern detected - command blocked",
                    "risk_level": "CRITICAL"
                }

        # Check dangerous commands (blocked unless explicitly allowed)
        if self.config.get("block_dangerous_commands", True):
            if base_command in self.DANGEROUS_COMMANDS:
                self.logger.warning(f"Blocked dangerous command: {base_command}")
                return {
                    "valid": False,
                    "reason": f"Dangerous command blocked: {base_command}",
                    "risk_level": "HIGH"
                }

        # Check for warning patterns (require extra confirmation)
        warning_detected = False
        detected_pattern = None
        for pattern in self.WARNING_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                warning_detected = True
                detected_pattern = pattern
                break

        # Special handling for config file editing
        config_editing = self._is_config_editing_command(command, command_parts)

        # Determine confirmation requirements
        needs_confirmation = False
        confirmation_reason = []

        if base_command in self.CONFIRMATION_COMMANDS:
            needs_confirmation = True
            confirmation_reason.append(f"'{base_command}' modifies system state")

        if warning_detected:
            needs_confirmation = True
            confirmation_reason.append("potentially risky operation detected")

        if config_editing["is_config"]:
            needs_confirmation = True
            confirmation_reason.append(f"editing configuration file: {config_editing['file_path']}")

        # Check if editing critical system files
        if config_editing["is_critical"]:
            needs_confirmation = True
            confirmation_reason.append("CRITICAL SYSTEM FILE - extra caution required")

        # Determine risk level
        risk_level = "LOW"
        if config_editing["is_critical"]:
            risk_level = "HIGH"
        elif warning_detected or config_editing["is_config"]:
            risk_level = "MEDIUM"

        return {
            "valid": True,
            "reason": "Command validated",
            "risk_level": risk_level,
            "needs_confirmation": needs_confirmation and self.config.get("require_confirmation", True),
            "confirmation_reason": "; ".join(confirmation_reason),
            "base_command": base_command,
            "config_editing": config_editing,
            "warning_pattern": detected_pattern,
            "backup_recommended": config_editing["is_config"] or config_editing["is_critical"]
        }

    def _is_config_editing_command(self, command: str, command_parts: List[str]) -> Dict[str, Any]:
        """Detect if command is editing configuration files"""
        result = {
            "is_config": False,
            "is_critical": False,
            "file_path": None,
            "editor": None,
            "requires_sudo": False
        }

        if not command_parts:
            return result

        base_command = command_parts[0].lower()

        # Check for text editors
        editors = {'nano', 'vim', 'vi', 'emacs', 'gedit', 'code', 'subl'}
        if base_command in editors or base_command == 'sudo' and len(command_parts) > 1 and command_parts[1] in editors:
            result["editor"] = base_command

            # Find the file being edited
            for part in command_parts[1:]:
                if not part.startswith('-') and '/' in part or part.startswith('~') or part.endswith(('.conf', '.config', '.cfg', '.ini', '.yml', '.yaml', '.json')):
                    result["file_path"] = part
                    break

        # Check for redirection to config files
        elif '>' in command:
            output_match = re.search(r'>\s*([^\s&|;]+)', command)
            if output_match:
                result["file_path"] = output_match.group(1)

        # Check for echo/cat to config files
        elif base_command in ['echo', 'cat', 'printf'] and ('>' in command or '>>' in command):
            output_match = re.search(r'>+\s*([^\s&|;]+)', command)
            if output_match:
                result["file_path"] = output_match.group(1)

        if result["file_path"]:
            file_path = result["file_path"]

            # Check if it's a recognized config file
            for safe_path in self.SAFE_CONFIG_FILES:
                if file_path.startswith(safe_path.rstrip('/')):
                    result["is_config"] = True
                    break

            # Check if it's a critical system file
            for critical_path in self.CRITICAL_FILES:
                if file_path.startswith(critical_path.rstrip('/')):
                    result["is_critical"] = True
                    result["is_config"] = True
                    break

            # Check if it requires sudo (system paths)
            if file_path.startswith(('/etc/', '/var/', '/usr/', '/boot/', '/opt/')):
                result["requires_sudo"] = True
                result["is_config"] = True

        return result