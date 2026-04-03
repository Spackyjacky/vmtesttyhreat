# ThreatPad

A comprehensive SOC (Security Operations Center) incident notes application with enhanced IOC (Indicators of Compromise) handling capabilities.

## Features

- **Multi-tab text editor** with syntax highlighting for security artifacts
- **IOC Detection & Extraction**: Automatically identifies and extracts IPs, domains, URLs, emails, and file hashes
- **Defanging/Refanging**: Safely neutralize IOCs for sharing and communication
- **Safe Copy Protection**: Warns when copying potentially dangerous undefanged IOCs
- **Template System**: Quick insertion of pre-defined incident response templates
- **Session Management**: Automatically saves and restores your work
- **Dark Mode Support**: Eye-friendly interface for long investigation sessions
- **Find/Replace**: Advanced text search and replacement functionality
- **Export Capabilities**: Export IOCs to CSV, JSON, or text formats
- **Line Numbers**: Optional line numbering for better text navigation
- **Drag & Drop**: Easy file loading via drag and drop

## Installation

1. Clone this repository:
   ```bash
   git clone <repository_url>
   cd threatpad-py
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python threatpad.py
   ```

## Usage

### Basic Operations
- **Ctrl+N**: New tab
- **Ctrl+O**: Open file
- **Ctrl+S**: Save file
- **Ctrl+Shift+S**: Save as

### IOC Operations
- **Ctrl+D**: Defang IOCs in current text
- **Ctrl+R**: Refang IOCs in current text
- **Ctrl+I**: Extract and display all IOCs
- **Ctrl+E**: Export IOCs to file

### Text Operations
- **Ctrl+F**: Find text
- **Ctrl+H**: Find and replace
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo

### View Options
- Toggle dark mode for better visibility
- Toggle line numbers for easier reference
- Adjust font size for comfort
- Enable/disable syntax highlighting

## File Structure

- `threatpad.py` - Main application file
- `templates/` - Directory for incident response templates
- `requirements.txt` - Python dependencies
- `README.md` - This file

## IOC Types Supported

- IPv4 addresses
- IPv6 addresses
- Domain names
- URLs (HTTP/HTTPS)
- Email addresses
- File hashes (MD5, SHA1, SHA256)

## Configuration

The application automatically saves your preferences including:
- Window geometry and theme settings
- Recent files list
- Session state (open tabs and their content)
- Font preferences and view options

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve ThreatPad.

## License

This project is open source. See LICENSE file for details.