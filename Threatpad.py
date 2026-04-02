import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font, simpledialog
try:
from spellchecker import SpellChecker
SPELL_CHECK_AVAILABLE = True
except ImportError:
SPELL_CHECK_AVAILABLE = False
SpellChecker = None
from tkinterdnd2 import DND_FILES, TkinterDnD
import re
import os
import json
from datetime import datetime
import csv
import hashlib
import base64
import platform
import subprocess
import threading
try:
from ioc_enrichment import IOCEnrichment
IOC_ENRICHMENT_AVAILABLE = True
except ImportError:
IOC_ENRICHMENT_AVAILABLE = False
IOCEnrichment = None

# ——————— Config ———————

class Config:
CUSTOM_DICT_FILE = “custom_dict.txt”
TEMPLATE_DIR = “templates”
RECENT_FILE = “recent_files.txt”
SESSION_FILE = “session.json”
SNIPPETS_FILE = “copy_pasta_snippets.json”
TEMPLATES_FILE = “templates.json”
MAX_RECENT = 10
DARK_MODE = False
FOLLOW_SYSTEM_THEME = False
LINE_NUMBERS = True
WORD_WRAP = True
FONT_SIZE = 12
FONT_FAMILY = “Consolas”
SYNTAX_HIGHLIGHTING = True
APP_DATA_FILE = “app_settings.json”
AUTO_SAVE_INTERVAL = 60000  # milliseconds
# API Keys for IOC enrichment
API_KEYS = {
‘virustotal’: ‘’,
‘abuseipdb’: ‘’
}

# ——————— System Theme Detection ———————

def get_system_theme():
“”“Detect system theme preference”””
try:
system = platform.system()
if system == “Windows”:
return get_windows_theme()
elif system == “Darwin”:  # macOS
return get_macos_theme()
elif system == “Linux”:
return get_linux_theme()
except Exception as e:
print(f”Error detecting system theme: {e}”)
return False  # Default to light theme

def get_windows_theme():
“”“Get Windows theme preference from registry”””
try:
import winreg
registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
key = winreg.OpenKey(registry, r”SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize”)
value, _ = winreg.QueryValueEx(key, “AppsUseLightTheme”)
winreg.CloseKey(key)
return value == 0  # 0 = dark theme, 1 = light theme
except (ImportError, OSError):
return False

def get_macos_theme():
“”“Get macOS theme preference”””
try:
result = subprocess.run(
[‘defaults’, ‘read’, ‘-g’, ‘AppleInterfaceStyle’],
capture_output=True, text=True, timeout=5
)
return ‘dark’ in result.stdout.lower()
except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
return False

def get_linux_theme():
“”“Get Linux theme preference (basic implementation)”””
try:
# Try to detect GNOME dark theme
result = subprocess.run(
[‘gsettings’, ‘get’, ‘org.gnome.desktop.interface’, ‘gtk-theme’],
capture_output=True, text=True, timeout=5
)
return ‘dark’ in result.stdout.lower()
except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
return False

class LineNumberText(tk.Frame):
“”“Text widget with line numbers”””
def **init**(self, parent, show_lines=True, **kwargs):
tk.Frame.**init**(self, parent)
self.show_lines = show_lines

```
    self.text = tk.Text(self, **kwargs)
    self.text.pack(side="right", fill="both", expand=True)
    
    if self.show_lines:
        self.line_numbers = tk.Text(self, width=4, padx=3, takefocus=0,
                                  border=0, state='disabled', wrap='none',
                                  font=kwargs.get('font', ('Consolas', 12)))
        self.line_numbers.pack(side="left", fill="y")
        
        # Bind events for line number updates
        self.text.bind('<KeyRelease>', self.update_line_numbers)
        self.text.bind('<ButtonRelease>', self.update_line_numbers)
        self.text.bind('<MouseWheel>', self.update_line_numbers)
        self.text.bind('<Configure>', self.update_line_numbers)
        
        # Sync scrolling
        self.text.config(yscrollcommand=self.on_text_scroll)
    
    self.update_line_numbers()

def on_text_scroll(self, *args):
    if self.show_lines:
        self.line_numbers.yview_moveto(args[0])

def update_line_numbers(self, event=None):
    if not self.show_lines:
        return
        
    self.line_numbers.config(state='normal')
    self.line_numbers.delete('1.0', 'end')
    
    line_count = int(self.text.index('end-1c').split('.')[0])
    line_numbers_string = "\n".join(str(i) for i in range(1, line_count + 1))
    self.line_numbers.insert('1.0', line_numbers_string)
    self.line_numbers.config(state='disabled')

def toggle_line_numbers(self):
    self.show_lines = not self.show_lines
    if self.show_lines:
        if not hasattr(self, 'line_numbers'):
            self.line_numbers = tk.Text(self, width=4, padx=3, takefocus=0,
                                      border=0, state='disabled', wrap='none')
        self.line_numbers.pack(side="left", fill="y", before=self.text)
        self.text.config(yscrollcommand=self.on_text_scroll)
    else:
        if hasattr(self, 'line_numbers'):
            self.line_numbers.pack_forget()
    self.update_line_numbers()
```

class SOCNotesApp:
def **init**(self):
self.root = TkinterDnD.Tk()
self.root.title(“ThreatPad”)
self.root.geometry(“1200x800”)

```
    # Initialize spell checker with error handling for PyInstaller
    self.spell = None
    if SPELL_CHECK_AVAILABLE:
        try:
            self.spell = SpellChecker()
        except (ValueError, FileNotFoundError, Exception) as e:
            print(f"Spell checker initialization failed: {e}")
            print("Spell checking features will be disabled.")
            self.spell = None
    self.tabs = {}
    self.config = Config()
    self.current_file_paths = {}  # Track file paths for each tab
    self.recent_files = []
    self.find_dialog = None
    
    # IOC patterns for better detection
    self.ioc_patterns = {
        'ipv4': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        'ipv6': re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|\b::1\b|\b::\b'),
        'domain': re.compile(r'\b[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b'),
        'url': re.compile(r'\bhttps?://[^\s<>"]{2,}\b', re.IGNORECASE),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'hash_md5': re.compile(r'\b[a-fA-F0-9]{32}\b'),
        'hash_sha1': re.compile(r'\b[a-fA-F0-9]{40}\b'),
        'hash_sha256': re.compile(r'\b[a-fA-F0-9]{64}\b'),
    }

    self.load_settings()
    self.load_custom_dictionary()
    self.load_recent_files()
    self.load_snippets()
    self.load_templates_data()
    
    # Initialize IOC enrichment if available
    self.enrichment_engine = None
    if IOC_ENRICHMENT_AVAILABLE:
        self.enrichment_engine = IOCEnrichment(api_keys=self.config.API_KEYS)
    
    self.setup_ui()
    self.setup_keybindings()
    self.setup_drag_drop()

    # Load previous session or start with one tab
    if not self.load_session():
        self.new_tab()

    # Setup auto-save
    self.auto_save()

# --------------------- Settings ---------------------
def load_settings(self):
    try:
        if os.path.exists(self.config.APP_DATA_FILE):
            with open(self.config.APP_DATA_FILE, 'r') as f:
                settings = json.load(f)
                self.config.DARK_MODE = settings.get('dark_mode', False)
                self.config.FOLLOW_SYSTEM_THEME = settings.get('follow_system_theme', False)
                self.config.LINE_NUMBERS = settings.get('line_numbers', True)
                self.config.WORD_WRAP = settings.get('word_wrap', True)
                self.config.FONT_SIZE = settings.get('font_size', 12)
                self.config.FONT_FAMILY = settings.get('font_family', 'Consolas')
                self.config.SYNTAX_HIGHLIGHTING = settings.get('syntax_highlighting', True)
                self.config.API_KEYS = settings.get('api_keys', {'virustotal': '', 'abuseipdb': ''})
        
        # Apply system theme if enabled
        if self.config.FOLLOW_SYSTEM_THEME:
            self.config.DARK_MODE = get_system_theme()
    except Exception as e:
        print(f"Error loading settings: {e}")

def save_settings(self):
    try:
        settings = {
            'dark_mode': self.config.DARK_MODE,
            'follow_system_theme': self.config.FOLLOW_SYSTEM_THEME,
            'line_numbers': self.config.LINE_NUMBERS,
            'word_wrap': self.config.WORD_WRAP,
            'font_size': self.config.FONT_SIZE,
            'font_family': self.config.FONT_FAMILY,
            'syntax_highlighting': self.config.SYNTAX_HIGHLIGHTING,
            'api_keys': self.config.API_KEYS
        }
        with open(self.config.APP_DATA_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_recent_files(self):
    try:
        if os.path.exists(self.config.RECENT_FILE):
            with open(self.config.RECENT_FILE, 'r') as f:
                self.recent_files = [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"Error loading recent files: {e}")

def save_recent_files(self):
    try:
        with open(self.config.RECENT_FILE, 'w') as f:
            for file in self.recent_files[:self.config.MAX_RECENT]:
                f.write(f"{file}\n")
    except Exception as e:
        print(f"Error saving recent files: {e}")

def add_recent_file(self, filepath):
    if filepath in self.recent_files:
        self.recent_files.remove(filepath)
    self.recent_files.insert(0, filepath)
    self.recent_files = self.recent_files[:self.config.MAX_RECENT]
    self.save_recent_files()
    self.update_recent_menu()

def load_session(self):
    try:
        if os.path.exists(self.config.SESSION_FILE):
            with open(self.config.SESSION_FILE, 'r') as f:
                session = json.load(f)
                for tab_data in session.get('tabs', []):
                    self.new_tab(tab_data['title'], tab_data['content'])
                    if tab_data.get('filepath'):
                        current = self.notebook.select()
                        self.current_file_paths[current] = tab_data['filepath']
                return len(session.get('tabs', [])) > 0
    except Exception as e:
        print(f"Error loading session: {e}")
    return False

def save_session(self):
    try:
        session = {'tabs': []}
        for frame in self.tabs:
            text_widget = self.tabs[frame].text if hasattr(self.tabs[frame], 'text') else self.tabs[frame]
            content = text_widget.get("1.0", "end-1c")
            raw_title = self.notebook.tab(frame, "text")
            # Strip the ✕ close-button suffix before saving
            title = raw_title.rstrip().rstrip("✕").rstrip()
            filepath = self.current_file_paths.get(frame)
            session['tabs'].append({
                'title': title,
                'content': content,
                'filepath': filepath
            })
        with open(self.config.SESSION_FILE, 'w') as f:
            json.dump(session, f)
    except Exception as e:
        print(f"Error saving session: {e}")

# --------------------- UI Setup ---------------------
def setup_ui(self):
    self.setup_menu()
    self.setup_notebook()
    self.setup_buttons()
    self.setup_status_bar()

    if self.config.DARK_MODE:
        self.apply_dark_mode()

def setup_menu(self):
    self.menubar = tk.Menu(self.root)
    self.root.config(menu=self.menubar)

    # File menu
    file_menu = tk.Menu(self.menubar, tearoff=0)
    file_menu.add_command(label="New Tab", command=self.new_tab, accelerator="Ctrl+N")
    file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
    file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
    file_menu.add_command(label="Save As...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
    file_menu.add_separator()
    
    # Recent files submenu
    self.recent_menu = tk.Menu(file_menu, tearoff=0)
    file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
    self.update_recent_menu()
    
    file_menu.add_separator()
    file_menu.add_command(label="Export IOCs...", command=self.export_iocs, accelerator="Ctrl+E")
    file_menu.add_separator()
    file_menu.add_command(label="Close Tab", command=self.close_tab, accelerator="Ctrl+W")
    file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")
    self.menubar.add_cascade(label="File", menu=file_menu)

    # Edit menu
    edit_menu = tk.Menu(self.menubar, tearoff=0)
    edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
    edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
    edit_menu.add_separator()
    edit_menu.add_command(label="Find...", command=self.show_find_dialog, accelerator="Ctrl+F")
    edit_menu.add_command(label="Replace...", command=self.show_replace_dialog, accelerator="Ctrl+H")
    edit_menu.add_separator()
    edit_menu.add_command(label="Defang IOCs", command=self.defang_text, accelerator="Ctrl+D")
    edit_menu.add_command(label="Refang IOCs", command=self.refang_text, accelerator="Ctrl+R")
    edit_menu.add_command(label="Extract IOCs", command=self.extract_iocs, accelerator="Ctrl+I")
    if IOC_ENRICHMENT_AVAILABLE:
        edit_menu.add_command(label="Enrich IOCs...", command=self.enrich_iocs, accelerator="Ctrl+Shift+E")
    self.menubar.add_cascade(label="Edit", menu=edit_menu)

    # Templates menu
    self.template_menu = tk.Menu(self.menubar, tearoff=0)
    self.update_templates_menu()
    self.menubar.add_cascade(label="Templates", menu=self.template_menu)
    
    # Copy Pasta menu
    self.copypasta_menu = tk.Menu(self.menubar, tearoff=0)
    self.update_copypasta_menu()
    self.menubar.add_cascade(label="Copy Pasta", menu=self.copypasta_menu)

    # View menu
    view_menu = tk.Menu(self.menubar, tearoff=0)
    view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)
    view_menu.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers)
    view_menu.add_command(label="Toggle Word Wrap", command=self.toggle_word_wrap)
    view_menu.add_command(label="Toggle Syntax Highlighting", command=self.toggle_syntax_highlighting)
    view_menu.add_separator()
    view_menu.add_command(label="Increase Font Size", command=self.increase_font_size, accelerator="Ctrl++")
    view_menu.add_command(label="Decrease Font Size", command=self.decrease_font_size, accelerator="Ctrl+-")
    self.menubar.add_cascade(label="View", menu=view_menu)
    
    # Tools menu
    tools_menu = tk.Menu(self.menubar, tearoff=0)
    
    # Hashing submenu
    hash_menu = tk.Menu(tools_menu, tearoff=0)
    hash_menu.add_command(label="Generate MD5", command=lambda: self.generate_hash('md5'))
    hash_menu.add_command(label="Generate SHA1", command=lambda: self.generate_hash('sha1'))
    hash_menu.add_command(label="Generate SHA256", command=lambda: self.generate_hash('sha256'))
    hash_menu.add_separator()
    hash_menu.add_command(label="Identify Hash Type", command=self.identify_hash_type)
    tools_menu.add_cascade(label="Hashing", menu=hash_menu)
    
    # Encoding submenu
    encode_menu = tk.Menu(tools_menu, tearoff=0)
    encode_menu.add_command(label="Base64 Encode", command=self.base64_encode)
    encode_menu.add_command(label="Base64 Decode", command=self.base64_decode)
    tools_menu.add_cascade(label="Encoding", menu=encode_menu)
    
    tools_menu.add_separator()
    tools_menu.add_command(label="Settings...", command=self.show_settings_window)
    self.menubar.add_cascade(label="Tools", menu=tools_menu)

def update_recent_menu(self):
    self.recent_menu.delete(0, "end")
    for filepath in self.recent_files:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            self.recent_menu.add_command(
                label=filename,
                command=lambda f=filepath: self.open_recent_file(f)
            )

def update_copypasta_menu(self):
    """Update the Copy Pasta menu with current snippets"""
    self.copypasta_menu.delete(0, "end")
    
    if hasattr(self, 'snippets') and self.snippets:
        for snippet_name in sorted(self.snippets.keys()):
            self.copypasta_menu.add_command(
                label=snippet_name,
                command=lambda name=snippet_name: self.insert_snippet(name)
            )
    else:
        self.copypasta_menu.add_command(label="No snippets available", state="disabled")
        
    self.copypasta_menu.add_separator()
    self.copypasta_menu.add_command(label="Manage Snippets...", command=self.show_settings_window)

def setup_notebook(self):
    self.notebook = ttk.Notebook(self.root)
    self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
    self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    # Bind click for X close button detection
    self.notebook.bind("<Button-1>", self.on_tab_click)

    # Middle-click to close tab
    self.notebook.bind("<Button-2>", self.on_tab_middle_click)

def _get_tab_index_at(self, event):
    """Return the tab index under the mouse, or None."""
    try:
        return self.notebook.index(f"@{event.x},{event.y}")
    except tk.TclError:
        return None

def on_tab_middle_click(self, event):
    """Close tab on middle-click."""
    idx = self._get_tab_index_at(event)
    if idx is not None:
        self._close_tab_by_index(idx)

def on_tab_click(self, event):
    """Detect clicks on the ✕ portion of a tab label and close that tab."""
    idx = self._get_tab_index_at(event)
    if idx is None:
        return
    tab_id = self.notebook.tabs()[idx]
    tab_label = self.notebook.tab(tab_id, "text")
    if tab_label.endswith("✕"):
        try:
            bbox = self.notebook.bbox(tab_id)
            if bbox:
                tab_x, _, tab_w, _ = bbox
                if event.x >= tab_x + tab_w - 20:
                    self._close_tab_by_index(idx)
        except tk.TclError:
            pass

def _close_tab_by_index(self, idx):
    """Close the tab at the given notebook index."""
    tab_id = self.notebook.tabs()[idx]
    current_frame = self.notebook.nametowidget(tab_id)
    text_widget = self.get_text_widget(current_frame)
    if text_widget:
        tab_text = text_widget.get("1.0", "end-1c")
        if tab_text.strip():
            if not messagebox.askyesno("Confirm", "Close tab without saving?"):
                return
    if current_frame in self.tabs:
        del self.tabs[current_frame]
    if tab_id in self.current_file_paths:
        del self.current_file_paths[tab_id]
    self.notebook.forget(tab_id)
    if len(self.tabs) == 0:
        self.new_tab()

def setup_buttons(self):
    self.frame_buttons = tk.Frame(self.root)
    self.frame_buttons.pack(fill="x", padx=5, pady=5)

    # Left side - IOC Operations
    left_frame = tk.Frame(self.frame_buttons)
    left_frame.pack(side="left")
    
    # IOC manipulation buttons — store refs so we can re-colour on theme change
    self.defang_btn = tk.Button(left_frame, text="Defang", command=self.defang_text, width=8)
    self.defang_btn.pack(side="left", padx=2)
    self.add_tooltip(self.defang_btn, "Defang IOCs to make them safe (Ctrl+D)")
    
    self.refang_btn = tk.Button(left_frame, text="Refang", command=self.refang_text, width=8)
    self.refang_btn.pack(side="left", padx=2)
    self.add_tooltip(self.refang_btn, "Refang IOCs to restore original form (Ctrl+R)")
    
    self.extract_btn = tk.Button(left_frame, text="Extract IOCs", command=self.extract_iocs, width=10)
    self.extract_btn.pack(side="left", padx=2)
    self.add_tooltip(self.extract_btn, "Extract and analyze IOCs from text (Ctrl+I)")
    
    self.clear_btn = tk.Button(left_frame, text="Clear", command=self.clear_text, width=8)
    self.clear_btn.pack(side="left", padx=2)
    self.add_tooltip(self.clear_btn, "Clear all text in current tab")

    # Right side - Copy and Status
    right_frame = tk.Frame(self.frame_buttons)
    right_frame.pack(side="right")
    
    self.validation_label = tk.Label(right_frame, text="", width=15, anchor="e")
    self.validation_label.pack(side="right", padx=5)
    
    self.copy_button = tk.Button(
        right_frame, text="Safe Copy", command=self.safe_copy_text,
        width=10
    )
    self.copy_button.pack(side="right", padx=2)
    self.add_tooltip(self.copy_button, "Copy text with IOC safety warnings")

    self.update_button_colors()

def add_tooltip(self, widget, text):
    """Add tooltip to widget"""
    def on_enter(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        label = tk.Label(tooltip, text=text, background="#ffffe0", 
                       font=("Arial", 9), borderwidth=1, relief="solid")
        label.pack()
        widget.tooltip = tooltip
    
    def on_leave(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
    
    widget.bind('<Enter>', on_enter)
    widget.bind('<Leave>', on_leave)

def update_button_colors(self):
    if self.config.DARK_MODE:
        btn_bg = "#404040"
        btn_fg = "#ffffff"
        btn_active_bg = "#555555"
        btn_active_fg = "#ffffff"
    else:
        btn_bg = "SystemButtonFace"
        btn_fg = "#000000"
        btn_active_bg = "#e1e1e1"
        btn_active_fg = "#000000"

    # Apply to all standard bottom-bar buttons
    for btn in (self.defang_btn, self.refang_btn, self.extract_btn, self.clear_btn):
        btn.config(
            bg=btn_bg, fg=btn_fg,
            activebackground=btn_active_bg, activeforeground=btn_active_fg
        )

    # Safe Copy keeps its green background with readable white text in both modes
    self.copy_button.config(
        bg="#4CAF50", fg="#ffffff",
        activebackground="#388E3C", activeforeground="#ffffff"
    )

def setup_status_bar(self):
    self.status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
    self.status_bar.pack(side="bottom", fill="x")
    self.status_left = tk.Label(self.status_bar, text="Ready", anchor="w")
    self.status_left.pack(side="left", padx=5)
    self.status_right = tk.Label(self.status_bar, text="", anchor="e")
    self.status_right.pack(side="right", padx=5)

def setup_keybindings(self):
    self.root.bind('<Control-n>', lambda e: self.new_tab())
    self.root.bind('<Control-o>', lambda e: self.open_file())
    self.root.bind('<Control-s>', lambda e: self.save_file())
    self.root.bind('<Control-Shift-S>', lambda e: self.save_file_as())
    self.root.bind('<Control-w>', lambda e: self.close_tab())
    self.root.bind('<Control-q>', lambda e: self.on_closing())
    self.root.bind('<Control-f>', lambda e: self.show_find_dialog())
    self.root.bind('<Control-h>', lambda e: self.show_replace_dialog())
    self.root.bind('<Control-d>', lambda e: self.defang_text())
    self.root.bind('<Control-r>', lambda e: self.refang_text())
    self.root.bind('<Control-i>', lambda e: self.extract_iocs())
    self.root.bind('<Control-e>', lambda e: self.export_iocs())
    if IOC_ENRICHMENT_AVAILABLE:
        self.root.bind('<Control-Shift-E>', lambda e: self.enrich_iocs())
    self.root.bind('<Control-z>', lambda e: self.undo())
    self.root.bind('<Control-y>', lambda e: self.redo())
    self.root.bind('<Control-plus>', lambda e: self.increase_font_size())
    self.root.bind('<Control-minus>', lambda e: self.decrease_font_size())
    self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

def setup_drag_drop(self):
    self.root.drop_target_register(DND_FILES)
    self.root.dnd_bind('<<Drop>>', self.on_drop)

def on_drop(self, event):
    files = event.data.split()
    for file in files:
        file = file.strip('{}')  # Remove braces if present
        if os.path.isfile(file):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                self.new_tab(os.path.basename(file), content)
                current = self.notebook.select()
                self.current_file_paths[current] = file
                self.add_recent_file(file)
                self.update_status(f"Opened {file}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open {file}: {e}")

# --------------------- Tabs ---------------------
def new_tab(self, title="Untitled", content=""):
    frame = tk.Frame(self.notebook)
    
    # Create text widget with line numbers
    text_frame = LineNumberText(
        frame, 
        show_lines=self.config.LINE_NUMBERS,
        wrap="word" if self.config.WORD_WRAP else "none",
        undo=True,
        font=(self.config.FONT_FAMILY, self.config.FONT_SIZE)
    )
    
    text_frame.text.insert("1.0", content)
    text_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Bind text change events for syntax highlighting and status updates
    text_frame.text.bind('<KeyRelease>', self.on_text_change_event)
    text_frame.text.bind('<ButtonRelease>', self.on_text_change_event)
    text_frame.text.bind('<FocusIn>', self.on_text_focus)
    text_frame.text.bind('<Motion>', self.on_cursor_move)
    
    # Add tab with ✕ close button in title
    tab_title = f"{title}  ✕"
    self.notebook.add(frame, text=tab_title)
    self.notebook.select(frame)
    self.tabs[frame] = text_frame
    self.current_file_paths[frame] = None
    
    # Initial syntax highlighting
    if self.config.SYNTAX_HIGHLIGHTING:
        self.apply_syntax_highlighting(text_frame.text)

def close_tab(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    tab_text = text_widget.get("1.0", "end-1c")
    
    if tab_text.strip():
        if not messagebox.askyesno("Confirm", "Close tab without saving?"):
            return
    
    if current_frame in self.tabs:
        del self.tabs[current_frame]
    if current in self.current_file_paths:
        del self.current_file_paths[current]
    self.notebook.forget(current)
    
    # If no tabs left, create a new one
    if len(self.tabs) == 0:
        self.new_tab()

def on_tab_changed(self, event):
    self.update_status("Tab changed")

def get_text_widget(self, frame):
    """Get the actual text widget from frame (handles LineNumberText wrapper)"""
    if frame in self.tabs:
        text_container = self.tabs[frame]
        if hasattr(text_container, 'text'):
            return text_container.text
        else:
            return text_container
    return None

# --------------------- File Handling ---------------------
def open_file(self):
    filepath = filedialog.askopenfilename(
        filetypes=[
            ("Text Files", "*.txt"),
            ("Markdown Files", "*.md"),
            ("All Files", "*.*")
        ]
    )
    if not filepath:
        return
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.new_tab(os.path.basename(filepath), content)
        current = self.notebook.select()
        self.current_file_paths[current] = filepath
        self.add_recent_file(filepath)
        self.update_status(f"Opened {filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file: {e}")

def open_recent_file(self, filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.new_tab(os.path.basename(filepath), content)
        current = self.notebook.select()
        self.current_file_paths[current] = filepath
        self.update_status(f"Opened {filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open file: {e}")

def save_file(self):
    current = self.notebook.select()
    if not current:
        return
    
    filepath = self.current_file_paths.get(current)
    if not filepath:
        return self.save_file_as()
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        self.update_status(f"Saved {filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save file: {e}")

def save_file_as(self):
    current = self.notebook.select()
    if not current:
        return
    
    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[
            ("Text Files", "*.txt"),
            ("Markdown Files", "*.md"),
            ("All Files", "*.*")
        ]
    )
    if not filepath:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        # Keep ✕ suffix on renamed tab
        self.notebook.tab(current, text=f"{os.path.basename(filepath)}  ✕")
        self.current_file_paths[current] = filepath
        self.add_recent_file(filepath)
        self.update_status(f"Saved as {filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save file: {e}")

# --------------------- IOC Handling ---------------------
def defang_text(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")

    # Defang URLs first (to avoid double defanging)
    text = re.sub(r"https://", "hxxps[://]", text, flags=re.IGNORECASE)
    text = re.sub(r"http://", "hxxp[://]", text, flags=re.IGNORECASE)

    # Defang emails (must happen before domain/IP dot defanging)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    def defang_email(match):
        return match.group().replace('@', '[@]')
    text = re.sub(email_pattern, defang_email, text)

    # More precise IPv6 defanging - only defang actual IPv6 addresses
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b'
    def defang_ipv6(match):
        return match.group().replace(':', '[:]')
    text = re.sub(ipv6_pattern, defang_ipv6, text)

    # Defang dots in domains/IPs
    domain_pattern = r'\b[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+\b'
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    
    def defang_dots(match):
        return match.group().replace('.', '[.]')
    
    text = re.sub(domain_pattern, defang_dots, text)
    text = re.sub(ip_pattern, defang_dots, text)

    # Defang hash/fragment symbols
    text = text.replace('#', '[#]')

    # Defang @ symbols adjacent to # (e.g. @#channel, user@#tag)
    # After # is already replaced with [#], catch @ next to [#]
    text = re.sub(r'@(?=\[#\])', '[@]', text)   # @ immediately before [#]
    text = re.sub(r'(?<=\[#\])@', '[@]', text)  # @ immediately after [#]

    # Pass 2: catch-all — any @ not yet wrapped as [@]
    # Covers no-TLD emails (user@domain), bare @ mid-sentence, and any
    # address format where Pass 1 regex did not match (e.g. # in local-part).
    text = re.sub(r'(?<!\[)@(?!\])', '[@]', text)

    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", text)
    
    if self.config.SYNTAX_HIGHLIGHTING:
        self.apply_syntax_highlighting(text_widget)
    
    self.update_status("Defanged IOCs")

def refang_text(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")

    # Refang URLs
    text = re.sub(r"hxxps\[\:\/\/\]", "https://", text, flags=re.IGNORECASE)
    text = re.sub(r"hxxp\[\:\/\/\]", "http://", text, flags=re.IGNORECASE)

    # Refang dots
    text = text.replace("[.]", ".")

    # Refang @ symbols
    text = text.replace("[@]", "@")

    # Refang IPv6 colons
    text = text.replace("[:]", ":")

    # Refang hash/fragment symbols
    text = text.replace("[#]", "#")

    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", text)
    
    if self.config.SYNTAX_HIGHLIGHTING:
        self.apply_syntax_highlighting(text_widget)
    
    self.update_status("Refanged IOCs")

def extract_iocs(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")
    
    # Extract IOCs using patterns
    iocs = {}
    for ioc_type, pattern in self.ioc_patterns.items():
        matches = pattern.findall(text)
        if matches:
            iocs[ioc_type] = list(set(matches))  # Remove duplicates
    
    # Display in new window
    self.show_ioc_window(iocs)

def show_ioc_window(self, iocs):
    window = tk.Toplevel(self.root)
    window.title("Extracted IOCs")
    window.geometry("600x400")
    
    # Create treeview
    tree = ttk.Treeview(window, columns=("Type", "Value"), show="tree headings")
    tree.heading("#0", text="")
    tree.heading("Type", text="Type")
    tree.heading("Value", text="Value")
    tree.column("#0", width=50)
    tree.column("Type", width=150)
    tree.column("Value", width=400)
    
    # Add IOCs to tree
    for ioc_type, values in iocs.items():
        parent = tree.insert("", "end", text="", values=(ioc_type.upper(), f"{len(values)} found"))
        for value in sorted(values):
            tree.insert(parent, "end", text="", values=("", value))
    
    tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Add export button
    export_frame = tk.Frame(window)
    export_frame.pack(fill="x", padx=10, pady=5)
    
    tk.Button(export_frame, text="Export to CSV", 
             command=lambda: self.export_iocs_from_dict(iocs)).pack(side="right")

def export_iocs(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")
    
    # Extract IOCs
    iocs = {}
    for ioc_type, pattern in self.ioc_patterns.items():
        matches = pattern.findall(text)
        if matches:
            iocs[ioc_type] = list(set(matches))
    
    self.export_iocs_from_dict(iocs)

def export_iocs_from_dict(self, iocs):
    if not iocs:
        messagebox.showinfo("No IOCs", "No IOCs found to export.")
        return
    
    filepath = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[
            ("CSV Files", "*.csv"),
            ("JSON Files", "*.json"),
            ("Text Files", "*.txt")
        ]
    )
    
    if not filepath:
        return
    
    try:
        if filepath.endswith('.csv'):
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Type', 'Value'])
                for ioc_type, values in iocs.items():
                    for value in values:
                        writer.writerow([ioc_type.upper(), value])
        
        elif filepath.endswith('.json'):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(iocs, f, indent=2)
        
        else:  # .txt
            with open(filepath, 'w', encoding='utf-8') as f:
                for ioc_type, values in iocs.items():
                    f.write(f"{ioc_type.upper()}:\n")
                    for value in values:
                        f.write(f"  {value}\n")
                    f.write("\n")
        
        self.update_status(f"IOCs exported to {filepath}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Could not export IOCs: {e}")

def enrich_iocs(self):
    """Extract and enrich IOCs with threat intelligence"""
    if not IOC_ENRICHMENT_AVAILABLE or not self.enrichment_engine:
        messagebox.showerror("Error", "IOC enrichment not available. Make sure 'requests' library is installed.")
        return
    
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")
    
    # Extract IOCs using patterns
    iocs = {}
    for ioc_type, pattern in self.ioc_patterns.items():
        matches = pattern.findall(text)
        if matches:
            iocs[ioc_type] = list(set(matches))  # Remove duplicates
    
    if not iocs:
        messagebox.showinfo("No IOCs", "No IOCs found in the current text.")
        return
    
    # Show enrichment window
    self.show_enrichment_window(iocs)

def show_enrichment_window(self, iocs):
    """Display IOC enrichment window with threat intelligence"""
    window = tk.Toplevel(self.root)
    window.title("IOC Enrichment")
    window.geometry("900x600")
    window.transient(self.root)
    
    # Create main frame
    main_frame = tk.Frame(window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Top info frame
    info_frame = tk.Frame(main_frame)
    info_frame.pack(fill="x", pady=(0, 10))
    
    total_iocs = sum(len(values) for values in iocs.values())
    tk.Label(info_frame, text=f"Found {total_iocs} IOCs ready for enrichment", 
            font=("Arial", 11, "bold")).pack(side="left")
    
    # Progress bar
    progress_frame = tk.Frame(main_frame)
    progress_frame.pack(fill="x", pady=(0, 10))
    
    progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
    progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    progress_label = tk.Label(progress_frame, text="Ready", width=30, anchor="w")
    progress_label.pack(side="left")
    
    # Create notebook for different IOC types
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, pady=(0, 10))
    
    # Results storage
    enrichment_results = {}
    
    # Create tabs for each IOC type
    for ioc_type, values in iocs.items():
        if not values:
            continue
        
        frame = tk.Frame(notebook)
        notebook.add(frame, text=f"{ioc_type.upper()} ({len(values)})")
        
        # Create scrolled text widget for results
        text_widget = tk.Text(frame, wrap="word", font=("Courier", 10))
        scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)
        
        # Store reference
        enrichment_results[ioc_type] = {
            'text_widget': text_widget,
            'data': []
        }
    
    # Buttons frame
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill="x")
    
    def start_enrichment():
        """Start the enrichment process in a thread"""
        enrich_btn.config(state="disabled")
        export_btn.config(state="disabled")
        
        def progress_callback(current, total, message):
            progress_bar['value'] = (current / total) * 100
            progress_label.config(text=message)
            window.update_idletasks()
        
        def enrichment_thread():
            try:
                results = self.enrichment_engine.enrich_iocs_batch(iocs, progress_callback)
                window.after(0, lambda: display_results(results))
            except Exception as e:
                window.after(0, lambda: messagebox.showerror("Error", f"Enrichment failed: {e}"))
            finally:
                window.after(0, lambda: enrich_btn.config(state="normal"))
                window.after(0, lambda: export_btn.config(state="normal"))
        
        thread = threading.Thread(target=enrichment_thread, daemon=True)
        thread.start()
    
    def display_results(results):
        """Display enrichment results in the UI"""
        for ioc_type, ioc_results in results.items():
            if ioc_type not in enrichment_results:
                continue
            
            text_widget = enrichment_results[ioc_type]['text_widget']
            enrichment_results[ioc_type]['data'] = ioc_results
            
            text_widget.delete("1.0", "end")
            
            for result in ioc_results:
                ioc = result.get('ioc', 'Unknown')
                text_widget.insert("end", f"{'='*80}\n", "header")
                text_widget.insert("end", f"IOC: {ioc}\n", "ioc")
                text_widget.insert("end", f"Type: {result.get('type', 'unknown').upper()}\n")
                text_widget.insert("end", f"Enriched: {result.get('enriched_at', 'N/A')}\n")
                text_widget.insert("end", f"{'-'*80}\n")
                
                if 'geolocation' in result:
                    geo = result['geolocation']
                    if 'error' not in geo:
                        text_widget.insert("end", "\n[GEOLOCATION]\n", "section")
                        text_widget.insert("end", f"  Country: {geo.get('country', 'N/A')} ({geo.get('country_code', 'N/A')})\n")
                        text_widget.insert("end", f"  Region: {geo.get('region', 'N/A')}\n")
                        text_widget.insert("end", f"  City: {geo.get('city', 'N/A')}\n")
                        text_widget.insert("end", f"  ISP: {geo.get('isp', 'N/A')}\n")
                        text_widget.insert("end", f"  Org: {geo.get('org', 'N/A')}\n")
                        text_widget.insert("end", f"  AS: {geo.get('as', 'N/A')}\n")
                        text_widget.insert("end", f"  Coordinates: {geo.get('latitude', 'N/A')}, {geo.get('longitude', 'N/A')}\n")
                        hosting = "Yes" if geo.get('is_hosting') else "No"
                        proxy = "Yes" if geo.get('is_proxy') else "No"
                        mobile = "Yes" if geo.get('is_mobile') else "No"
                        text_widget.insert("end", f"  Hosting/Datacenter: {hosting}\n")
                        text_widget.insert("end", f"  Proxy: {proxy}\n")
                        text_widget.insert("end", f"  Mobile: {mobile}\n")
                
                if 'vpn_detection' in result:
                    vpn = result['vpn_detection']
                    if 'error' not in vpn:
                        text_widget.insert("end", "\n[VPN/PROXY DETECTION]\n", "section")
                        is_vpn = "YES" if vpn.get('is_vpn') else "NO"
                        is_proxy = "YES" if vpn.get('is_proxy') else "NO"
                        is_tor = "YES" if vpn.get('is_tor') else "NO"
                        is_hosting = "YES" if vpn.get('is_hosting') else "NO"
                        text_widget.insert("end", f"  VPN: {is_vpn}\n", "warning" if vpn.get('is_vpn') else "")
                        text_widget.insert("end", f"  Proxy: {is_proxy}\n", "warning" if vpn.get('is_proxy') else "")
                        text_widget.insert("end", f"  Tor: {is_tor}\n", "warning" if vpn.get('is_tor') else "")
                        text_widget.insert("end", f"  Hosting: {is_hosting}\n")
                        if vpn.get('network'):
                            text_widget.insert("end", f"  Network: {vpn.get('network')}\n")
                
                if 'virustotal' in result:
                    vt = result['virustotal']
                    if 'error' not in vt:
                        text_widget.insert("end", "\n[VIRUSTOTAL]\n", "section")
                        malicious = vt.get('malicious', 0)
                        suspicious = vt.get('suspicious', 0)
                        harmless = vt.get('harmless', 0)
                        undetected = vt.get('undetected', 0)
                        total = malicious + suspicious + harmless + undetected
                        if total > 0:
                            text_widget.insert("end", f"  Detections: {malicious + suspicious}/{total}\n",
                                             "danger" if malicious > 0 else "")
                            text_widget.insert("end", f"    Malicious: {malicious}\n",
                                             "danger" if malicious > 0 else "")
                            text_widget.insert("end", f"    Suspicious: {suspicious}\n",
                                             "warning" if suspicious > 0 else "")
                            text_widget.insert("end", f"    Harmless: {harmless}\n")
                            text_widget.insert("end", f"    Undetected: {undetected}\n")
                        if vt.get('reputation') is not None:
                            text_widget.insert("end", f"  Reputation Score: {vt.get('reputation')}\n")
                        if vt.get('file_type'):
                            text_widget.insert("end", f"  File Type: {vt.get('file_type')}\n")
                        if vt.get('names'):
                            text_widget.insert("end", f"  Known Names: {', '.join(vt.get('names')[:3])}\n")
                    elif vt.get('error'):
                        text_widget.insert("end", f"\n[VIRUSTOTAL] {vt['error']}\n", "info")
                
                if 'reputation' in result and result['reputation']:
                    rep = result['reputation']
                    if 'error' not in rep:
                        text_widget.insert("end", "\n[ABUSEIPDB]\n", "section")
                        score = rep.get('abuse_confidence_score', 0)
                        text_widget.insert("end", f"  Abuse Confidence Score: {score}%\n",
                                         "danger" if score > 50 else "warning" if score > 20 else "")
                        text_widget.insert("end", f"  Total Reports: {rep.get('total_reports', 0)}\n")
                        text_widget.insert("end", f"  Distinct Reporters: {rep.get('num_distinct_users', 0)}\n")
                        if rep.get('is_whitelisted'):
                            text_widget.insert("end", "  Status: Whitelisted\n", "safe")
                        if rep.get('is_tor'):
                            text_widget.insert("end", "  Tor Exit Node: YES\n", "warning")
                
                text_widget.insert("end", "\n\n")
            
            text_widget.tag_config("header", font=("Courier", 10, "bold"))
            text_widget.tag_config("ioc", foreground="blue", font=("Courier", 11, "bold"))
            text_widget.tag_config("section", foreground="purple", font=("Courier", 10, "bold"))
            text_widget.tag_config("danger", foreground="red", font=("Courier", 10, "bold"))
            text_widget.tag_config("warning", foreground="orange", font=("Courier", 10, "bold"))
            text_widget.tag_config("safe", foreground="green")
            text_widget.tag_config("info", foreground="gray")
        
        progress_label.config(text="Enrichment complete!")
        self.update_status("IOC enrichment completed")
    
    def export_results():
        """Export enrichment results to JSON"""
        if not any(enrichment_results[k]['data'] for k in enrichment_results):
            messagebox.showinfo("No Data", "No enrichment data to export. Run enrichment first.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt")]
        )
        
        if not filepath:
            return
        
        try:
            export_data = {k: v['data'] for k, v in enrichment_results.items() if v['data']}
            if filepath.endswith('.json'):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    for ioc_type, results in export_data.items():
                        f.write(f"\n{'='*80}\n")
                        f.write(f"{ioc_type.upper()}\n")
                        f.write(f"{'='*80}\n\n")
                        for result in results:
                            f.write(f"IOC: {result.get('ioc')}\n")
                            f.write(json.dumps(result, indent=2))
                            f.write("\n\n")
            messagebox.showinfo("Success", f"Enrichment data exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export data: {e}")
    
    enrich_btn = tk.Button(button_frame, text="Start Enrichment", command=start_enrichment,
                          bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=15)
    enrich_btn.pack(side="left", padx=5)
    
    export_btn = tk.Button(button_frame, text="Export Results", command=export_results, width=15)
    export_btn.pack(side="left", padx=5)
    
    tk.Button(button_frame, text="Close", command=window.destroy, width=10).pack(side="right", padx=5)

def clear_text(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text_widget.delete("1.0", "end")
    self.update_status("Cleared text")

def safe_copy_text(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text = text_widget.get("1.0", "end-1c")

    unsafe_patterns = [
        r'https?://',
        r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b'
    ]
    
    is_unsafe = any(re.search(pattern, text, re.IGNORECASE) for pattern in unsafe_patterns)
    
    if is_unsafe:
        dialog = tk.Toplevel(self.root)
        dialog.title("Unsafe Content Detected")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text="Warning: Undefanged IOCs detected!", 
                font=('Arial', 12, 'bold'), fg='red').pack(pady=10)
        tk.Label(dialog, text="The text contains potentially unsafe content\nthat hasn't been defanged.", 
                justify=tk.CENTER).pack(pady=5)
        tk.Label(dialog, text="Are you sure you want to copy this text?", 
                justify=tk.CENTER).pack(pady=5)
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def copy_anyway():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.validation_label.config(text="Copied (Unsafe)", fg="orange")
            self.update_status("Text copied (contained unsafe content)")
            dialog.destroy()
        
        def cancel_copy():
            self.validation_label.config(text="Copy Cancelled", fg="red")
            dialog.destroy()
        
        tk.Button(button_frame, text="Copy Anyway", command=copy_anyway, bg="#ff6b6b", fg="white", activebackground="#ff4c4c", activeforeground="white", width=12).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel_copy, bg="#666666", fg="white", activebackground="#888888", activeforeground="white", width=12).pack(side="left", padx=5)
        return

    self.root.clipboard_clear()
    self.root.clipboard_append(text)
    self.validation_label.config(text="Copied Safely", fg="green")
    self.update_status("Text copied safely")

# --------------------- Syntax Highlighting ---------------------
def on_text_change_event(self, event=None):
    """Handle text change events - syntax highlighting and status update"""
    if event and event.widget:
        text_widget = event.widget
        if self.config.SYNTAX_HIGHLIGHTING:
            self.root.after_idle(lambda: self.apply_syntax_highlighting(text_widget))
        self.root.after_idle(lambda: self.update_status("Ready"))

def on_text_focus(self, event=None):
    """Handle text widget focus events"""
    self.update_status("Ready")
    # Reapply button colours — tkinter can reset them when focus shifts
    self.update_button_colors()

def on_cursor_move(self, event=None):
    """Handle cursor movement"""
    self.root.after_idle(lambda: self.update_status("Ready"))

def apply_syntax_highlighting(self, text_widget):
    if not self.config.SYNTAX_HIGHLIGHTING:
        return
    
    for tag in ['url', 'ip', 'email', 'hash', 'defanged']:
        text_widget.tag_delete(tag)
    
    text = text_widget.get("1.0", "end-1c")
    
    if self.config.DARK_MODE:
        colors = {
            'url': '#66B2FF',
            'ip': '#FFB366',
            'email': '#66FF66',
            'hash': '#FF66FF',
            'defanged': '#FFFF66'
        }
    else:
        colors = {
            'url': '#0066CC',
            'ip': '#CC6600',
            'email': '#009900',
            'hash': '#CC00CC',
            'defanged': '#CC9900'
        }
    
    patterns = {
        'url': [self.ioc_patterns['url'], r'hxxps?\[\:\/\/\][^\s<>"]{2,}'],
        'ip': [self.ioc_patterns['ipv4'], self.ioc_patterns['ipv6']],
        'email': [self.ioc_patterns['email']],
        'hash': [self.ioc_patterns['hash_md5'], self.ioc_patterns['hash_sha1'], self.ioc_patterns['hash_sha256']],
        'defanged': [re.compile(r'\[[.:\@\/\#]+\]')]
    }
    
    for tag, pattern_list in patterns.items():
        for pattern in pattern_list:
            start_pos = "1.0"
            while True:
                try:
                    match = pattern.search(text, text_widget.count("1.0", start_pos, "chars")[0] if start_pos != "1.0" else 0)
                    if not match:
                        break
                    start_idx = f"1.0+{match.start()}c"
                    end_idx = f"1.0+{match.end()}c"
                    text_widget.tag_add(tag, start_idx, end_idx)
                    text_widget.tag_config(tag, foreground=colors[tag])
                    start_pos = end_idx
                except:
                    break

# --------------------- Templates ---------------------
def load_templates_data(self):
    """Load templates from JSON file"""
    try:
        if os.path.exists(self.config.TEMPLATES_FILE):
            with open(self.config.TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        else:
            self.templates = {
                "Phishing Investigation": "=== PHISHING INVESTIGATION ===\nDate: {date}\nAnalyst: {analyst}\n\nSubject Line:\nSender:\nRecipients:\n\n--- ANALYSIS ---\n\n--- VERDICT ---\nPhishing: [YES/NO]\nAction Taken:\n\n",
                "Malware Analysis": "=== MALWARE ANALYSIS ===\nDate: {date}\nAnalyst: {analyst}\n\nSample Hash:\nFile Name:\nFile Type:\n\n--- BEHAVIORAL ANALYSIS ---\n\n--- NETWORK INDICATORS ---\n\n--- CONCLUSION ---\n\n",
                "Security Incident Report": "=== SECURITY INCIDENT REPORT ===\nIncident ID: \nDate/Time: {datetime}\nSeverity: [LOW/MEDIUM/HIGH/CRITICAL]\nStatus: [OPEN/INVESTIGATING/RESOLVED]\n\n--- INCIDENT SUMMARY ---\n\n--- AFFECTED SYSTEMS ---\n\n--- INDICATORS OF COMPROMISE ---\n\n--- ACTIONS TAKEN ---\n\n--- RECOMMENDATIONS ---\n\n"
            }
            self.save_templates_data()
    except Exception as e:
        print(f"Error loading templates: {e}")
        self.templates = {}

def save_templates_data(self):
    """Save templates to JSON file"""
    try:
        with open(self.config.TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving templates: {e}")

def update_templates_menu(self):
    """Update the Templates menu with current templates"""
    self.template_menu.delete(0, "end")
    
    if hasattr(self, 'templates') and self.templates:
        for template_name in sorted(self.templates.keys()):
            self.template_menu.add_command(
                label=template_name,
                command=lambda name=template_name: self.insert_template(name)
            )
    else:
        self.template_menu.add_command(label="No templates available", state="disabled")
        
    self.template_menu.add_separator()
    self.template_menu.add_command(label="Manage Templates...", command=self.show_settings_window)

def insert_template(self, template_name):
    """Insert template at cursor position"""
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    
    if template_name in self.templates:
        content = self.templates[template_name]
        content = content.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
        content = content.replace('{time}', datetime.now().strftime('%H:%M:%S'))
        content = content.replace('{datetime}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        text_widget.insert('insert', content)
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)
        self.update_status(f"Inserted template: {template_name}")

# --------------------- Find/Replace ---------------------
def show_find_dialog(self):
    if self.find_dialog and self.find_dialog.winfo_exists():
        self.find_dialog.focus()
        return
    
    self.find_dialog = tk.Toplevel(self.root)
    self.find_dialog.title("Find")
    self.find_dialog.geometry("350x120")
    self.find_dialog.transient(self.root)
    
    tk.Label(self.find_dialog, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    self.find_entry = tk.Entry(self.find_dialog, width=30)
    self.find_entry.grid(row=0, column=1, padx=5, pady=5)
    self.find_entry.focus()
    
    button_frame = tk.Frame(self.find_dialog)
    button_frame.grid(row=1, column=0, columnspan=2, pady=10)
    
    tk.Button(button_frame, text="Find Next", command=self.find_next).pack(side="left", padx=5)
    tk.Button(button_frame, text="Find All", command=self.find_all).pack(side="left", padx=5)
    tk.Button(button_frame, text="Clear", command=self.clear_find).pack(side="left", padx=5)
    
    self.find_entry.bind('<Return>', lambda e: self.find_next())

def show_replace_dialog(self):
    if self.find_dialog and self.find_dialog.winfo_exists():
        self.find_dialog.destroy()
    
    self.find_dialog = tk.Toplevel(self.root)
    self.find_dialog.title("Find and Replace")
    self.find_dialog.geometry("350x180")
    self.find_dialog.transient(self.root)
    
    tk.Label(self.find_dialog, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    self.find_entry = tk.Entry(self.find_dialog, width=30)
    self.find_entry.grid(row=0, column=1, padx=5, pady=5)
    
    tk.Label(self.find_dialog, text="Replace:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    self.replace_entry = tk.Entry(self.find_dialog, width=30)
    self.replace_entry.grid(row=1, column=1, padx=5, pady=5)
    
    self.find_entry.focus()
    
    button_frame = tk.Frame(self.find_dialog)
    button_frame.grid(row=2, column=0, columnspan=2, pady=10)
    
    tk.Button(button_frame, text="Find Next", command=self.find_next).pack(side="left", padx=2)
    tk.Button(button_frame, text="Replace", command=self.replace_current).pack(side="left", padx=2)
    tk.Button(button_frame, text="Replace All", command=self.replace_all).pack(side="left", padx=2)
    tk.Button(button_frame, text="Clear", command=self.clear_find).pack(side="left", padx=2)
    
    self.find_entry.bind('<Return>', lambda e: self.find_next())

def find_next(self):
    if not hasattr(self, 'find_entry'):
        return
    
    term = self.find_entry.get()
    current = self.notebook.select()
    if not current or not term:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    
    start_pos = text_widget.index(tk.INSERT)
    pos = text_widget.search(term, start_pos, stopindex="end", nocase=True)
    
    if not pos:
        pos = text_widget.search(term, "1.0", stopindex=start_pos, nocase=True)
    
    if pos:
        end_pos = f"{pos}+{len(term)}c"
        text_widget.tag_remove("sel", "1.0", "end")
        text_widget.tag_add("sel", pos, end_pos)
        text_widget.mark_set(tk.INSERT, end_pos)
        text_widget.see(pos)

def find_all(self):
    if not hasattr(self, 'find_entry'):
        return
    
    term = self.find_entry.get()
    current = self.notebook.select()
    if not current or not term:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    
    text_widget.tag_remove("found", "1.0", "end")
    if term:
        idx = "1.0"
        count = 0
        while True:
            idx = text_widget.search(term, idx, nocase=True, stopindex="end")
            if not idx:
                break
            lastidx = f"{idx}+{len(term)}c"
            text_widget.tag_add("found", idx, lastidx)
            idx = lastidx
            count += 1
        text_widget.tag_config("found", background="yellow")
        self.update_status(f"Found {count} occurrences")

def replace_current(self):
    if not hasattr(self, 'find_entry') or not hasattr(self, 'replace_entry'):
        return
    
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    
    try:
        if text_widget.tag_ranges("sel"):
            text_widget.delete("sel.first", "sel.last")
            text_widget.insert("insert", self.replace_entry.get())
            if self.config.SYNTAX_HIGHLIGHTING:
                self.apply_syntax_highlighting(text_widget)
    except tk.TclError:
        pass

def replace_all(self):
    if not hasattr(self, 'find_entry') or not hasattr(self, 'replace_entry'):
        return
    
    find_term = self.find_entry.get()
    replace_term = self.replace_entry.get()
    current = self.notebook.select()
    
    if not current or not find_term:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    
    text = text_widget.get("1.0", "end-1c")
    count = text.count(find_term)
    
    if count > 0:
        new_text = text.replace(find_term, replace_term)
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", new_text)
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)
        self.update_status(f"Replaced {count} occurrences")

def clear_find(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    text_widget.tag_remove("found", "1.0", "end")
    text_widget.tag_remove("sel", "1.0", "end")

# --------------------- Edit Functions ---------------------
def undo(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    
    try:
        text_widget.edit_undo()
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)
    except tk.TclError:
        pass

def redo(self):
    current = self.notebook.select()
    if not current:
        return
    
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    
    try:
        text_widget.edit_redo()
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)
    except tk.TclError:
        pass

# --------------------- Font Controls ---------------------
def increase_font_size(self):
    self.config.FONT_SIZE = min(self.config.FONT_SIZE + 1, 24)
    self.update_all_fonts()
    self.save_settings()

def decrease_font_size(self):
    self.config.FONT_SIZE = max(self.config.FONT_SIZE - 1, 8)
    self.update_all_fonts()
    self.save_settings()

def update_all_fonts(self):
    new_font = (self.config.FONT_FAMILY, self.config.FONT_SIZE)
    for frame in self.tabs:
        text_container = self.tabs[frame]
        if hasattr(text_container, 'text'):
            text_container.text.config(font=new_font)
            if hasattr(text_container, 'line_numbers'):
                text_container.line_numbers.config(font=new_font)

# --------------------- View Controls ---------------------
def toggle_line_numbers(self):
    self.config.LINE_NUMBERS = not self.config.LINE_NUMBERS
    for frame in self.tabs:
        text_container = self.tabs[frame]
        if hasattr(text_container, 'toggle_line_numbers'):
            text_container.toggle_line_numbers()
    self.save_settings()
    self.update_status(f"Line numbers {'enabled' if self.config.LINE_NUMBERS else 'disabled'}")

def toggle_word_wrap(self):
    self.config.WORD_WRAP = not self.config.WORD_WRAP
    wrap_mode = "word" if self.config.WORD_WRAP else "none"
    for frame in self.tabs:
        text_container = self.tabs[frame]
        text_widget = text_container.text if hasattr(text_container, 'text') else text_container
        text_widget.config(wrap=wrap_mode)
    self.save_settings()
    self.update_status(f"Word wrap {'enabled' if self.config.WORD_WRAP else 'disabled'}")

def toggle_syntax_highlighting(self):
    self.config.SYNTAX_HIGHLIGHTING = not self.config.SYNTAX_HIGHLIGHTING
    if self.config.SYNTAX_HIGHLIGHTING:
        for frame in self.tabs:
            text_container = self.tabs[frame]
            text_widget = text_container.text if hasattr(text_container, 'text') else text_container
            self.apply_syntax_highlighting(text_widget)
            text_widget.bind('<KeyRelease>', self.on_text_change_event)
            text_widget.bind('<ButtonRelease>', self.on_text_change_event)
    else:
        for frame in self.tabs:
            text_container = self.tabs[frame]
            text_widget = text_container.text if hasattr(text_container, 'text') else text_container
            for tag in ['url', 'ip', 'email', 'hash', 'defanged']:
                text_widget.tag_delete(tag)
            text_widget.unbind('<KeyRelease>')
            text_widget.unbind('<ButtonRelease>')
    self.save_settings()
    self.update_status(f"Syntax highlighting {'enabled' if self.config.SYNTAX_HIGHLIGHTING else 'disabled'}")

# --------------------- Dictionary ---------------------
def load_custom_dictionary(self):
    if SPELL_CHECK_AVAILABLE and self.spell and os.path.exists(self.config.CUSTOM_DICT_FILE):
        try:
            with open(self.config.CUSTOM_DICT_FILE, "r", encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and hasattr(self.spell, 'word_frequency'):
                        self.spell.word_frequency.add(word)
        except Exception as e:
            print(f"Error loading custom dictionary: {e}")

# --------------------- Utilities ---------------------
def toggle_dark_mode(self):
    self.config.DARK_MODE = not self.config.DARK_MODE
    if self.config.DARK_MODE:
        self.apply_dark_mode()
    else:
        self.remove_dark_mode()
    self.update_button_colors()
    self.save_settings()
    if self.config.SYNTAX_HIGHLIGHTING:
        for frame in self.tabs:
            text_container = self.tabs[frame]
            text_widget = text_container.text if hasattr(text_container, 'text') else text_container
            self.apply_syntax_highlighting(text_widget)

def apply_dark_mode(self):
    dark_bg = "#2b2b2b"
    dark_fg = "#ffffff"
    button_bg = "#404040"
    button_fg = "#ffffff"
    entry_bg = "#3d3d3d"
    select_bg = "#505050"
    
    self.root.configure(bg=dark_bg)
    
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", background=dark_bg, foreground=dark_fg)
    style.configure("TNotebook.Tab", background="#404040", foreground=dark_fg,
                   padding=[8, 4], focuscolor="none")
    style.map("TNotebook.Tab",
             background=[("selected", "#505050"), ("active", "#454545")],
             foreground=[("selected", "#ffffff"), ("active", "#ffffff")])
    style.configure("TFrame", background=dark_bg)
    style.configure("TButton", background=button_bg, foreground=button_fg,
                   fieldbackground=button_bg, borderwidth=1)
    style.map("TButton",
             background=[("active", "#555555"), ("pressed", "#666666")],
             foreground=[("active", "#ffffff"), ("pressed", "#ffffff")])
    style.configure("TEntry", fieldbackground=entry_bg, foreground=dark_fg,
                   bordercolor="#555555", insertcolor=dark_fg)
    style.map("TEntry",
             focuscolor=[("focus", "#0078D4")],
             fieldbackground=[("focus", entry_bg)])
    style.configure("TLabel", background=dark_bg, foreground=dark_fg)
    
    for frame in self.tabs:
        text_container = self.tabs[frame]
        text_widget = text_container.text if hasattr(text_container, 'text') else text_container
        text_widget.config(
            bg=dark_bg, fg=dark_fg, insertbackground=dark_fg,
            selectbackground=select_bg, selectforeground=dark_fg,
            highlightbackground=dark_bg, highlightcolor="#0078D4"
        )
        if hasattr(text_container, 'line_numbers'):
            text_container.line_numbers.config(
                bg="#404040", fg="#888888",
                selectbackground="#505050", selectforeground="#ffffff"
            )
    
    self.frame_buttons.config(bg=dark_bg)
    self.status_bar.config(bg=dark_bg)
    self.status_left.config(bg=dark_bg, fg=dark_fg)
    self.status_right.config(bg=dark_bg, fg=dark_fg)
    self.apply_dark_theme_to_widgets(self.root)
    # Ensure bottom-bar buttons are correctly coloured after recursive walk
    self.update_button_colors()

def apply_dark_theme_to_widgets(self, parent):
    """Recursively apply dark theme to all tkinter widgets"""
    dark_bg = "#2b2b2b"
    dark_fg = "#ffffff"
    button_bg = "#404040"
    
    try:
        for child in parent.winfo_children():
            widget_class = child.winfo_class()
            if widget_class == 'Button':
                # Skip Safe Copy — it keeps its own green colour
                if child is self.copy_button:
                    pass
                else:
                    child.config(
                        bg=button_bg, fg=dark_fg,
                        activebackground="#555555", activeforeground=dark_fg,
                        highlightbackground=dark_bg, highlightcolor="#0078D4"
                    )
            elif widget_class == 'Label':
                child.config(bg=dark_bg, fg=dark_fg)
            elif widget_class == 'Entry':
                child.config(
                    bg="#3d3d3d", fg=dark_fg, insertbackground=dark_fg,
                    selectbackground="#505050", selectforeground=dark_fg
                )
            elif widget_class in ['Frame', 'Toplevel']:
                child.config(bg=dark_bg)
            elif widget_class == 'Listbox':
                child.config(
                    bg="#3d3d3d", fg=dark_fg,
                    selectbackground="#505050", selectforeground=dark_fg
                )
            elif widget_class == 'Text':
                child.config(
                    bg=dark_bg, fg=dark_fg, insertbackground=dark_fg,
                    selectbackground="#505050", selectforeground=dark_fg
                )
            self.apply_dark_theme_to_widgets(child)
    except tk.TclError:
        pass

def remove_dark_mode(self):
    light_bg = "white"
    light_fg = "black"
    button_bg = "SystemButtonFace"
    select_bg = "#0078D4"
    
    self.root.configure(bg=button_bg)
    
    style = ttk.Style()
    style.theme_use("default")
    style.configure("TNotebook", background=button_bg, foreground=light_fg)
    style.configure("TNotebook.Tab", background=button_bg, foreground=light_fg)
    style.configure("TFrame", background=button_bg)
    style.configure("TButton")
    style.configure("TEntry")
    style.configure("TLabel", background=button_bg, foreground=light_fg)
    
    for frame in self.tabs:
        text_container = self.tabs[frame]
        text_widget = text_container.text if hasattr(text_container, 'text') else text_container
        text_widget.config(
            bg=light_bg, fg=light_fg, insertbackground=light_fg,
            selectbackground=select_bg, selectforeground=light_bg,
            highlightbackground=button_bg, highlightcolor="#0078D4"
        )
        if hasattr(text_container, 'line_numbers'):
            text_container.line_numbers.config(
                bg="#f0f0f0", fg="#666666",
                selectbackground=select_bg, selectforeground=light_bg
            )
    
    self.frame_buttons.config(bg=button_bg)
    self.status_bar.config(bg=button_bg)
    self.status_left.config(bg=button_bg, fg=light_fg)
    self.status_right.config(bg=button_bg, fg=light_fg)
    self.apply_light_theme_to_widgets(self.root)
    # Ensure bottom-bar buttons are correctly coloured after recursive walk
    self.update_button_colors()

def apply_light_theme_to_widgets(self, parent):
    """Recursively apply light theme to all tkinter widgets"""
    light_fg = "black"
    button_bg = "SystemButtonFace"
    light_bg = "white"
    
    try:
        for child in parent.winfo_children():
            widget_class = child.winfo_class()
            if widget_class == 'Button':
                # Skip Safe Copy — it keeps its own green colour
                if child is self.copy_button:
                    pass
                else:
                    child.config(
                        bg=button_bg, fg=light_fg,
                        activebackground="#e1e1e1", activeforeground=light_fg,
                        highlightbackground=button_bg
                    )
            elif widget_class == 'Label':
                child.config(bg=button_bg, fg=light_fg)
            elif widget_class == 'Entry':
                child.config(
                    bg=light_bg, fg=light_fg, insertbackground=light_fg,
                    selectbackground="#0078D4", selectforeground=light_bg
                )
            elif widget_class in ['Frame', 'Toplevel']:
                child.config(bg=button_bg)
            elif widget_class == 'Listbox':
                child.config(
                    bg=light_bg, fg=light_fg,
                    selectbackground="#0078D4", selectforeground=light_bg
                )
            elif widget_class == 'Text':
                child.config(
                    bg=light_bg, fg=light_fg, insertbackground=light_fg,
                    selectbackground="#0078D4", selectforeground=light_bg
                )
            self.apply_light_theme_to_widgets(child)
    except tk.TclError:
        pass

# --------------------- Settings Window ---------------------
def show_settings_window(self):
    """Show the settings configuration window"""
    settings_window = tk.Toplevel(self.root)
    settings_window.title("ThreatPad Settings")
    settings_window.geometry("600x500")
    settings_window.transient(self.root)
    settings_window.grab_set()
    
    settings_window.update_idletasks()
    x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
    y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
    settings_window.geometry(f"+{x}+{y}")
    
    notebook = ttk.Notebook(settings_window)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    appearance_frame = ttk.Frame(notebook)
    notebook.add(appearance_frame, text="Appearance")
    self.create_appearance_tab(appearance_frame)
    
    copypasta_frame = ttk.Frame(notebook)
    notebook.add(copypasta_frame, text="Copy Pasta")
    self.create_copypasta_tab(copypasta_frame)
    
    templates_frame = ttk.Frame(notebook)
    notebook.add(templates_frame, text="Templates")
    self.create_templates_tab(templates_frame)
    
    general_frame = ttk.Frame(notebook)
    notebook.add(general_frame, text="General")
    self.create_general_tab(general_frame)
    
    if IOC_ENRICHMENT_AVAILABLE:
        apikeys_frame = ttk.Frame(notebook)
        notebook.add(apikeys_frame, text="API Keys")
        self.create_apikeys_tab(apikeys_frame)
    
    button_frame = ttk.Frame(settings_window)
    button_frame.pack(fill="x", padx=10, pady=10)
    
    ttk.Button(button_frame, text="OK", command=lambda: self.save_and_close_settings(settings_window)).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side="right", padx=5)
    ttk.Button(button_frame, text="Apply", command=self.apply_settings_changes).pack(side="right", padx=5)

def create_appearance_tab(self, parent):
    theme_frame = ttk.LabelFrame(parent, text="Theme")
    theme_frame.pack(fill="x", padx=10, pady=5)
    
    self.follow_system_var = tk.BooleanVar(value=self.config.FOLLOW_SYSTEM_THEME)
    self.dark_mode_var = tk.BooleanVar(value=self.config.DARK_MODE)
    
    ttk.Checkbutton(theme_frame, text="Follow system theme",
                   variable=self.follow_system_var,
                   command=self.toggle_manual_theme).pack(anchor="w", padx=5, pady=2)
    
    self.manual_theme_frame = ttk.Frame(theme_frame)
    self.manual_theme_frame.pack(fill="x", padx=5, pady=2)
    
    ttk.Checkbutton(self.manual_theme_frame, text="Dark mode",
                   variable=self.dark_mode_var).pack(anchor="w")
    
    font_frame = ttk.LabelFrame(parent, text="Font")
    font_frame.pack(fill="x", padx=10, pady=5)
    
    ttk.Label(font_frame, text="Font Family:").pack(anchor="w", padx=5, pady=2)
    self.font_family_var = tk.StringVar(value=self.config.FONT_FAMILY)
    font_combo = ttk.Combobox(font_frame, textvariable=self.font_family_var,
                             values=["Consolas", "Courier New", "Monaco", "Source Code Pro", "Ubuntu Mono"])
    font_combo.pack(fill="x", padx=5, pady=2)
    
    ttk.Label(font_frame, text="Font Size:").pack(anchor="w", padx=5, pady=2)
    self.font_size_var = tk.IntVar(value=self.config.FONT_SIZE)
    font_size_frame = ttk.Frame(font_frame)
    font_size_frame.pack(fill="x", padx=5, pady=2)
    ttk.Scale(font_size_frame, from_=8, to=24, variable=self.font_size_var,
             orient="horizontal").pack(side="left", fill="x", expand=True)
    ttk.Label(font_size_frame, textvariable=self.font_size_var, width=3).pack(side="right")
    
    display_frame = ttk.LabelFrame(parent, text="Display")
    display_frame.pack(fill="x", padx=10, pady=5)
    
    self.line_numbers_var = tk.BooleanVar(value=self.config.LINE_NUMBERS)
    self.word_wrap_var = tk.BooleanVar(value=self.config.WORD_WRAP)
    self.syntax_highlight_var = tk.BooleanVar(value=self.config.SYNTAX_HIGHLIGHTING)
    
    ttk.Checkbutton(display_frame, text="Show line numbers",
                   variable=self.line_numbers_var).pack(anchor="w", padx=5, pady=2)
    ttk.Checkbutton(display_frame, text="Word wrap",
                   variable=self.word_wrap_var).pack(anchor="w", padx=5, pady=2)
    ttk.Checkbutton(display_frame, text="Syntax highlighting",
                   variable=self.syntax_highlight_var).pack(anchor="w", padx=5, pady=2)
    
    self.toggle_manual_theme()

def toggle_manual_theme(self):
    if self.follow_system_var.get():
        for child in self.manual_theme_frame.winfo_children():
            child.configure(state="disabled")
    else:
        for child in self.manual_theme_frame.winfo_children():
            child.configure(state="normal")

def create_copypasta_tab(self, parent):
    self.load_snippets()
    ttk.Label(parent, text="Configure text snippets for quick insertion:").pack(anchor="w", padx=10, pady=5)
    
    list_frame = ttk.Frame(parent)
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    left_frame = ttk.Frame(list_frame)
    left_frame.pack(side="left", fill="both", expand=True)
    ttk.Label(left_frame, text="Snippets:").pack(anchor="w")
    self.snippets_listbox = tk.Listbox(left_frame)
    self.snippets_listbox.pack(fill="both", expand=True)
    self.snippets_listbox.bind('<<ListboxSelect>>', self.on_snippet_select)
    for name in self.snippets.keys():
        self.snippets_listbox.insert(tk.END, name)
    
    right_frame = ttk.Frame(list_frame)
    right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
    ttk.Label(right_frame, text="Snippet Name:").pack(anchor="w")
    self.snippet_name_var = tk.StringVar()
    ttk.Entry(right_frame, textvariable=self.snippet_name_var).pack(fill="x")
    ttk.Label(right_frame, text="Snippet Content:").pack(anchor="w", pady=(10, 0))
    self.snippet_text = tk.Text(right_frame, height=8)
    self.snippet_text.pack(fill="both", expand=True)
    
    button_frame = ttk.Frame(right_frame)
    button_frame.pack(fill="x", pady=5)
    ttk.Button(button_frame, text="Add", command=self.add_snippet).pack(side="left", padx=2)
    ttk.Button(button_frame, text="Update", command=self.update_snippet).pack(side="left", padx=2)
    ttk.Button(button_frame, text="Delete", command=self.delete_snippet).pack(side="left", padx=2)

def create_general_tab(self, parent):
    autosave_frame = ttk.LabelFrame(parent, text="Auto-save")
    autosave_frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(autosave_frame, text="Auto-save interval (minutes):").pack(anchor="w", padx=5, pady=2)
    self.autosave_interval_var = tk.IntVar(value=self.config.AUTO_SAVE_INTERVAL // 60000)
    interval_frame = ttk.Frame(autosave_frame)
    interval_frame.pack(fill="x", padx=5, pady=2)
    ttk.Scale(interval_frame, from_=1, to=10, variable=self.autosave_interval_var,
             orient="horizontal").pack(side="left", fill="x", expand=True)
    ttk.Label(interval_frame, textvariable=self.autosave_interval_var, width=3).pack(side="right")
    
    recent_frame = ttk.LabelFrame(parent, text="Recent Files")
    recent_frame.pack(fill="x", padx=10, pady=5)
    ttk.Label(recent_frame, text="Maximum recent files:").pack(anchor="w", padx=5, pady=2)
    self.max_recent_var = tk.IntVar(value=self.config.MAX_RECENT)
    recent_scale_frame = ttk.Frame(recent_frame)
    recent_scale_frame.pack(fill="x", padx=5, pady=2)
    ttk.Scale(recent_scale_frame, from_=5, to=20, variable=self.max_recent_var,
             orient="horizontal").pack(side="left", fill="x", expand=True)
    ttk.Label(recent_scale_frame, textvariable=self.max_recent_var, width=3).pack(side="right")

def create_apikeys_tab(self, parent):
    info_frame = ttk.Frame(parent)
    info_frame.pack(fill="x", padx=10, pady=10)
    ttk.Label(info_frame, text="Configure API keys for IOC enrichment:",
             font=("Arial", 10, "bold")).pack(anchor="w")
    ttk.Label(info_frame, text="API keys are stored locally and used for threat intelligence lookups.",
             font=("Arial", 9)).pack(anchor="w", pady=(5, 0))
    
    vt_frame = ttk.LabelFrame(parent, text="VirusTotal")
    vt_frame.pack(fill="x", padx=10, pady=10)
    ttk.Label(vt_frame, text="API Key:").pack(anchor="w", padx=5, pady=(5, 0))
    self.vt_api_key_var = tk.StringVar(value=self.config.API_KEYS.get('virustotal', ''))
    vt_entry = ttk.Entry(vt_frame, textvariable=self.vt_api_key_var, width=50, show="*")
    vt_entry.pack(fill="x", padx=5, pady=5)
    ttk.Label(vt_frame, text="Get a free API key at: https://www.virustotal.com/gui/my-apikey",
             foreground="blue", cursor="hand2").pack(anchor="w", padx=5, pady=(0, 5))
    
    def show_vt_key():
        if vt_entry.cget('show') == '*':
            vt_entry.config(show='')
            vt_show_btn.config(text="Hide")
        else:
            vt_entry.config(show='*')
            vt_show_btn.config(text="Show")
    vt_show_btn = ttk.Button(vt_frame, text="Show", command=show_vt_key, width=10)
    vt_show_btn.pack(anchor="w", padx=5, pady=(0, 10))
    
    abuse_frame = ttk.LabelFrame(parent, text="AbuseIPDB")
    abuse_frame.pack(fill="x", padx=10, pady=10)
    ttk.Label(abuse_frame, text="API Key:").pack(anchor="w", padx=5, pady=(5, 0))
    self.abuse_api_key_var = tk.StringVar(value=self.config.API_KEYS.get('abuseipdb', ''))
    abuse_entry = ttk.Entry(abuse_frame, textvariable=self.abuse_api_key_var, width=50, show="*")
    abuse_entry.pack(fill="x", padx=5, pady=5)
    ttk.Label(abuse_frame, text="Get a free API key at: https://www.abuseipdb.com/api",
             foreground="blue", cursor="hand2").pack(anchor="w", padx=5, pady=(0, 5))
    
    def show_abuse_key():
        if abuse_entry.cget('show') == '*':
            abuse_entry.config(show='')
            abuse_show_btn.config(text="Hide")
        else:
            abuse_entry.config(show='*')
            abuse_show_btn.config(text="Show")
    abuse_show_btn = ttk.Button(abuse_frame, text="Show", command=show_abuse_key, width=10)
    abuse_show_btn.pack(anchor="w", padx=5, pady=(0, 10))
    
    note_text = ("Note: Free API services used:\n"
                 "- IP Geolocation: ip-api.com (no key required, 45 requests/minute)\n"
                 "- VPN Detection: vpnapi.io (no key required, 1000 requests/day)\n"
                 "- VirusTotal: Requires free API key (4 requests/minute)\n"
                 "- AbuseIPDB: Optional, requires free API key (1000 requests/day)")
    ttk.Label(parent, text=note_text, font=("Arial", 9),
             foreground="gray", justify="left").pack(anchor="w", padx=10, pady=10)

def apply_settings_changes(self):
    self.config.FOLLOW_SYSTEM_THEME = self.follow_system_var.get()
    if not self.config.FOLLOW_SYSTEM_THEME:
        self.config.DARK_MODE = self.dark_mode_var.get()
    else:
        self.config.DARK_MODE = get_system_theme()
    
    self.config.FONT_FAMILY = self.font_family_var.get()
    self.config.FONT_SIZE = self.font_size_var.get()
    self.config.LINE_NUMBERS = self.line_numbers_var.get()
    self.config.WORD_WRAP = self.word_wrap_var.get()
    self.config.SYNTAX_HIGHLIGHTING = self.syntax_highlight_var.get()
    self.config.AUTO_SAVE_INTERVAL = self.autosave_interval_var.get() * 60000
    self.config.MAX_RECENT = self.max_recent_var.get()
    
    if hasattr(self, 'vt_api_key_var'):
        self.config.API_KEYS['virustotal'] = self.vt_api_key_var.get().strip()
    if hasattr(self, 'abuse_api_key_var'):
        self.config.API_KEYS['abuseipdb'] = self.abuse_api_key_var.get().strip()
    
    if IOC_ENRICHMENT_AVAILABLE:
        self.enrichment_engine = IOCEnrichment(api_keys=self.config.API_KEYS)
    
    if self.config.DARK_MODE:
        self.apply_dark_mode()
    else:
        self.remove_dark_mode()
    
    self.update_all_fonts()
    self.save_settings()
    self.save_snippets()
    self.save_templates_data()
    self.update_copypasta_menu()
    self.update_templates_menu()
    self.update_status("Settings applied")

def save_and_close_settings(self, window):
    self.apply_settings_changes()
    window.destroy()

# --------------------- Snippet Management ---------------------
def load_snippets(self):
    try:
        if os.path.exists(self.config.SNIPPETS_FILE):
            with open(self.config.SNIPPETS_FILE, 'r', encoding='utf-8') as f:
                self.snippets = json.load(f)
        else:
            self.snippets = {
                "Incident Header": "=== INCIDENT ANALYSIS ===\nDate: {date}\nAnalyst: {analyst}\nSeverity: [LOW/MEDIUM/HIGH/CRITICAL]\n\n",
                "IOC Section": "\n--- INDICATORS OF COMPROMISE (IOCs) ---\nIPs:\n- \n\nDomains:\n- \n\nHashes:\n- \n\nURLs:\n- \n\n",
                "Timeline": "\n--- TIMELINE ---\n[TIME] Event description\n[TIME] Event description\n\n",
                "Remediation": "\n--- REMEDIATION STEPS ---\n1. \n2. \n3. \n\n",
                "Executive Summary": "\n--- EXECUTIVE SUMMARY ---\nThreat Level: \nImpact: \nRecommended Actions: \n\n"
            }
            self.save_snippets()
    except Exception as e:
        print(f"Error loading snippets: {e}")
        self.snippets = {}

def save_snippets(self):
    try:
        with open(self.config.SNIPPETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.snippets, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving snippets: {e}")

def on_snippet_select(self, event=None):
    selection = self.snippets_listbox.curselection()
    if selection:
        snippet_name = self.snippets_listbox.get(selection[0])
        self.snippet_name_var.set(snippet_name)
        self.snippet_text.delete('1.0', tk.END)
        self.snippet_text.insert('1.0', self.snippets.get(snippet_name, ''))

def add_snippet(self):
    name = self.snippet_name_var.get().strip()
    content = self.snippet_text.get('1.0', 'end-1c')
    if not name:
        messagebox.showerror("Error", "Please enter a snippet name.")
        return
    if name in self.snippets:
        if not messagebox.askyesno("Confirm", f"Snippet '{name}' already exists. Replace it?"):
            return
    self.snippets[name] = content
    if name not in [self.snippets_listbox.get(i) for i in range(self.snippets_listbox.size())]:
        self.snippets_listbox.insert(tk.END, name)
    self.update_status(f"Snippet '{name}' added")

def update_snippet(self):
    selection = self.snippets_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a snippet to update.")
        return
    old_name = self.snippets_listbox.get(selection[0])
    new_name = self.snippet_name_var.get().strip()
    content = self.snippet_text.get('1.0', 'end-1c')
    if not new_name:
        messagebox.showerror("Error", "Please enter a snippet name.")
        return
    if old_name != new_name:
        del self.snippets[old_name]
        self.snippets_listbox.delete(selection[0])
        self.snippets_listbox.insert(selection[0], new_name)
    self.snippets[new_name] = content
    self.update_status(f"Snippet '{new_name}' updated")

def delete_snippet(self):
    selection = self.snippets_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a snippet to delete.")
        return
    snippet_name = self.snippets_listbox.get(selection[0])
    if messagebox.askyesno("Confirm", f"Delete snippet '{snippet_name}'?"):
        del self.snippets[snippet_name]
        self.snippets_listbox.delete(selection[0])
        self.snippet_name_var.set('')
        self.snippet_text.delete('1.0', tk.END)
        self.update_status(f"Snippet '{snippet_name}' deleted")

def insert_snippet(self, snippet_name):
    current = self.notebook.select()
    if not current:
        return
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    if snippet_name in self.snippets:
        content = self.snippets[snippet_name]
        content = content.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
        content = content.replace('{time}', datetime.now().strftime('%H:%M:%S'))
        content = content.replace('{datetime}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        text_widget.insert('insert', content)
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)
        self.update_status(f"Inserted snippet: {snippet_name}")

# --------------------- Template Management ---------------------
def create_templates_tab(self, parent):
    self.load_templates_data()
    ttk.Label(parent, text="Configure templates for quick insertion:").pack(anchor="w", padx=10, pady=5)
    
    list_frame = ttk.Frame(parent)
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    left_frame = ttk.Frame(list_frame)
    left_frame.pack(side="left", fill="both", expand=True)
    ttk.Label(left_frame, text="Templates:").pack(anchor="w")
    self.templates_listbox = tk.Listbox(left_frame)
    self.templates_listbox.pack(fill="both", expand=True)
    self.templates_listbox.bind('<<ListboxSelect>>', self.on_template_select)
    for name in self.templates.keys():
        self.templates_listbox.insert(tk.END, name)
    
    right_frame = ttk.Frame(list_frame)
    right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
    ttk.Label(right_frame, text="Template Name:").pack(anchor="w")
    self.template_name_var = tk.StringVar()
    ttk.Entry(right_frame, textvariable=self.template_name_var).pack(fill="x")
    ttk.Label(right_frame, text="Template Content:").pack(anchor="w", pady=(10, 0))
    self.template_text = tk.Text(right_frame, height=8)
    self.template_text.pack(fill="both", expand=True)
    
    button_frame = ttk.Frame(right_frame)
    button_frame.pack(fill="x", pady=5)
    ttk.Button(button_frame, text="Add", command=self.add_template).pack(side="left", padx=2)
    ttk.Button(button_frame, text="Update", command=self.update_template).pack(side="left", padx=2)
    ttk.Button(button_frame, text="Delete", command=self.delete_template).pack(side="left", padx=2)

def on_template_select(self, event=None):
    selection = self.templates_listbox.curselection()
    if selection:
        template_name = self.templates_listbox.get(selection[0])
        self.template_name_var.set(template_name)
        self.template_text.delete('1.0', tk.END)
        self.template_text.insert('1.0', self.templates.get(template_name, ''))

def add_template(self):
    name = self.template_name_var.get().strip()
    content = self.template_text.get('1.0', 'end-1c')
    if not name:
        messagebox.showerror("Error", "Please enter a template name.")
        return
    if name in self.templates:
        if not messagebox.askyesno("Confirm", f"Template '{name}' already exists. Replace it?"):
            return
    self.templates[name] = content
    if name not in [self.templates_listbox.get(i) for i in range(self.templates_listbox.size())]:
        self.templates_listbox.insert(tk.END, name)
    self.update_status(f"Template '{name}' added")

def update_template(self):
    selection = self.templates_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a template to update.")
        return
    old_name = self.templates_listbox.get(selection[0])
    new_name = self.template_name_var.get().strip()
    content = self.template_text.get('1.0', 'end-1c')
    if not new_name:
        messagebox.showerror("Error", "Please enter a template name.")
        return
    if old_name != new_name:
        del self.templates[old_name]
        self.templates_listbox.delete(selection[0])
        self.templates_listbox.insert(selection[0], new_name)
    self.templates[new_name] = content
    self.update_status(f"Template '{new_name}' updated")

def delete_template(self):
    selection = self.templates_listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "Please select a template to delete.")
        return
    template_name = self.templates_listbox.get(selection[0])
    if messagebox.askyesno("Confirm", f"Delete template '{template_name}'?"):
        del self.templates[template_name]
        self.templates_listbox.delete(selection[0])
        self.template_name_var.set('')
        self.template_text.delete('1.0', tk.END)
        self.update_status(f"Template '{template_name}' deleted")

# --------------------- Hashing and Encoding ---------------------
def generate_hash(self, hash_type):
    current = self.notebook.select()
    if not current:
        return
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    try:
        selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:
        selected_text = text_widget.get("1.0", "end-1c")
    if not selected_text.strip():
        messagebox.showwarning("Warning", "No text to hash.")
        return
    text_bytes = selected_text.encode('utf-8')
    if hash_type == 'md5':
        hash_value = hashlib.md5(text_bytes).hexdigest()
    elif hash_type == 'sha1':
        hash_value = hashlib.sha1(text_bytes).hexdigest()
    elif hash_type == 'sha256':
        hash_value = hashlib.sha256(text_bytes).hexdigest()
    else:
        messagebox.showerror("Error", f"Unknown hash type: {hash_type}")
        return
    self.show_hash_result(hash_type.upper(), hash_value, selected_text)

def show_hash_result(self, hash_type, hash_value, original_text):
    result_window = tk.Toplevel(self.root)
    result_window.title(f"{hash_type} Hash Result")
    result_window.geometry("600x400")
    result_window.transient(self.root)
    result_window.update_idletasks()
    x = (result_window.winfo_screenwidth() // 2) - (result_window.winfo_width() // 2)
    y = (result_window.winfo_screenheight() // 2) - (result_window.winfo_height() // 2)
    result_window.geometry(f"+{x}+{y}")
    
    ttk.Label(result_window, text="Original Text:").pack(anchor="w", padx=10, pady=5)
    original_frame = tk.Frame(result_window)
    original_frame.pack(fill="both", expand=True, padx=10, pady=5)
    original_text_widget = tk.Text(original_frame, height=6, wrap=tk.WORD)
    original_scrollbar = ttk.Scrollbar(original_frame, orient="vertical", command=original_text_widget.yview)
    original_text_widget.config(yscrollcommand=original_scrollbar.set)
    original_text_widget.pack(side="left", fill="both", expand=True)
    original_scrollbar.pack(side="right", fill="y")
    original_text_widget.insert("1.0", original_text)
    original_text_widget.config(state="disabled")
    
    ttk.Label(result_window, text=f"{hash_type} Hash:").pack(anchor="w", padx=10, pady=5)
    hash_frame = tk.Frame(result_window)
    hash_frame.pack(fill="x", padx=10, pady=5)
    hash_entry = tk.Entry(hash_frame, font=("Consolas", 10))
    hash_entry.pack(side="left", fill="x", expand=True)
    hash_entry.insert(0, hash_value)
    hash_entry.config(state="readonly")
    ttk.Button(hash_frame, text="Copy Hash",
              command=lambda: self.copy_to_clipboard(hash_value, f"{hash_type} hash copied")).pack(side="right", padx=5)
    ttk.Button(result_window, text="Close", command=result_window.destroy).pack(pady=10)

def identify_hash_type(self):
    current = self.notebook.select()
    if not current:
        return
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    try:
        selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
    except tk.TclError:
        selected_text = ""
    if not selected_text:
        hash_input = tk.simpledialog.askstring("Hash Identification", "Enter hash to identify:")
        if not hash_input:
            return
        selected_text = hash_input.strip()
    hash_types = []
    if re.match(r'^[a-fA-F0-9]{32}$', selected_text):
        hash_types.append("MD5")
    if re.match(r'^[a-fA-F0-9]{40}$', selected_text):
        hash_types.append("SHA1")
    if re.match(r'^[a-fA-F0-9]{64}$', selected_text):
        hash_types.append("SHA256")
    if re.match(r'^[a-fA-F0-9]{96}$', selected_text):
        hash_types.append("SHA384")
    if re.match(r'^[a-fA-F0-9]{128}$', selected_text):
        hash_types.append("SHA512")
    result = f"Possible hash type(s): {', '.join(hash_types)}" if hash_types else "Unknown hash type or invalid format"
    messagebox.showinfo("Hash Type Identification",
                       f"Input: {selected_text[:50]}{'...' if len(selected_text) > 50 else ''}\n\n{result}")

def base64_encode(self):
    current = self.notebook.select()
    if not current:
        return
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    try:
        selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:
        selected_text = text_widget.get("1.0", "end-1c")
    if not selected_text.strip():
        messagebox.showwarning("Warning", "No text to encode.")
        return
    try:
        encoded = base64.b64encode(selected_text.encode('utf-8')).decode('ascii')
        self.show_encoding_result("Base64 Encode", selected_text, encoded)
    except Exception as e:
        messagebox.showerror("Error", f"Could not encode text: {e}")

def base64_decode(self):
    current = self.notebook.select()
    if not current:
        return
    current_frame = self.notebook.nametowidget(current)
    text_widget = self.get_text_widget(current_frame)
    try:
        selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
    except tk.TclError:
        selected_text = text_widget.get("1.0", "end-1c").strip()
    if not selected_text:
        messagebox.showwarning("Warning", "No text to decode.")
        return
    try:
        decoded = base64.b64decode(selected_text).decode('utf-8')
        self.show_encoding_result("Base64 Decode", selected_text, decoded)
    except Exception as e:
        messagebox.showerror("Error", f"Could not decode Base64: {e}")

def show_encoding_result(self, operation, input_text, output_text):
    result_window = tk.Toplevel(self.root)
    result_window.title(f"{operation} Result")
    result_window.geometry("600x500")
    result_window.transient(self.root)
    result_window.update_idletasks()
    x = (result_window.winfo_screenwidth() // 2) - (result_window.winfo_width() // 2)
    y = (result_window.winfo_screenheight() // 2) - (result_window.winfo_height() // 2)
    result_window.geometry(f"+{x}+{y}")
    
    ttk.Label(result_window, text="Input:").pack(anchor="w", padx=10, pady=5)
    input_frame = tk.Frame(result_window)
    input_frame.pack(fill="both", expand=True, padx=10, pady=5)
    input_text_widget = tk.Text(input_frame, height=8, wrap=tk.WORD)
    input_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=input_text_widget.yview)
    input_text_widget.config(yscrollcommand=input_scrollbar.set)
    input_text_widget.pack(side="left", fill="both", expand=True)
    input_scrollbar.pack(side="right", fill="y")
    input_text_widget.insert("1.0", input_text)
    input_text_widget.config(state="disabled")
    
    ttk.Label(result_window, text="Output:").pack(anchor="w", padx=10, pady=5)
    output_frame = tk.Frame(result_window)
    output_frame.pack(fill="both", expand=True, padx=10, pady=5)
    output_text_widget = tk.Text(output_frame, height=8, wrap=tk.WORD)
    output_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=output_text_widget.yview)
    output_text_widget.config(yscrollcommand=output_scrollbar.set)
    output_text_widget.pack(side="left", fill="both", expand=True)
    output_scrollbar.pack(side="right", fill="y")
    output_text_widget.insert("1.0", output_text)
    output_text_widget.config(state="disabled")
    
    button_frame = tk.Frame(result_window)
    button_frame.pack(fill="x", padx=10, pady=10)
    ttk.Button(button_frame, text="Copy Output",
              command=lambda: self.copy_to_clipboard(output_text, "Output copied")).pack(side="left")
    ttk.Button(button_frame, text="Insert at Cursor",
              command=lambda: self.insert_at_cursor(output_text, result_window)).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Close", command=result_window.destroy).pack(side="right")

def copy_to_clipboard(self, text, message):
    self.root.clipboard_clear()
    self.root.clipboard_append(text)
    self.update_status(message)

def insert_at_cursor(self, text, window_to_close):
    current = self.notebook.select()
    if current:
        current_frame = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(current_frame)
        text_widget.insert('insert', text)
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)
    window_to_close.destroy()
    self.update_status("Text inserted at cursor")

def update_status(self, text):
    self.status_left.config(text=text)
    current = self.notebook.select()
    if current:
        try:
            current_frame = self.notebook.nametowidget(current)
            text_widget = self.get_text_widget(current_frame)
            content = text_widget.get("1.0", "end-1c")
            line_count = int(text_widget.index('end-1c').split('.')[0])
            char_count = len(content)
            word_count = len(content.split()) if content.strip() else 0
            cursor_pos = text_widget.index('insert')
            cursor_line, cursor_col = cursor_pos.split('.')
            timestamp = datetime.now().strftime("%H:%M:%S")
            stats_text = f"Ln {cursor_line}, Col {cursor_col} | Lines: {line_count} | Words: {word_count} | Chars: {char_count} | {timestamp}"
            self.status_right.config(text=stats_text)
        except:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.status_right.config(text=timestamp)
    else:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_right.config(text=timestamp)

def auto_save(self):
    for frame, text_container in self.tabs.items():
        filepath = self.current_file_paths.get(frame)
        if filepath:
            text_widget = text_container.text if hasattr(text_container, 'text') else text_container
            text = text_widget.get("1.0", "end-1c")
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text)
            except Exception as e:
                print(f"Auto-save error: {e}")
    self.save_session()
    self.root.after(60000, self.auto_save)

def on_closing(self):
    self.save_session()
    unsaved_tabs = []
    for frame, text_container in self.tabs.items():
        text_widget = text_container.text if hasattr(text_container, 'text') else text_container
        if text_widget.get("1.0", "end-1c").strip():
            filepath = self.current_file_paths.get(frame)
            if not filepath:
                tab_name = self.notebook.tab(frame, "text")
                unsaved_tabs.append(tab_name)
    if unsaved_tabs and not messagebox.askyesno(
        "Unsaved Changes",
        f"You have unsaved changes in {len(unsaved_tabs)} tab(s).\nDo you want to quit anyway?"
    ):
        return
    self.root.destroy()

def run(self):
    self.root.mainloop()
```

# ——————— Main ———————

if **name** == “**main**”:
app = SOCNotesApp()
app.run()
