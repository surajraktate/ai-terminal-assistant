# 🤖 AI Terminal Assistant  
*Your AI-powered Ubuntu terminal companion.*  

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)  
[![Debian Package](https://img.shields.io/badge/.deb-download-blue)](https://github.com/yourrepo/ai-terminal-assistant/releases)  

AI Terminal Assistant lets you **ask questions in natural language** and automatically runs the correct Linux commands — securely, with explanations.  

---

## ✨ Features  
- 🖥️ Run Linux commands with **AI-generated suggestions**  
- 🔒 Secure execution (auto-detects when shell is required)  
- ⚡ Streaming responses (feels like real-time "thinking…")  
- 📦 Debian package support (`.deb` installer)  
- 🛠️ Configurable via `config.yaml`  

---

## 🚀 Quick Start  

### Install (Debian/Ubuntu)  
```bash
# Download .deb from releases
sudo apt install ai-terminal-assistant.deb
```

### Run  
```bash
ai --config
```

💡 Example output:  
```
🔧 AI Terminal Assistant Configuration
==================================================

📡 API Configuration
The assistant needs an OpenAI API key to function.
Get your key from: https://platform.openai.com/api-keys
......
```

---

## ⚙️ Configuration  
Default config is stored at:  

```yaml
/etc/ai-terminal-assistant/config.yaml
```

You can customize:  
- **GPT model**  
- **Timeouts**  
- **Security filters**  

---

### Usage Example  
```
ai "Show me network out packet count in last hour"
```

``
============================================================
Request: Show me network out packet count in last hour
🤖 Generating command...
💻 Generated Command:
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ifconfig | grep 'TX packets' | awk '{print $3}'                                                                                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
⚡ Executing command...

✅ Command executed successfully
📤 Output:
╭──────────────────────────────────────────────────────────────────────────────────────────── Command Output ─────────────────────────────────────────────────────────────────────────────────────────────╮
│ 0                                                                                                                                                                                                       │
│ 8603                                                                                                                                                                                                    │
│ 80627                                                                                                                                                                                                   │
│                                                                                                                                                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

## 📂 Project Structure  

```
ai-terminal-assistant/
├── debian/           # Packaging files
├── usr/bin/ai        # CLI entrypoint
├── usr/lib/ai-terminal-assistant/
│   ├── ai_assistant.py
│   ├── config.py
│   ├── security.py
│   └── requirements.txt
├── etc/ai-terminal-assistant/config.yaml
├── Makefile
└── build-package.sh
```

---

## 🔒 Security  
- Runs commands with `shell=False` whenever possible  
- Detects dangerous operators (`|`, `>`, `&&`, etc.)  
- Prompts before running commands that **modify system state** (`sudo`, `apt install`, etc.)  

---

## 🧑‍💻 Development  

Clone and install dependencies:  
```bash
git clone https://github.com/surajraktate/ai-terminal-assistant.git
cd ai-terminal-assistant/usr/lib/ai-terminal-assistant
pip install -r requirements.txt
```

Run directly:  
```bash
python3 ai_assistant.py "find files larger than 1GB"
```

Build package:  
```bash
dpkg-buildpackage -us -uc
```

---

## ✅ Roadmap  
- [ ] Plugin system for custom commands  
- [ ] Multi-AI provider fallback  
- [ ] Rich TUI interface  

---

## 🤝 Contributing  
PRs welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).  

---

## 📜 License  
MIT © 2025 Suraj Raktate
