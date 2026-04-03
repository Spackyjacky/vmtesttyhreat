# ThreatPad - SOC Incident Response Tool

## 🛡️ **What is ThreatPad?**
ThreatPad is a professional SOC (Security Operations Center) incident response application designed for cybersecurity analysts. It provides comprehensive IOC (Indicators of Compromise) handling, analysis tools, and incident documentation capabilities.

## 📦 **Executable Distribution**

### **File Information:**
- **Executable**: `ThreatPad.exe` (Windows) / `ThreatPad` (macOS/Linux)
- **Size**: ~10-25 MB
- **Requirements**: None - standalone executable
- **Installation**: Not required - just run the executable

### **First Run:**
1. Download the executable
2. Double-click to run (Windows may show security warning - click "More info" → "Run anyway")
3. The application will create configuration files in the same directory
4. No internet connection required - all features work offline

## 🎯 **Key Features**

### **IOC Processing:**
- **Defang/Refang**: Safely neutralize and restore IOCs
- **Extract IOCs**: Automatically identify IPs, domains, URLs, emails, hashes
- **Safe Copy**: Warns when copying potentially dangerous undefanged IOCs

### **Analysis Tools:**
- **Hashing**: Generate MD5, SHA1, SHA256 hashes
- **Hash Identification**: Identify hash types by length/format
- **Base64 Encoding/Decoding**: Essential for malware analysis

### **Productivity Features:**
- **Copy Pasta Snippets**: Quick incident response templates
- **Templates**: Full document templates for investigations
- **Dark Mode**: Professional dark theme with system detection
- **Multi-tab Interface**: Work on multiple incidents simultaneously
- **Auto-save**: Automatic session restoration

### **Professional Interface:**
- **Real-time Statistics**: Line/word/character counts, cursor position
- **Syntax Highlighting**: IOC types highlighted in different colors
- **Find/Replace**: Advanced text search and replacement
- **Session Management**: Restore work exactly where you left off

## 🚀 **Quick Start Guide**

### **Basic IOC Workflow:**
1. Open ThreatPad
2. Paste or type incident text containing IOCs
3. Use **Extract IOCs** to identify all indicators
4. Use **Defang** to make IOCs safe for sharing
5. Use **Copy Pasta** for quick incident response templates
6. Export results or save for later

### **Common Tasks:**
- **Hash a file name**: Select text → Tools → Hashing → Generate SHA256
- **Decode Base64**: Select encoded text → Tools → Encoding → Base64 Decode  
- **Create incident report**: Copy Pasta → Incident Header
- **Switch themes**: View → Toggle Dark Mode (or use system detection)

## ⚙️ **Settings & Configuration**

Access comprehensive settings via **Tools → Settings**:

### **Appearance Tab:**
- Theme options (Dark, Light, Follow System)
- Font family and size
- Line numbers, word wrap, syntax highlighting

### **Copy Pasta Tab:**
- Add/edit/delete text snippets
- Manage quick-insert templates
- Customize incident response workflows

### **General Tab:**
- Auto-save intervals
- Recent files management
- Application preferences

## 📁 **File Management**

### **Supported Formats:**
- **Open**: Text files (.txt), Markdown (.md), All files (*.*)
- **Save**: Any text format
- **Export IOCs**: CSV (.csv), JSON (.json), Text (.txt)

### **Session Files** (created automatically):
- `session.json` - Saves all open tabs and content
- `app_settings.json` - User preferences
- `copy_pasta_snippets.json` - Custom snippets
- `recent_files.txt` - Recent file history

## 🔐 **Security Features**

### **Safe by Design:**
- **No internet access required** - completely offline
- **Defanging warnings** - prevents accidental IOC exposure
- **Local processing only** - no data leaves your machine
- **Malware analysis safe** - designed for handling malicious indicators

### **Enterprise Ready:**
- Portable executable - no installation required
- Can run from USB drives or network shares
- No registry modifications
- Easy deployment across SOC teams

## 🆘 **Troubleshooting**

### **Common Issues:**
- **Antivirus alerts**: PyInstaller executables may trigger false positives
- **Slow startup**: Normal behavior - executable unpacks on first run
- **Missing features**: Ensure you're using the latest version

### **Performance Tips:**
- Keep text files under 10MB for optimal performance  
- Use "Clear" button to reset large documents
- Close unused tabs to free memory

### **Support:**
- Check `BUILD_INSTRUCTIONS.md` for technical details
- Review source code if modifications are needed
- No external dependencies - everything is self-contained

---

**ThreatPad** - Professional SOC incident response made simple.  
Built for cybersecurity analysts, by cybersecurity professionals.