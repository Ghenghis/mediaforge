# Windsurf Professional Configuration Guide
## Last Updated: December 2025

---

## Overview

This document outlines the complete professional Windsurf IDE configuration optimized for:
- Managing 100+ GitHub projects
- AI/ML development pipelines
- Python API development
- WPF/C# applications
- ComfyUI automation
- Multi-language development

---

## Configuration Files Created

### 1. Global Rules
**Location:** `~/.codeium/global_rules.md`

Applies to ALL workspaces. Contains:
- Code quality standards
- Automation requirements (no interactive prompts)
- Event handling guidelines
- Performance best practices
- Security practices
- Git conventions
- Windows/PowerShell specifics
- MCP server integration guidelines

### 2. Workspace Rules
**Location:** `c:\Users\Admin\civitai\.windsurf\rules\`

| File | Activation | Purpose |
|------|------------|---------|
| python-api.md | *.py files | FastAPI, port management, error handling |
| comfyui-integration.md | *comfyui*, *workflow* | Workflow validation, API integration |
| automation-scripts.md | *.ps1, *.bat, *scheduler* | Script standards, no prompts |
| wpf-development.md | *.cs, *.xaml | MVVM, event handling, async |
| testing-standards.md | *test*, *spec* | Test structure, mocking, coverage |

### 3. Ignore Files
**Location:** `c:\Users\Admin\civitai\.codeiumignore`
**Global:** `~/.codeium/.codeiumignore`

Excludes from AI indexing:
- Large model files (.safetensors, .ckpt, .pt)
- Dependencies (node_modules, venv, __pycache__)
- Build outputs (dist, build)
- Media files (video, audio)
- Databases (.db, .sqlite)
- Secrets (.env, .pem)

### 4. Settings.json Enhancements
**Location:** `%APPDATA%\Windsurf\User\settings.json`

Categories configured:
- Windsurf AI settings (autocomplete, supercomplete)
- CodeScene memory leak fix
- Editor performance optimizations
- Terminal enhancements
- File watcher exclusions
- Search optimizations
- Language-specific formatting (Python, JS, TS, PowerShell)
- Git enhancements

---

## Key Settings Explained

### Performance Optimizations
`json
"files.watcherExclude": { ... }  // Reduces CPU usage
"search.exclude": { ... }        // Faster searches
"editor.minimap.enabled": false  // Reduces memory
"files.maxMemoryForLargeFilesMB": 4096  // Handle large files
`

### AI Features
`json
"windsurf.autocompleteSpeed": "fast"
"windsurf.enableSupercomplete": true
"windsurf.enableTabToJump": true
"windsurf.enableAutocomplete": true
`

### Language Formatting
- **Python**: Black formatter, auto-organize imports
- **JavaScript/TypeScript**: Prettier, 2-space tabs
- **PowerShell**: 4-space tabs

---

## Recommended Extensions to Install

### Essential
1. **Python**: ms-python.python, ms-python.black-formatter
2. **Prettier**: esbenp.prettier-vscode
3. **Git**: GitLens (eamodio.gitlens)

### Optional but Recommended
- Material Icon Theme (pkief.material-icon-theme)
- Error Lens (usernamehw.errorlens)
- Thunder Client (rangav.vscode-thunder-client)

---

## Maintenance Commands

### Reload Settings
`Ctrl+Shift+P`  "Reload Window"

### Clear Extension Cache
`powershell
Remove-Item -Recurse "C:\Users\Admin\AppData\Roaming\Windsurf\User\workspaceStorage" -Force
`

### Verify Configuration
`powershell
Get-Content "C:\Users\Admin\AppData\Roaming\Windsurf\User\settings.json" | ConvertFrom-Json
`

---

## Troubleshooting

### Memory Issues
1. Check CodeScene is disabled: `codescene.enableAutoReview: false`
2. Verify file watcher exclusions are active
3. Close unused tabs and terminals

### Slow Indexing
1. Add large directories to .codeiumignore
2. Exclude model files (.safetensors, .ckpt)
3. Use workspace-specific ignore patterns

### AI Not Responding
1. Check internet connection
2. Verify Windsurf subscription status
3. Try reloading window

---

## Quick Reference

| Setting | Purpose |
|---------|---------|
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+,` | Settings |
| `Ctrl+` | Terminal |
| `Ctrl+L` | Open Cascade |
| `Ctrl+I` | Inline Cascade |

---

## Files Location Summary

| File | Path |
|------|------|
| Global Rules | ~/.codeium/global_rules.md |
| Settings | %APPDATA%\Windsurf\User\settings.json |
| Workspace Rules | .windsurf/rules/*.md |
| Workflows | .windsurf/workflows/*.md |
| Ignore | .codeiumignore |

---

*Configuration by Cascade AI - Optimized for professional development*
