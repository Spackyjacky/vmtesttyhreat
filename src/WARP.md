# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

ThreatPad is a comprehensive SOC (Security Operations Center) incident notes application built with Python and Tkinter. It specializes in handling IOCs (Indicators of Compromise) with advanced detection, defanging/refanging, and export capabilities for cybersecurity professionals.

## Common Commands

### Running the Application
```bash
python threatpad.py
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode (if using setup.py)
pip install -e .
```

### Testing
```bash
# Run all tests
python -m unittest tests/test_threatpad.py

# Run specific test class
python -m unittest tests.test_threatpad.TestIOCPatterns

# Run with verbose output
python -m unittest tests/test_threatpad.py -v

# Run individual test method
python -m unittest tests.test_threatpad.TestIOCPatterns.test_ipv4_detection
```

### Code Quality
```bash
# Check Python syntax (if pylint installed)
python -m py_compile threatpad.py

# Basic code validation
python -c "import threatpad; print('Syntax OK')"
```

## Architecture Overview

### Core Components

1. **SOCNotesApp** - Main application class that orchestrates all functionality
2. **LineNumberText** - Custom text widget wrapper that adds line numbering capability
3. **Config** - Configuration management class for application settings

### Key Architecture Patterns

- **Single-file application**: The entire GUI application is contained in `threatpad.py` (~1300 lines)
- **Tkinter-based GUI**: Uses tkinter with ttk for modern styling and tkinterdnd2 for drag-drop
- **Tab-based interface**: Multiple document interface using ttk.Notebook
- **Regex-driven IOC detection**: All IOC patterns defined as compiled regex patterns
- **State persistence**: Automatic session saving/loading and settings management

### IOC Processing Pipeline

The application uses a sophisticated regex-based system for IOC handling:

```python
self.ioc_patterns = {
    'ipv4': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
    'ipv6': re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\\b::1\\b|\\b::\\b'),
    'domain': re.compile(r'\b[a-zA-Z0-9](?:[a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?)*\\.[a-zA-Z]{2,}\\b'),
    'url': re.compile(r'\bhttps?://[^\s<>"]{2,}\b', re.IGNORECASE),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'hash_md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
    'hash_sha1': re.compile(r'\b[a-fA-F0-9]{40}\b'),
    'hash_sha256': re.compile(r'\b[a-fA-F0-9]{64}\b'),
}
```

### Data Flow

1. **Input**: Text entered via tabs or file drag-and-drop
2. **Processing**: Real-time syntax highlighting and IOC detection
3. **Manipulation**: Defanging/refanging operations using regex substitution
4. **Output**: Export to CSV, JSON, or text formats
5. **Persistence**: Auto-save to session files and user settings

### File Management System

- **Session persistence**: `session.json` stores all open tabs and content
- **Settings management**: `app_settings.json` stores user preferences
- **Recent files**: `recent_files.txt` maintains file history
- **Templates**: Optional `templates/` directory for incident response templates
- **Custom dictionary**: `custom_dict.txt` for spell checking extensions

## Key Features to Understand

### Defanging/Refanging Logic
The application implements a sophisticated defanging system that safely neutralizes IOCs:
- URLs: `http://` → `hxxp[://]`
- IPs/Domains: `.` → `[.]`  
- Emails: `@` → `[@]`
- IPv6: `:` → `[:]`

### Safety Features
- **Safe Copy Protection**: Warns users before copying undefanged IOCs
- **Validation feedback**: Real-time feedback on copy operations
- **Confirmation dialogs**: For potentially dangerous operations

### Multi-format Export
Supports exporting detected IOCs to:
- CSV with Type/Value columns
- JSON with structured data
- Plain text with categorized lists

## Development Guidelines

### Code Style
- Follow the existing Tkinter patterns and widget organization
- Use the established regex patterns for IOC detection
- Maintain the existing error handling patterns with try/catch and messagebox
- Preserve the modular function organization by feature area

### Adding New IOC Types
1. Add regex pattern to `self.ioc_patterns` in `__init__`
2. Update syntax highlighting colors in `apply_syntax_highlighting`
3. Add defanging/refanging rules in respective methods
4. Update test cases in `tests/test_threatpad.py`

### UI Modifications
- Use the existing dark mode/light mode theming system
- Follow the established keybinding conventions (Ctrl+letter)
- Maintain the consistent button layout and menu structure
- Preserve the status bar update patterns

### Testing Strategy
- IOC pattern tests are in `TestIOCPatterns` class
- Defanging logic tests are in `TestDefanging` class
- Add new tests following the existing subTest pattern for multiple test cases

## Dependencies

The application has minimal external dependencies:
- **tkinter**: Built-in Python GUI framework
- **pyspellchecker**: Spell checking functionality
- **tkinterdnd2**: Drag and drop support for files

## Security Considerations

This application handles potentially malicious IOCs, so:
- Always validate regex patterns thoroughly
- Test defanging/refanging with real-world IOC samples
- Ensure safe copy warnings are properly triggered
- Validate file operations for malicious content

## File Structure Notes

- Single-file architecture keeps everything in `threatpad.py`
- Tests are isolated in `tests/` directory
- Configuration files are created at runtime in working directory
- Templates directory is optional and created on-demand