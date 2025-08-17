# 🚀 Roadmap – AI Terminal Assistant  

This roadmap outlines the planned evolution of the project. Each version adds safety, usability, and power while keeping the assistant **lightweight and terminal-native**.  

---

## ✅ v1 – Core Release (MVP)
**Status:** Released 🎉  

- `.deb` installer for Ubuntu  
- Convert **natural language → safe Ubuntu shell commands**  
- Runs inside your **existing terminal** (no need to switch any custom terminals)  
- Works with OpenAI API (bring your own key)  -
- **Free mode** using our managed backend (limited requests per day)  

---

## 🔒 v2 – Safety & Better UX
**Goal:** Make the tool safe, trustworthy, and pleasant to use  

- [ ] **Dry Run Mode** → Show command, only execute after user confirms  
- [ ] **Explain Before Execute** → Plain-English summary of what the command will do  
- [ ] **Dangerous Command Warnings** (`rm -rf`, system-critical paths, fork bombs, etc.)  
- [ ] **Editable Suggestions** → User can tweak the command before execution  
- [ ] **History Context** → Assistant considers recent commands when generating new ones  
- [ ] **Copy-Only Mode** → Output command without executing (for cautious users)  

---

## 🌍 v3 – Expansion & Flexibility
**Goal:** Reach more users and make it extensible  

- [ ] **Multi-shell support** (Bash, Zsh, Fish, PowerShell)  
- [ ] **Cross-distro packaging** (.deb ✅, add .rpm, Snap, Flatpak)  
- [ ] **Plugin System** (e.g., Git helper, Docker helper, Kubernetes helper)  
- [ ] **Local Model Support** (Ollama, LM Studio → offline & private)  
- [ ] **Configurable Personality** (choose between “concise mode” and “verbose explanations”)  
- [ ] **Demo GIFs & Example Workflows** in README  

---

## 🛠️ v4 – Advanced Features (Future Ideas)
**Goal:** Power-user tools & learning assistant  

- [ ] **Contextual Help** → Explain output of commands (`df -h`, `ps aux`, etc.)  
- [ ] **Script Generation** → For multi-step tasks, output a bash script instead of a one-liner  
- [ ] **Auto-Cheatsheet** → Save executed commands + explanations into a Markdown “personal cheatsheet”  
- [ ] **Interactive TUI Mode** (optional) → like `htop` but for AI terminal interactions  
- [ ] **Community Extensions** → Enable easy sharing of plugins or prompts  

---

## ✨ How to Contribute
We welcome PRs, issues, and feature requests!  

- Pick up an open item from the roadmap  
- Suggest improvements  
- Add distro/OS support  
- Help test safety features  

👉 See [README.md](./README.md) for installation and usage instructions.
