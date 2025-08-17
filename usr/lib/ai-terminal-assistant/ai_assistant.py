"""
AI Terminal Assistant - Core functionality with enhanced interactive mode
Author: surajraktate
"""

import os
import sys
import json
import logging
import subprocess
import shlex
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

try:
    from openai import OpenAI
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Confirm
    from rich.syntax import Syntax
    from rich.logging import RichHandler
    from rich.markdown import Markdown
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please reinstall the package: sudo apt reinstall ai-terminal-assistant")
    sys.exit(1)

from config import ConfigManager
from security import CommandValidator, SecurityError, BackupManager

class AITerminalAssistant:
    """Main AI Terminal Assistant class"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        self.console = Console()
        self.validator = CommandValidator(self.config["security"])
        self.backup_manager = BackupManager()

        # Initialize OpenAI client
        api_key = self.config_manager.get_api_key()
        if not api_key:
            raise ValueError("No API key configured. Run: ai --config")

        self.client = OpenAI(api_key=api_key)
        self.logger = self._setup_logging()

        # Interactive mode conversation history
        self.conversation_history = []

    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path.home() / '.local' / 'share' / 'ai-terminal-assistant'
        log_dir.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger('ai_assistant')
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(log_dir / 'assistant.log')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)

        # Security log
        if self.config["security"]["log_commands"]:
            security_handler = logging.FileHandler(log_dir / 'security.log')
            security_handler.setFormatter(
                logging.Formatter('%(asctime)s - SECURITY - %(message)s')
            )
            logger.addHandler(security_handler)

        return logger

    def _get_command_system_prompt(self) -> str:
        """System prompt for command generation mode"""
        return """You are an expert Ubuntu/Linux system administrator and command generator. Convert natural language requests into safe, executable shell commands, including system configuration tasks.

CAPABILITIES:
- File operations (find, grep, copy, move, etc.)
- Process management (ps, top, kill, etc.)
- System information (df, free, uptime, etc.)
- Configuration editing (nginx, apache, bash, etc.)
- Package management (apt, snap, pip)
- Service management (systemctl, service)
- User and permission management
- Network configuration

SAFETY RULES:
1. Generate ONLY the command, no extra explanations unless requested
2. Use standard POSIX-compliant commands when possible
3. For system config editing, prefer nano/vim over dangerous commands
4. Always use appropriate sudo when needed for system files
5. Include safety flags when available (e.g., -i for interactive)

CONFIGURATION EDITING EXAMPLES:
User: "edit nginx config"
Assistant: sudo nano /etc/nginx/nginx.conf

User: "add alias to bash profile"
Assistant: nano ~/.bash_aliases

User: "edit apache virtual host"
Assistant: sudo nano /etc/apache2/sites-available/000-default.conf

User: "modify environment variables"
Assistant: sudo nano /etc/environment

User: "edit SSH config"
Assistant: nano ~/.ssh/config

User: "configure PHP settings"
Assistant: sudo nano /etc/php/8.1/apache2/php.ini

SYSTEM ADMINISTRATION EXAMPLES:
User: "restart nginx service"
Assistant: sudo systemctl restart nginx

User: "check nginx status"
Assistant: sudo systemctl status nginx

User: "install package"
Assistant: sudo apt install package-name

User: "create new user"
Assistant: sudo useradd -m username

User: "change file permissions"
Assistant: chmod 755 filename

Generate Ubuntu shell commands that accomplish the requested task safely and effectively."""

    def _get_interactive_system_prompt(self) -> str:
        """System prompt for interactive technical chat mode"""
        return """You are an expert technical assistant specializing in Linux/Ubuntu system administration, programming, DevOps, and technology in general. You can both answer technical questions conversationally AND generate executable commands when requested.

CONVERSATION MODE - Answer these types of questions naturally:
- Linux/Ubuntu system administration concepts and troubleshooting
- Programming languages, frameworks, and best practices  
- DevOps tools and methodologies (Docker, Kubernetes, CI/CD, etc.)
- Database administration and optimization
- Network configuration and security
- Web server setup and configuration
- Cloud platforms (AWS, Azure, GCP)
- Programming concepts and debugging help
- Software architecture and design patterns
- Technology explanations and comparisons

COMMAND MODE - Generate executable commands when user requests actions:
- "show me..." → Generate and offer to execute command
- "run this..." → Generate and offer to execute command  
- "check..." → Generate and offer to execute command
- "install..." → Generate and offer to execute command
- "configure..." → Generate and offer to execute command

RESPONSE GUIDELINES:
1. For technical discussions: Provide detailed, helpful explanations like ChatGPT
2. For command requests: Generate the command and ask if they want to execute it
3. Be conversational and educational
4. Include practical examples and best practices
5. Explain the "why" behind recommendations
6. Stay focused on technology topics

NON-TECHNICAL TOPICS:
Politely redirect non-technical questions: "I'm focused on technical topics. Is there a technology or system administration question I can help you with?"

COMMAND GENERATION:
When generating commands, use the same safety guidelines as before:
- Prefer safe, read-only operations when possible
- Use sudo when needed for system files
- Include appropriate safety flags
- Focus on standard Ubuntu/Linux commands"""

    def process_request(self, user_request: str, explain: bool = False) -> None:
        """Process a natural language request"""
        self.console.print("\n" + "="*60)
        self.console.print(f"[bold blue]Request:[/bold blue] {user_request}")

        # Log the request
        self.logger.info(f"User request: {user_request}")

        # Generate command
        self.console.print("[dim]🤖 Generating command...[/dim]")

        command_result = self._generate_command(user_request, explain)

        if not command_result["success"]:
            self.console.print(f"[red]❌ AI Error:[/red] {command_result.get('error', 'Unknown error')}")
            return

        command = command_result["command"]
        if not command:
            self.console.print("[red]❌ No command generated[/red]")
            return

        # Display command
        self.console.print(f"[green]💻 Generated Command:[/green]")
        syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
        self.console.print(Panel(syntax, border_style="green"))

        # Show explanation if available
        if explain and "explanation" in command_result:
            self.console.print(f"[blue]📋 Explanation:[/blue] {command_result['explanation']}")

        # Validate command
        try:
            validation = self.validator.validate_command(command)

            if not validation["valid"]:
                self.console.print(f"[red]🚫 Security Check Failed:[/red] {validation['reason']}")
                self.logger.warning(f"Command blocked: {command} - Reason: {validation['reason']}")
                return

            # Show risk level and details
            if validation["risk_level"] != "LOW":
                risk_color = {"MEDIUM": "yellow", "HIGH": "red", "CRITICAL": "red bold"}[validation["risk_level"]]
                self.console.print(f"[{risk_color}]⚠️  Risk Level: {validation['risk_level']}[/{risk_color}]")

            # Handle backup for config files
            backup_created = None
            if validation.get("backup_recommended", False) and validation.get("config_editing", {}).get("file_path"):
                file_path = validation["config_editing"]["file_path"]
                self.console.print(f"[blue]💾 Creating backup of {file_path}...[/blue]")
                backup_created = self.backup_manager.create_backup(file_path)
                if backup_created:
                    self.console.print(f"[green]✅ Backup created: {backup_created}[/green]")
                else:
                    self.console.print("[yellow]⚠️  Could not create backup (file may not exist yet)[/yellow]")

            # Enhanced confirmation for config editing
            if validation.get("needs_confirmation", False):
                confirmation_msg = f"[yellow]⚠️  {validation.get('confirmation_reason', 'This command requires confirmation')}[/yellow]"
                self.console.print(confirmation_msg)

                # Show additional info for config editing
                config_info = validation.get("config_editing", {})
                if config_info.get("is_config"):
                    if config_info.get("requires_sudo"):
                        self.console.print("[yellow]🔐 This command requires sudo privileges[/yellow]")
                    if config_info.get("is_critical"):
                        self.console.print("[red bold]⚠️  WARNING: Editing critical system file![/red bold]")
                        self.console.print("[red]Incorrect changes could break your system![/red]")

                if not Confirm.ask("Do you want to proceed?"):
                    self.console.print("[dim]Operation cancelled.[/dim]")
                    self.logger.info(f"Command cancelled by user: {command}")
                    return

            # Execute command
            self.console.print("[dim]⚡ Executing command...[/dim]")
            result = self._execute_command(command)

            # Log execution with enhanced details
            log_msg = f"Command executed: {command} - Success: {result['success']}"
            if validation.get("config_editing", {}).get("is_config"):
                log_msg += f" - Config file: {validation['config_editing']['file_path']}"
            if backup_created:
                log_msg += f" - Backup: {backup_created}"
            self.logger.info(log_msg)

            # Display results with backup info
            self._display_results(result, command, backup_created)

        except SecurityError as e:
            self.console.print(f"[red]🚫 Security Error:[/red] {e}")
            self.logger.error(f"Security error for command '{command}': {e}")

    def _generate_command(self, natural_language_request: str, explain: bool = False) -> Dict[str, Any]:
        """Generate command using OpenAI API"""
        try:
            messages = [
                {"role": "system", "content": self._get_command_system_prompt()},
                {"role": "user", "content": natural_language_request}
            ]

            if explain:
                messages.append({
                    "role": "user",
                    "content": "Also provide a brief explanation of what this command does."
                })

            response = self.client.chat.completions.create(
                model=self.config["api"]["model"],
                messages=messages,
                temperature=0,
                max_tokens=self.config["api"]["max_tokens"],
                timeout=self.config["api"]["timeout"]
            )

            content = response.choices[0].message.content.strip()

            # Parse response
            if explain and "Explanation:" in content:
                parts = content.split("Explanation:", 1)
                command = parts[0].strip()
                explanation = parts[1].strip()
            else:
                command = content
                explanation = None

            # Clean command
            if command.startswith('```') and command.endswith('```'):
                lines = command.split('\n')
                command = '\n'.join(lines[1:-1]) if len(lines) >= 3 else command

            result = {
                "success": True,
                "command": command,
                "model_used": self.config["api"]["model"]
            }

            if explanation:
                result["explanation"] = explanation

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute shell command safely"""

        def _needs_shell(command_str: str) -> bool:
            shell_ops = [
                "|",  # pipes
                ">", "<", ">>",  # redirection
                "&", "&&", "||",  # background / logical operators
                ";",  # command separator
                "$", "$( ", "${",  # variable and command substitution
                "*", "?", "~",  # globbing / tilde expansion
                "`"  # backticks for command substitution
            ]
            return any(op in command_str for op in shell_ops)
        try:
            command_parts = shlex.split(command)
            cmd_str = " ".join(command_parts)
            shell_mode = _needs_shell(cmd_str)
            if shell_mode:
                # Run using shell
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.config["api"]["timeout"],
                    check=False
                )
            else:
                # Run safely without shell
                result = subprocess.run(
                    command_parts,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=self.config["api"]["timeout"],
                    check=False
                )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {self.config['api']['timeout']} seconds",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def _display_results(self, result: Dict[str, Any], command: str, backup_path: str = None) -> None:
        """Display command execution results with backup information"""
        if result["success"]:
            self.console.print("[green]✅ Command executed successfully[/green]")

            # Show backup information if created
            if backup_path:
                self.console.print(f"[blue]💾 Original file backed up to: {backup_path}[/blue]")

            if result["stdout"]:
                output = result["stdout"]
                lines = output.split('\n')

                # Truncate if configured
                max_lines = self.config["ui"]["truncate_output"]
                if max_lines and len(lines) > max_lines:
                    output = '\n'.join(lines[:max_lines])
                    output += f"\n... (truncated, showing first {max_lines} lines of {len(lines)})"

                self.console.print("[blue]📤 Output:[/blue]")
                self.console.print(Panel(output, border_style="blue", title="Command Output"))

            if result["stderr"]:
                self.console.print("[yellow]⚠️  Warnings:[/yellow]")
                self.console.print(Panel(result["stderr"], border_style="yellow"))

        else:
            self.console.print("[red]❌ Command failed[/red]")

            if "error" in result:
                self.console.print(f"[red]Error:[/red] {result['error']}")

            if result.get("stderr"):
                self.console.print(Panel(result["stderr"], border_style="red", title="Error Details"))

            if "returncode" in result:
                self.console.print(f"[dim]Return code: {result['returncode']}[/dim]")

            # Offer backup restore if available
            if backup_path:
                self.console.print(f"[blue]💾 Backup available for restore: {backup_path}[/blue]")
                if Confirm.ask("Would you like to restore the backup?"):
                    if self.backup_manager.restore_backup(backup_path):
                        self.console.print("[green]✅ Backup restored successfully[/green]")
                    else:
                        self.console.print("[red]❌ Failed to restore backup[/red]")

    def _chat_response(self, user_message: str) -> Dict[str, Any]:
        """Generate conversational response for interactive mode"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Keep conversation history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            # Create messages for API call
            messages = [
                {"role": "system", "content": self._get_interactive_system_prompt()}
            ] + self.conversation_history

            response = self.client.chat.completions.create(
                model=self.config["api"]["model"],
                messages=messages,
                temperature=0.7,  # More conversational
                max_tokens=800,   # Longer responses for explanations
                timeout=self.config["api"]["timeout"]
            )

            assistant_message = response.choices[0].message.content.strip()

            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})

            return {
                "success": True,
                "response": assistant_message,
                "type": "conversation"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "type": "error"
            }

    def _detect_command_request(self, user_input: str) -> bool:
        """Detect if user is requesting a command to be executed"""
        command_indicators = [
            "show me", "list", "check", "run", "execute", "install", "remove",
            "start", "stop", "restart", "enable", "disable", "configure",
            "edit", "modify", "create", "delete", "copy", "move", "find",
            "search", "update", "upgrade", "download", "upload"
        ]

        user_lower = user_input.lower()

        # Check for direct command requests
        for indicator in command_indicators:
            if user_lower.startswith(indicator) or f" {indicator} " in user_lower:
                return True

        # Check for question words that often lead to commands
        if any(user_lower.startswith(q) for q in ["how do i", "how can i", "what command"]):
            return True

        return False

    def _extract_command_from_response(self, response_text: str) -> Optional[str]:
        """Extract executable command from AI response"""
        # Look for code blocks
        code_block_match = re.search(r'```(?:bash|shell)?\n?(.*?)\n?```', response_text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()

        # Look for inline code
        inline_code_match = re.search(r'`([^`]+)`', response_text)
        if inline_code_match:
            potential_command = inline_code_match.group(1).strip()
            # Check if it looks like a command (contains common command words)
            common_commands = ['ls', 'ps', 'df', 'grep', 'find', 'sudo', 'systemctl', 'apt', 'nano', 'vim']
            if any(cmd in potential_command.split() for cmd in common_commands):
                return potential_command

        return None

    def run_interactive(self):
        """Run in enhanced interactive mode with conversational AI"""
        self.console.print(Panel.fit(
            "[bold green]AI Terminal Assistant - Interactive Mode[/bold green]\n"
            "[blue]Technical ChatGPT + Command Execution[/blue]\n\n"
            "💬 Ask technical questions or request commands\n"
            "🔧 Linux, programming, DevOps, system administration\n"
            "⚡ Commands can be executed directly when offered\n\n"
            "Commands: 'help' for help, 'clear' to reset chat, 'quit' to exit",
            border_style="green"
        ))

        while True:
            try:
                user_input = self.console.input("\n[bold cyan]💬 You:[/bold cyan] ")

                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.console.print("[dim]Goodbye! 👋[/dim]")
                    break

                if user_input.lower() == 'clear':
                    self.conversation_history.clear()
                    self.console.print("[dim]🧹 Conversation history cleared[/dim]")
                    continue

                if user_input.lower() in ['help', 'h']:
                    self._show_interactive_help()
                    continue

                if not user_input.strip():
                    continue

                # Detect if this is a command request or conversational question
                is_command_request = self._detect_command_request(user_input)

                if is_command_request:
                    # Handle as command generation and potential execution
                    self.console.print("[dim]🤖 Generating command...[/dim]")

                    command_result = self._generate_command(user_input, explain=True)

                    if command_result["success"] and command_result["command"]:
                        command = command_result["command"]

                        # Display the command
                        self.console.print(f"\n[green]💻 Generated Command:[/green]")
                        syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
                        self.console.print(Panel(syntax, border_style="green"))

                        if "explanation" in command_result:
                            self.console.print(f"[blue]📋 Explanation:[/blue] {command_result['explanation']}")

                        # Ask if they want to execute it
                        if Confirm.ask("Would you like to execute this command?"):
                            self.process_request(user_input, explain=False)
                        else:
                            self.console.print("[dim]Command not executed.[/dim]")
                    else:
                        # Fallback to conversational mode
                        self._handle_conversation(user_input)

                else:
                    # Handle as conversational question
                    self._handle_conversation(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Use 'quit' to exit or 'clear' to reset conversation.[/dim]")
                continue
            except EOFError:
                break

    def _handle_conversation(self, user_input: str):
        """Handle conversational interaction"""
        self.console.print("[dim]🤖 Thinking...[/dim]")

        chat_result = self._chat_response(user_input)

        if chat_result["success"]:
            response = chat_result["response"]

            # Display the AI response
            self.console.print(f"\n[bold green]🤖 Assistant:[/bold green]")
            self.render_ai_response(response)

            # Check if the response contains an executable command
            command = self._extract_command_from_response(response)
            if command:
                self.console.print(f"\n[yellow]💡 I found a command in my response:[/yellow]")
                syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
                self.console.print(Panel(syntax, border_style="yellow"))

                if Confirm.ask("Would you like me to execute this command?"):
                    # Execute the extracted command
                    validation = self.validator.validate_command(command)

                    if not validation["valid"]:
                        self.console.print(f"[red]🚫 Security Check Failed:[/red] {validation['reason']}")
                        return

                    # Handle confirmation if needed
                    if validation.get("needs_confirmation", False):
                        self.console.print(f"[yellow]⚠️  {validation.get('confirmation_reason', 'Command requires confirmation')}[/yellow]")
                        if not Confirm.ask("Proceed with execution?"):
                            self.console.print("[dim]Command cancelled.[/dim]")
                            return

                    # Execute
                    result = self._execute_command(command)
                    self._display_results(result, command)
                else:
                    self.console.print("[dim]Command not executed.[/dim]")

        else:
            self.console.print(f"[red]❌ Error:[/red] {chat_result.get('error', 'Unknown error')}")

    def _show_help(self):
        """Show help information with configuration examples"""
        help_text = """
[bold green]AI Terminal Assistant Help[/bold green]

[blue]System Information:[/blue]
• "show disk usage"
• "which process uses most CPU?"
• "check memory usage"
• "show system uptime"

[blue]File Operations:[/blue]
• "find files containing 'error'"
• "list all python files"
• "copy file.txt to backup/"
• "change permissions of script.sh to executable"

[blue]Configuration Editing:[/blue]
• "edit nginx config"
• "modify apache virtual host"
• "add alias to bash profile"
• "edit SSH config"
• "configure PHP settings"
• "edit environment variables"

[blue]Service Management:[/blue]
• "restart nginx service"
• "check apache status"
• "enable auto-start for mysql"
• "stop redis service"

[blue]Package Management:[/blue]
• "install docker"
• "update package list"
• "remove old packages"
• "search for python packages"

[blue]Network Operations:[/blue]
• "check if google.com is reachable"
• "show network connections"
• "configure firewall rules"

[blue]Commands:[/blue]
• help, h - Show this help
• quit, exit, q - Exit interactive mode

[blue]Global Options:[/blue]
• ai --config - Configure settings and API key
• ai --explain - Include detailed explanations
• ai --interactive - Start interactive mode
• ai --backup-list - Show available backups
• ai --backup-restore - Restore configuration backups

[yellow]Safety Features:[/yellow]
• Automatic backups before editing config files
• Confirmation required for system modifications
• Security validation for all commands
• Comprehensive logging and audit trails

[green]Configuration Files Supported:[/green]
• Web servers: nginx, apache, httpd
• Databases: mysql, postgresql, redis
• Shell: .bashrc, .bash_aliases, .zshrc
• System: /etc/environment, /etc/hosts, /etc/fstab
• Applications: SSH, Git, PHP, Python configs

[red]Note:[/red] System configuration files require sudo privileges.
Backups are automatically created before modifications.
"""
        self.console.print(Panel(help_text, border_style="blue", title="Help"))

    def _show_interactive_help(self):
        """Show help for interactive mode"""
        help_text = """
[bold green]Interactive Mode Help[/bold green]

[blue]Conversational Questions (I'll explain and discuss):[/blue]
• "What's the difference between Docker and Podman?"
• "How does nginx load balancing work?"
• "Explain MySQL indexing strategies"
• "What are the best practices for securing SSH?"
• "How do I troubleshoot high CPU usage?"
• "What's the difference between systemd and init?"

[blue]Command Requests (I'll generate and offer to execute):[/blue]
• "Show me all running Docker containers"
• "Check nginx configuration syntax"
• "List all users on the system"
• "Find large files in /var/log"
• "Install Docker on Ubuntu"
• "Restart the Apache service"

[blue]Programming & DevOps Questions:[/blue]
• "How to optimize a slow SQL query?"
• "Best practices for Python error handling"
• "Explain Kubernetes pods vs deployments"
• "How to set up CI/CD with GitHub Actions?"
• "What's the difference between TCP and UDP?"

[blue]Interactive Commands:[/blue]
• help, h - Show this help
• clear - Reset conversation history
• quit, exit, q - Exit interactive mode

[green]Tips:[/green]
• Ask follow-up questions for deeper explanations
• Request examples: "show me an example"
• Ask for alternatives: "what other ways can I do this?"
• I maintain conversation context throughout the session

[yellow]Note:[/yellow] I focus on technical topics. For general questions, 
I'll politely redirect you to technical subjects.
"""
        self.console.print(Panel(help_text, border_style="blue", title="Interactive Help"))

    def render_ai_response(self, text: str):
        # Pattern to match fenced code blocks: ```lang\n ... \n```
        code_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)

        last_end = 0
        for match in code_pattern.finditer(text):
            # Print any normal text before this code block
            if match.start() > last_end:
                normal_text = text[last_end:match.start()].strip()
                if normal_text:
                    self.console.print(Markdown(normal_text))

            # Extract language and code
            lang = match.group(1) or "text"
            code = match.group(2).strip()

            # Show syntax-highlighted code
            syntax = Syntax(code, lang, theme="monokai", line_numbers=False)
            self.console.print(syntax)

            last_end = match.end()

        # Print remaining text after last code block
        if last_end < len(text):
            remaining_text = text[last_end:].strip()
            if remaining_text:
                self.console.print(Markdown(remaining_text))