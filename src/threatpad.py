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
try:
    from ascii_menu import ASCIIMenuIntegration
    ASCII_MENU_AVAILABLE = True
except Exception:
    ASCII_MENU_AVAILABLE = False
    ASCIIMenuIntegration = None


# --------------------- Helpers ---------------------
def _darken_hex(hex_colour, factor=0.7):
    """Return a darkened version of a #rrggbb hex colour string."""
    hex_colour = hex_colour.lstrip('#')
    r, g, b = int(hex_colour[0:2], 16), int(hex_colour[2:4], 16), int(hex_colour[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


# --------------------- Config ---------------------
class Config:
    CUSTOM_DICT_FILE = "custom_dict.txt"
    TEMPLATE_DIR = "templates"
    RECENT_FILE = "recent_files.txt"
    SESSION_FILE = "session.json"
    SNIPPETS_FILE = "copy_pasta_snippets.json"
    TEMPLATES_FILE = "templates.json"
    MAX_RECENT = 10
    DARK_MODE = False
    FOLLOW_SYSTEM_THEME = False
    LINE_NUMBERS = True
    WORD_WRAP = True
    FONT_SIZE = 12
    FONT_FAMILY = "Consolas"
    SYNTAX_HIGHLIGHTING = True
    APP_DATA_FILE = "app_settings.json"
    AUTO_SAVE_INTERVAL = 60000  # milliseconds
    TRAINING_WHEELS = False
    COPY_CLEAR = False
    COPY_COUNT_WARN = True
    # Appearance themes
    THEME_NAME = 'Default Dark'
    CUSTOM_BG = ''
    CUSTOM_FG = ''
    CUSTOM_ACCENT = ''
    # API Keys for IOC enrichment
    API_KEYS = {
        'virustotal': '',
        'abuseipdb': ''
    }
    LOCK_PASSWORD = "unlock"
    CLIENTS = ["Client Alpha", "Client Beta", "Client Gamma"]
    CLIPBOARD_CLEAR_DELAY = 0   # seconds after copy; 0 = disabled


# --------------------- System Theme Detection ---------------------
def get_system_theme():
    """Detect system theme preference"""
    try:
        system = platform.system()
        if system == "Windows":
            return get_windows_theme()
        elif system == "Darwin":  # macOS
            return get_macos_theme()
        elif system == "Linux":
            return get_linux_theme()
    except Exception as e:
        print(f"Error detecting system theme: {e}")
    return False  # Default to light theme

def get_windows_theme():
    """Get Windows theme preference from registry"""
    try:
        import winreg
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0  # 0 = dark theme, 1 = light theme
    except (ImportError, OSError):
        return False

def get_macos_theme():
    """Get macOS theme preference"""
    try:
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
            capture_output=True, text=True, timeout=5
        )
        return 'dark' in result.stdout.lower()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_linux_theme():
    """Get Linux theme preference (basic implementation)"""
    try:
        # Try to detect GNOME dark theme
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'],
            capture_output=True, text=True, timeout=5
        )
        return 'dark' in result.stdout.lower()
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False


class LineNumberText(tk.Frame):
    """Text widget with line numbers"""
    def __init__(self, parent, show_lines=True, **kwargs):
        tk.Frame.__init__(self, parent)
        self.show_lines = show_lines
        
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


class CustomNotebook(ttk.Notebook):
    """ttk.Notebook with built-in per-tab × close buttons via a custom style."""

    _images = {}        # class-level keeps PhotoImages from being GC'd
    _style_ready = False

    def __init__(self, master, on_close=None, **kwargs):
        if not CustomNotebook._style_ready:
            CustomNotebook._build_style(master)
            CustomNotebook._style_ready = True
        kwargs.setdefault("style", "CustomNotebook")
        super().__init__(master, **kwargs)
        self._on_close = on_close   # callable(tab_index)
        self._pressed  = None
        self.bind("<ButtonPress-1>",   self._on_press,   True)
        self.bind("<ButtonRelease-1>", self._on_release, True)

    @classmethod
    def _build_style(cls, master):
        def _make_x(fg, bg):
            img = tk.PhotoImage(width=10, height=10, master=master)
            img.put(bg, to=(0, 0, 10, 10))
            for x, y in [(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8),
                         (8,1),(7,2),(6,3),(5,4),(4,5),(3,6),(2,7),(1,8)]:
                img.put(fg, to=(x, y, x+1, y+1))
            return img

        cls._images["normal"]  = _make_x("#555555", "#d9d9d9")
        cls._images["active"]  = _make_x("#cc0000", "#f0c0c0")
        cls._images["pressed"] = _make_x("#ffffff", "#cc0000")

        s = ttk.Style(master)
        s.element_create(
            "CustomNotebook.close", "image",
            cls._images["normal"],
            ("active", "pressed", "!disabled", cls._images["pressed"]),
            ("active", "!disabled",             cls._images["active"]),
            border=4, sticky="",
        )
        s.layout("CustomNotebook",
                 [("CustomNotebook.client", {"sticky": "nswe"})])
        s.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("CustomNotebook.padding", {
                        "side": "top", "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.focus", {
                                "side": "top", "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.label",
                                     {"side": "left", "sticky": ""}),
                                    ("CustomNotebook.close",
                                     {"side": "left", "sticky": ""}),
                                ],
                            })
                        ],
                    })
                ],
            })
        ])

    def _on_press(self, event):
        elem = self.identify(event.x, event.y)
        if "close" in elem:
            try:
                self._pressed = self.index(f"@{event.x},{event.y}")
                self.state(["pressed"])
            except tk.TclError:
                pass

    def _on_release(self, event):
        if not self.instate(["pressed"]):
            return
        self.state(["!pressed"])
        elem = self.identify(event.x, event.y)
        if "close" in elem and self._pressed is not None:
            try:
                idx = self.index(f"@{event.x},{event.y}")
                if idx == self._pressed and self._on_close:
                    self._on_close(idx)
            except tk.TclError:
                pass
        self._pressed = None


class SOCNotesApp:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("ThreatPad")
        self.root.geometry("1200x800")

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
        self._tab_copy_counts = {}
        self.clients = {}
        self.active_client = ''
        self._contamination_job = None
        self.current_file_paths = {}  # Track file paths for each tab
        self.recent_files = []
        self.find_dialog = None
        self._mileage = {}
        self._tab_timers = {}
        self._timer_job = None
        self._action_log = []
        self._traffic_light_job = None
        self._tab_locked_client = {}
        self._closed_tabs      = []   # list of (title, content, filepath) — recently closed
        self._pinned_tabs      = set()
        self._bookmarks        = {}   # {frame: set of line numbers}
        self._tab_colour_images = {}  # {frame: PhotoImage} — prevents GC
        self._redaction_on     = False
        self._clipboard_clear_job = None
        self._ioc_panel_win    = None
        
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

        # ASCII Quick Menu integration
        self.ascii_menu_integration = None
        if ASCII_MENU_AVAILABLE:
            self.ascii_menu_integration = ASCIIMenuIntegration(self)
        
        # Initialize IOC enrichment if available
        self.enrichment_engine = None
        if IOC_ENRICHMENT_AVAILABLE:
            self.enrichment_engine = IOCEnrichment(api_keys=self.config.API_KEYS)
        
        self.setup_ui()
        self.setup_keybindings()
        self.setup_drag_drop()

        # Always show welcome tab first, then restore session
        self.new_welcome_tab()
        if not self.load_session():
            self.new_tab()
        # Select the welcome tab (always first)
        tabs = self.notebook.tabs()
        if tabs:
            self.notebook.select(tabs[0])

        # Setup auto-save
        self.auto_save()

    # --------------------- Settings ---------------------
    def load_settings(self):
        try:
            if os.path.exists(self.config.APP_DATA_FILE):
                with open(self.config.APP_DATA_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.config.DARK_MODE = settings.get('dark_mode', False)
                    self.config.FOLLOW_SYSTEM_THEME = settings.get('follow_system_theme', False)
                    self.config.LINE_NUMBERS = settings.get('line_numbers', True)
                    self.config.WORD_WRAP = settings.get('word_wrap', True)
                    self.config.FONT_SIZE = settings.get('font_size', 12)
                    self.config.FONT_FAMILY = settings.get('font_family', 'Consolas')
                    self.config.SYNTAX_HIGHLIGHTING = settings.get('syntax_highlighting', True)
                    self.config.API_KEYS = settings.get('api_keys', {'virustotal': '', 'abuseipdb': ''})
                    self.config.TRAINING_WHEELS = settings.get('training_wheels', False)
                    self.config.COPY_CLEAR = settings.get('copy_clear', False)
                    self.config.COPY_COUNT_WARN = settings.get('copy_count_warn', True)
                    self.config.CLIPBOARD_CLEAR_DELAY = settings.get('clipboard_clear_delay', 0)
                    self.config.LOCK_PASSWORD = settings.get('lock_password', 'unlock')
                    raw_clients = settings.get('clients', {})
                    # Migrate: older saves stored clients as a plain list of names
                    if isinstance(raw_clients, list):
                        raw_clients = {name: {} for name in raw_clients}
                    self.clients = raw_clients
                    self.active_client = settings.get('active_client', '')
                    self.config.THEME_NAME = settings.get('theme_name', 'Default Dark')
                    saved_mileage = settings.get('mileage', {})
                    if saved_mileage:
                        self._mileage.update(saved_mileage)
                    custom = settings.get('training_checklists', None)
                    if custom:
                        self.TRAINING_CHECKLISTS = {
                            k: [(s, list(items)) for s, items in v]
                            for k, v in custom.items()
                        }
            
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
                'api_keys': self.config.API_KEYS,
                'training_wheels': self.config.TRAINING_WHEELS,
                'copy_clear': self.config.COPY_CLEAR,
                'copy_count_warn': self.config.COPY_COUNT_WARN,
                'clipboard_clear_delay': self.config.CLIPBOARD_CLEAR_DELAY,
                'lock_password': self.config.LOCK_PASSWORD,
                'clients': self.clients,
                'active_client': self.active_client,
                'theme_name': self.config.THEME_NAME,
                'mileage': self._mileage,
                'training_checklists': {
                    k: [[s, list(items)] for s, items in v]
                    for k, v in self.TRAINING_CHECKLISTS.items()
                }
            }
            with open(self.config.APP_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_recent_files(self):
        try:
            if os.path.exists(self.config.RECENT_FILE):
                with open(self.config.RECENT_FILE, 'r', encoding='utf-8') as f:
                    self.recent_files = [line.strip() for line in f.readlines()]
        except Exception as e:
            print(f"Error loading recent files: {e}")

    def save_recent_files(self):
        try:
            with open(self.config.RECENT_FILE, 'w', encoding='utf-8') as f:
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
                with open(self.config.SESSION_FILE, 'r', encoding='utf-8') as f:
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
                title = self.notebook.tab(frame, "text")
                filepath = self.current_file_paths.get(frame)
                session['tabs'].append({
                    'title': title,
                    'content': content,
                    'filepath': filepath
                })
            with open(self.config.SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(session, f)
        except Exception as e:
            print(f"Error saving session: {e}")

    # --------------------- UI Setup ---------------------
    def setup_ui(self):
        from datetime import datetime as _dt
        if not self._mileage.get('session_start'):
            self._mileage['session_start'] = _dt.now().isoformat()
        self.setup_menu()
        self.setup_training_wheels_panel()
        self.setup_notebook()
        self.setup_buttons()
        self.setup_status_bar()

        if self.config.DARK_MODE:
            self.apply_dark_mode()
        # Restore theme preset if set
        if hasattr(self.config, 'THEME_NAME') and self.config.THEME_NAME not in ('Default Dark', 'Default Light', ''):
            self.root.after(200, lambda: self._apply_theme_preset(self.config.THEME_NAME))

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
        file_menu.add_command(label="Export HTML Report...", command=self.export_html_report)
        file_menu.add_command(label="Export JSON Report...", command=self.export_json_report)
        file_menu.add_separator()
        file_menu.add_command(label="Reopen Closed Tab", command=self.reopen_closed_tab, accelerator="Ctrl+Shift+T")
        file_menu.add_separator()
        file_menu.add_command(
            label="Quick Action Menu  Ctrl+`",
            command=lambda: self.ascii_menu_integration.show_menu()
                    if self.ascii_menu_integration else None)
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
        edit_menu.add_command(label="IOC Panel (live)", command=self.toggle_ioc_panel)
        if IOC_ENRICHMENT_AVAILABLE:
            edit_menu.add_command(label="Enrich IOCs...", command=self.enrich_iocs, accelerator="Ctrl+Shift+E")
        edit_menu.add_separator()
        edit_menu.add_command(label="Jump to Line...", command=self.jump_to_line, accelerator="Ctrl+G")
        edit_menu.add_command(label="Toggle Bookmark", command=self.toggle_bookmark, accelerator="F2")
        edit_menu.add_command(label="Next Bookmark", command=self.next_bookmark, accelerator="Ctrl+F2")
        edit_menu.add_command(label="Prev Bookmark", command=self.prev_bookmark, accelerator="Shift+F2")
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
        self.training_wheels_var = tk.BooleanVar(value=self.config.TRAINING_WHEELS)
        view_menu.add_checkbutton(label="Training Wheels Mode", variable=self.training_wheels_var,
                                  command=self.toggle_training_wheels)
        view_menu.add_separator()
        view_menu.add_command(label="Increase Font Size", command=self.increase_font_size, accelerator="Ctrl++")
        view_menu.add_command(label="Decrease Font Size", command=self.decrease_font_size, accelerator="Ctrl+-")
        view_menu.add_separator()
        view_menu.add_command(label="🔴 Toggle Redaction Mode", command=self.toggle_redaction)
        view_menu.add_command(label="🔒 Lock Session", command=self.lock_session, accelerator="Ctrl+L")
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
        self.notebook = CustomNotebook(self.root, on_close=self._close_tab_by_index)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        # Middle-click closes a tab, right-click opens colour menu
        self.notebook.bind("<Button-2>", self.on_tab_middle_click)
        self.notebook.bind("<Button-3>", self.show_tab_colour_menu)

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

    def _add_close_button(self, tab_id):
        pass  # handled by CustomNotebook style

    def _remove_close_button(self, tab_id):
        pass  # handled by CustomNotebook style

    def _reposition_close_buttons(self):
        pass  # handled by CustomNotebook style

    def _do_reposition_close_buttons(self):
        pass  # handled by CustomNotebook style

    def _close_tab_by_index(self, idx):
        """Close the tab at the given notebook index."""
        tab_id = self.notebook.tabs()[idx]
        self._remove_close_button(tab_id)
        current_frame = self.notebook.nametowidget(tab_id)
        # Clean up all per-tab state
        self._tab_copy_counts.pop(current_frame, None)
        self._tab_timers.pop(current_frame, None)
        self._tab_locked_client.pop(current_frame, None)
        self._log_action('tab_closed', self.notebook.tab(tab_id, 'text') if tab_id in self.notebook.tabs() else 'unknown')
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
        
        # IOC manipulation buttons -- store refs so we can re-colour on theme change
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

        # Centre — Client selector
        centre_frame = tk.Frame(self.frame_buttons)
        centre_frame.pack(side="left", padx=12)
        tk.Label(centre_frame, text="🏢 Client:", font=("Consolas", 9, "bold")).pack(side="left")
        self.active_client_var = tk.StringVar(value=self.active_client or "— None —")
        self.client_combo = ttk.Combobox(centre_frame, textvariable=self.active_client_var,
            state="readonly", width=20, font=("Consolas", 9))
        self.client_combo.pack(side="left", padx=(4, 2))
        self.client_combo.bind("<<ComboboxSelected>>", self._on_client_selected)
        self._refresh_client_combo()
        self.check_btn = tk.Button(centre_frame, text="⚠ Check",
            command=self.run_contamination_check, font=("Consolas", 9), width=8,
            bg="#CC7722", fg="white", activebackground="#994400",
            activeforeground="white", relief="flat")
        self.check_btn.pack(side="left", padx=2)
        self.add_tooltip(self.check_btn, "Scan for cross-client data contamination")

        # Right side - Copy, traffic light, Breakglass, timer
        right_frame = tk.Frame(self.frame_buttons)
        right_frame.pack(side="right")

        self.validation_label = tk.Label(right_frame, text="", width=13, anchor="e")
        self.validation_label.pack(side="right", padx=5)

        # Traffic light canvas — 3 stacked circles
        self.traffic_light_canvas = tk.Canvas(right_frame, width=18, height=18,
            highlightthickness=0, bd=0)
        self.traffic_light_canvas.pack(side="right", padx=(0, 4))
        self._tl_circle = self.traffic_light_canvas.create_oval(
            2, 2, 16, 16, fill="#555555", outline="#333333", width=1)
        self.add_tooltip(self.traffic_light_canvas,
            "Note health: Grey=empty, Red=contamination, Amber=undefanged IOCs, Green=clean")

        self.copy_button = tk.Button(
            right_frame, text="Safe Copy", command=self.safe_copy_text,
            width=10
        )
        self.copy_button.pack(side="right", padx=2)
        self.add_tooltip(self.copy_button, "Copy text with IOC safety warnings")

        # Breakglass button
        self.breakglass_btn = tk.Button(
            right_frame, text="🚨 Breakglass", command=self.show_breakglass_mode,
            font=("Consolas", 9, "bold"), width=10,
            bg="#8B0000", fg="white",
            activebackground="#cc0000", activeforeground="white", relief="flat"
        )
        self.breakglass_btn.pack(side="right", padx=(6, 2))
        self.add_tooltip(self.breakglass_btn, "Emergency: I think I've made a mistake")

        # Per-tab incident timer label
        self.timer_label = tk.Label(right_frame, text="⏱ --:--",
            font=("Consolas", 9), fg="#888888", anchor="e", width=8)
        self.timer_label.pack(side="right", padx=(4, 2))

        self.update_button_colors()
    
    def add_tooltip(self, widget, text):
        """Add tooltip to widget"""
        def on_enter(event):
            tooltip = tk.Toplevel(self.root)
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

        if hasattr(self, 'check_btn'):
            self.check_btn.config(bg="#CC7722", fg="#ffffff",
                activebackground="#994400", activeforeground="#ffffff")
        if hasattr(self, 'breakglass_btn'):
            self.breakglass_btn.config(bg="#8B0000", fg="#ffffff",
                activebackground="#cc0000", activeforeground="#ffffff")
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
        self.root.bind('<Control-plus>',  lambda e: self.increase_font_size())
        self.root.bind('<Control-equal>', lambda e: self.increase_font_size())
        self.root.bind('<Control-minus>', lambda e: self.decrease_font_size())
        self.root.bind('<Control-Shift-T>', lambda e: self.reopen_closed_tab())
        self.root.bind('<Control-l>', lambda e: self.lock_session())
        self.root.bind('<Control-g>', lambda e: self.jump_to_line())
        self.root.bind('<F2>',        lambda e: self.toggle_bookmark())
        self.root.bind('<Control-F2>', lambda e: self.next_bookmark())
        self.root.bind('<Shift-F2>',   lambda e: self.prev_bookmark())
        # ASCII Quick Menu keybindings
        if self.ascii_menu_integration:
            self.ascii_menu_integration.bind_keys()
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
                except UnicodeDecodeError:
                    messagebox.showerror("Error", f"Cannot open binary file: {os.path.basename(file)}\nOnly text files are supported.")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open {file}: {e}")


    # --------------------- Training Wheels ---------------------

    TRAINING_CHECKLISTS = {
        "Phishing": [
            ("TRIAGE", [
                "Identify the reporting user and collection method (email forward, ticket, verbal)",
                "Obtain the original email headers (not a screenshot -- raw headers)",
                "Confirm whether the email was clicked, credentials entered, or attachments opened",
                "Check how many users received the same email (targeted vs. bulk campaign)",
            ]),
            ("EMAIL ANALYSIS", [
                "Extract and defang sender address, reply-to, and return-path fields",
                "Check SPF, DKIM, and DMARC alignment in headers",
                "Extract all URLs from body and headers -- defang before logging",
                "Extract any attachment names, types, and hashes (MD5/SHA256)",
                "Check sending infrastructure: IP reputation via AbuseIPDB, domain age/WHOIS",
            ]),
            ("IOC ENRICHMENT", [
                "Submit URLs to VirusTotal / URLScan.io",
                "Submit attachment hashes to VirusTotal",
                "Check sender domain against threat intel feeds",
                "Search SIEM for same sender, subject, or URL across all users",
            ]),
            ("CONTAINMENT", [
                "Block sender address and sending IP at email gateway",
                "Block identified malicious URLs at proxy/firewall",
                "Quarantine or delete the email from all affected mailboxes",
                "If credentials were entered: initiate password reset immediately",
                "If attachment was opened: isolate the endpoint for forensic review",
            ]),
            ("ESCALATION CHECK", [
                "Were credentials compromised? → Escalate to L2 / Identity team",
                "Was malware executed? → Escalate to L2 / IR team, isolate host",
                "Is this a targeted spearphishing campaign? → Escalate to L2",
                "Multiple users affected across departments? → Escalate to L2",
            ]),
            ("CLOSURE", [
                "Document full timeline: reported → triaged → contained → resolved",
                "Record all IOCs extracted in the ticket",
                "Confirm no further mailboxes are affected",
                "User awareness: advise reporting user of outcome",
                "Lessons learned: was anything missed in filtering/detection?",
            ]),
        ],
        "Malware": [
            ("TRIAGE", [
                "Identify the affected host(s): hostname, IP, OS, owner, department",
                "Determine detection source: AV alert, EDR, SIEM rule, user report",
                "Confirm malware family if known (ransomware, trojan, infostealer, etc.)",
                "Establish initial infection vector if possible (email, web, USB, lateral)",
            ]),
            ("EVIDENCE COLLECTION", [
                "Capture the file path, name, and hash (MD5 + SHA256) of the malicious file",
                "Pull process tree: parent process, child processes, command-line arguments",
                "Capture network connections made by the process at time of execution",
                "Pull relevant event logs: 4688 (process creation), 7045 (service install), Sysmon if available",
                "Note any persistence mechanisms: registry run keys, scheduled tasks, services",
            ]),
            ("IOC ENRICHMENT", [
                "Submit file hash to VirusTotal -- note detection ratio and family",
                "Check C2 IPs/domains against AbuseIPDB and threat intel",
                "Search SIEM for same hash or C2 across all endpoints",
                "Check for lateral movement: same user or admin credentials used elsewhere?",
            ]),
            ("CONTAINMENT", [
                "Isolate the affected endpoint from the network immediately",
                "Block identified C2 IPs and domains at firewall/proxy",
                "Disable or reset any accounts that ran the malicious process",
                "Revoke any tokens or sessions associated with compromised accounts",
                "Notify endpoint owner and their manager",
            ]),
            ("ESCALATION CHECK", [
                "Is this ransomware or wiper malware? → Escalate to L2 / IR immediately",
                "Evidence of lateral movement or credential harvesting? → Escalate to L2",
                "Multiple hosts affected? → Escalate to L2",
                "Persistence mechanism found? → Escalate to L2 for full remediation",
            ]),
            ("CLOSURE", [
                "Confirm endpoint has been reimaged or fully remediated",
                "Verify C2 blocks are in place and verified at network layer",
                "Confirm no other hosts are affected via SIEM sweep",
                "Document full attack chain in ticket with timeline",
                "Update detection rules if this bypassed existing signatures",
            ]),
        ],
        "Brute Force": [
            ("TRIAGE", [
                "Identify the targeted account(s) and service (VPN, RDP, OWA, SSH, etc.)",
                "Determine source IP(s) -- single IP, distributed, or credential stuffing pattern",
                "Check whether any authentication attempts succeeded",
                "Identify timeframe: first failed attempt to detection time",
            ]),
            ("INVESTIGATION", [
                "Pull authentication logs for the targeted account(s) -- last 7 days minimum",
                "Check for successful logins from unusual IPs, locations, or times",
                "Identify if the attack is targeted (single account) or widespread (multiple accounts)",
                "Check source IPs against AbuseIPDB -- known scanner or botnet?",
                "Review MFA logs: was MFA prompted? Was it bypassed or fatigue-attacked?",
            ]),
            ("IOC ENRICHMENT", [
                "Submit attacking IPs to AbuseIPDB",
                "Check if usernames match a known breach list (if tooling permits)",
                "Search SIEM for same source IPs across other services",
                "Check for impossible travel or session anomalies on any successful logins",
            ]),
            ("CONTAINMENT", [
                "Block source IPs at firewall/WAF/VPN gateway",
                "Lock or temporarily disable targeted account(s) if at risk",
                "Force password reset on any accounts with successful logins during attack window",
                "Revoke active sessions for affected accounts",
                "Enforce MFA if not already in place on targeted service",
            ]),
            ("ESCALATION CHECK", [
                "Any successful logins during the attack window? → Escalate to L2",
                "MFA bypassed or push fatigue attack confirmed? → Escalate to L2",
                "Targeting privileged or admin accounts? → Escalate to L2",
                "Attack pattern suggests coordinated campaign? → Escalate to L2",
            ]),
            ("CLOSURE", [
                "Confirm source IPs are blocked and no further attempts are occurring",
                "Confirm affected accounts are secured and sessions revoked",
                "Document attack timeline, source IPs, and targeted accounts",
                "Recommend account lockout policy review if thresholds allowed excessive attempts",
                "Note whether geo-blocking or conditional access rules should be tightened",
            ]),
        ],
        "Unauthorised Access": [
            ("TRIAGE", [
                "Identify which system, application, or data was accessed without authorisation",
                "Identify the account used -- internal, external, service account, or unknown",
                "Determine whether access was accidental, insider threat, or external compromise",
                "Establish the timeframe of the unauthorised access",
            ]),
            ("INVESTIGATION", [
                "Pull access logs for the affected system for the full suspected window",
                "Identify what data or resources were accessed, modified, or exfiltrated",
                "Review authentication logs: how was access obtained? VPN, direct, web, API?",
                "Check if the account was compromised (concurrent sessions, unusual location/time)",
                "Review privilege logs: was privilege escalation used to gain access?",
            ]),
            ("IOC ENRICHMENT", [
                "Check source IPs used against AbuseIPDB and geo lookup",
                "Search SIEM for the account's activity across all systems in the window",
                "Check for data staging, compression, or large file transfers",
                "Review DLP alerts if available for the timeframe",
            ]),
            ("CONTAINMENT", [
                "Disable the compromised account immediately",
                "Revoke all active sessions and tokens",
                "Block source IPs if external access was used",
                "Preserve all relevant logs before any rotation or deletion occurs",
                "Notify system/data owner of the unauthorised access",
            ]),
            ("ESCALATION CHECK", [
                "Sensitive, personal, or regulated data was accessed? → Escalate to L2 / DPO",
                "Insider threat indicators? → Escalate to L2 / HR / Legal",
                "Evidence of data exfiltration? → Escalate to L2 / IR immediately",
                "Privileged or admin account involved? → Escalate to L2",
            ]),
            ("CLOSURE", [
                "Confirm account is secured and access revoked",
                "Document exactly what was accessed and whether data was exfiltrated",
                "Assess whether a data breach notification is required (GDPR / regulatory)",
                "Review access controls -- was least privilege in place?",
                "Document timeline and all evidence in the ticket",
            ]),
        ],
        "Data Exfiltration": [
            ("TRIAGE", [
                "Identify the source of the alert: DLP, CASB, SIEM rule, user report, or network anomaly",
                "Identify the user or system responsible for the transfer",
                "Determine what data was transferred and the approximate volume",
                "Identify the destination: external email, USB, cloud storage, remote IP, etc.",
            ]),
            ("INVESTIGATION", [
                "Pull full transfer logs for the suspected window -- confirm volume and destination",
                "Classify the data: is it sensitive, personal, regulated, or classified?",
                "Review if the transfer method was authorised (business justification?)",
                "Check for staging behaviour: large file creation, compression, or renaming before transfer",
                "Review user's recent activity for other anomalies or policy violations",
                "Check if other users or systems have transferred data to the same destination",
            ]),
            ("IOC ENRICHMENT", [
                "Look up destination IPs/domains -- known file sharing, personal cloud, or C2?",
                "Check if destination is a known data broker or exfiltration service",
                "Search SIEM for other transfers to the same destination across all users",
                "Cross-reference with any concurrent phishing or malware incidents",
            ]),
            ("CONTAINMENT", [
                "Block the destination IP/domain at proxy/firewall",
                "Suspend or disable the account responsible if compromise or malicious intent is suspected",
                "Revoke sessions and tokens for the account",
                "Preserve all logs and evidence immediately -- do not allow log rotation",
                "Notify data/system owner and escalate to management if sensitive data is involved",
            ]),
            ("ESCALATION CHECK", [
                "Personal data (PII) confirmed exfiltrated? → Escalate to DPO -- potential GDPR breach",
                "Volume or sensitivity suggests intentional exfiltration? → Escalate to L2 / Legal / HR",
                "Malware or external attacker involved? → Escalate to L2 / IR immediately",
                "Regulated data (financial, healthcare)? → Escalate and initiate breach protocol",
            ]),
            ("CLOSURE", [
                "Confirm exfiltration vector is blocked",
                "Document exactly what data was exfiltrated, volume, destination, and timeline",
                "Confirm whether regulatory breach notification is required and to whom",
                "Recommend DLP rule tuning if detection was delayed",
                "Document the full incident timeline and all evidence in the ticket",
            ]),
        ],
        "Ransomware": [
            ("TRIAGE -- ACT FAST", [
                "Confirm ransomware activity: encrypted files, ransom note, or EDR/AV alert",
                "Identify affected host(s): hostname, IP, OS, owner, department",
                "IMMEDIATELY notify L2 / IR lead -- ransomware is a P1 incident",
                "Do NOT reboot or power off hosts without L2 instruction -- this may destroy evidence",
            ]),
            ("IMMEDIATE CONTAINMENT", [
                "Isolate ALL affected hosts from the network immediately (network isolation, not shutdown)",
                "Identify and isolate any hosts showing similar IOCs proactively",
                "Disable the affected user account(s) immediately",
                "Notify IT infrastructure team to suspend backups temporarily (to prevent backup encryption)",
                "Check whether backups are already affected -- this is critical",
            ]),
            ("EVIDENCE COLLECTION", [
                "Capture ransom note contents and file paths",
                "Identify the ransomware family if possible (via EDR, hash lookup, or note format)",
                "Pull process tree and execution chain from EDR",
                "Capture network connections made by the ransomware process",
                "Check for lateral movement: which other systems did the infected host connect to?",
                "Identify initial infection vector: phishing email, RDP exposure, vulnerable service?",
            ]),
            ("IOC ENRICHMENT", [
                "Submit ransomware hash to VirusTotal -- identify family and known C2",
                "Check C2 IPs/domains against threat intel -- block immediately",
                "Search SIEM for same hash, C2, or execution pattern across all endpoints",
                "Check ID Ransomware (https://id-ransomware.malwarehunterteam.com) for family identification",
            ]),
            ("ESCALATION -- MANDATORY", [
                "Escalate to L2 / IR team immediately if not already done",
                "Notify CISO / management -- this is a major incident",
                "Engage legal if data exfiltration is suspected (double extortion)",
                "If regulated data is involved, initiate breach notification protocol",
                "Do not engage with threat actor or pay ransom without legal/management authorisation",
            ]),
            ("CLOSURE (POST-IR)", [
                "Confirm all affected systems are reimaged -- not just cleaned",
                "Verify backups are clean and restoration has been tested",
                "Confirm all IOCs are blocked at network and endpoint level",
                "Document full attack chain, timeline, and impact in the ticket",
                "Conduct post-incident review -- how did ransomware execute and persist?",
            ]),
        ],
        "Other / Unknown": [
            ("TRIAGE", [
                "Describe the alert or suspicious activity clearly in the ticket",
                "Identify affected users, systems, or services",
                "Determine detection source: automated alert, user report, or proactive hunt",
                "Assess urgency: is there active, ongoing malicious activity?",
            ]),
            ("INVESTIGATION", [
                "Collect relevant logs for the suspected timeframe",
                "Identify any IOCs: IPs, domains, hashes, email addresses, file paths",
                "Search SIEM for related activity across other users or systems",
                "Determine whether this matches a known TTP or attack pattern",
            ]),
            ("IOC ENRICHMENT", [
                "Check any identified IPs against AbuseIPDB",
                "Submit any hashes to VirusTotal",
                "Check domains for age, reputation, and passive DNS history",
                "Search for the activity pattern in threat intel sources",
            ]),
            ("CONTAINMENT", [
                "Block any confirmed malicious IPs or domains",
                "Isolate any affected endpoints if active compromise is suspected",
                "Disable accounts if credential compromise is suspected",
                "Preserve all logs and evidence",
            ]),
            ("ESCALATION CHECK", [
                "Unable to determine scope or root cause? → Escalate to L2",
                "Active, ongoing threat activity? → Escalate to L2 immediately",
                "Sensitive data potentially involved? → Escalate to L2",
                "Incident type matches a P1 category (ransomware, mass data loss)? → Escalate immediately",
            ]),
            ("CLOSURE", [
                "Document all investigation steps taken and findings",
                "Record all IOCs in the ticket",
                "Confirm containment actions are in place",
                "Note any unresolved questions or recommended follow-up actions",
                "Update incident type classification if root cause was identified",
            ]),
        ],

        "Rare and Potentially High-Risk Office Operations": [
            ("TRIAGE", [
                "Identify the user account and specific Office operation flagged (e.g. eDiscovery export, mailbox delegation, audit log clearing, admin role assignment)",
                "Determine whether this is a first-time or rare operation for this user",
                "Confirm whether the operation was performed interactively or via an app/service principal",
                "Check whether the operation was performed from a known trusted IP, location, and device",
            ]),
            ("INVESTIGATION", [
                "Pull the full Unified Audit Log (UAL) entry — note ClientIP, UserAgent, and ResultStatus",
                "Review the user's UAL activity for the past 7 days for other anomalous operations",
                "Check sign-in logs: unusual location, IP, device, or time",
                "Verify whether MFA was satisfied for the session that performed the operation",
                "Identify what the operation acted on: which mailbox, site, or tenant setting was affected",
                "If mailbox delegation or forwarding was set: identify the recipient and verify legitimacy",
                "If eDiscovery was run: identify the scope and whether results were exported",
                "If audit logging was modified or cleared: treat as high severity and escalate immediately",
                "Check for concurrent alerts: impossible travel, suspicious sign-in, MFA bypass",
            ]),
            ("IOC ENRICHMENT", [
                "Check the source IP against AbuseIPDB and threat intel feeds",
                "Check the UserAgent string for anomalies (automation tools, unusual browsers)",
                "If a service principal performed the operation: review its permissions and recent activity",
                "Search SIEM for same operation performed by other accounts in the same window",
            ]),
            ("CONTAINMENT", [
                "If unauthorised: disable the account and revoke all active sessions and tokens",
                "Reverse the operation where possible (remove delegation, remove forwarding rule, restore audit settings)",
                "If data was exported via eDiscovery: notify the DPO and begin data breach assessment",
                "If admin role was assigned: remove the role immediately and audit what the new admin did",
                "Block the source IP at the network/conditional access layer if external and suspicious",
            ]),
            ("ESCALATION CHECK", [
                "Audit log cleared or disabled? → Escalate to L2 immediately",
                "eDiscovery export completed with sensitive data? → Escalate to L2 / DPO",
                "Admin role granted to unexpected account? → Escalate to L2 / CISO",
                "Account confirmed compromised? → Escalate to L2 / Identity team",
                "Multiple rare operations in same session? → Escalate to L2",
            ]),
            ("CLOSURE", [
                "Confirm the unauthorised operation has been reversed or remediated",
                "Confirm account is secured: password reset, MFA re-enrolled, sessions revoked",
                "Document the operation, resource affected, source IP, and timeline",
                "If data exposure occurred: complete formal data breach assessment",
            ]),
        ],
        "Mass Cloud Resource Deletions Time Series Anomaly": [
            ("TRIAGE", [
                "Identify the Azure subscription(s), resource group(s), and account(s) involved",
                "Determine the volume and type of resources deleted — VMs, storage, databases, networking?",
                "Establish the timeframe and whether deletions are ongoing",
                "Check whether this is a known maintenance activity or completely unexpected",
                "Identify whether deletion was performed by a human user, service principal, or automation",
            ]),
            ("INVESTIGATION", [
                "Pull Azure Activity Log entries for all delete operations — note Caller, CallerIpAddress, OperationName, ResourceId",
                "Review the calling account's sign-in history: unusual location, IP, device, or time",
                "Check whether the account is a service principal — review permissions and recent credential changes",
                "Check whether resource locks were bypassed or removed before deletion",
                "Review whether backups, snapshots, or soft-delete protections exist for deleted resources",
                "Search for other anomalous Azure management operations from the same account",
                "Identify business impact: which services or workloads have been taken offline?",
            ]),
            ("IOC ENRICHMENT", [
                "Check the calling IP against AbuseIPDB and Azure known safe IP ranges",
                "If a service principal: check for recent credential rotation or new client secrets",
                "Search SIEM for other bulk management operations from the same Caller in the past 7 days",
            ]),
            ("CONTAINMENT", [
                "If malicious: disable the calling account or service principal immediately",
                "Revoke all active sessions and OAuth tokens for the account",
                "Apply Azure subscription-level resource locks to prevent further deletions",
                "Initiate recovery of deleted resources via Recovery Vault, soft-delete, or snapshots",
                "Notify resource owners and business stakeholders of the impact",
            ]),
            ("ESCALATION CHECK", [
                "Backups or DR resources deleted? → Escalate to L2 / CISO — potential ransomware",
                "Production services offline? → Escalate to L2 / CISO and initiate BCP",
                "Service principal or admin account confirmed compromised? → Escalate to L2",
                "Multiple subscriptions affected? → Escalate to L2 / CISO immediately",
            ]),
            ("CLOSURE", [
                "Confirm the calling account/service principal is secured",
                "Document all deleted resources, business impact, and recovery status",
                "Confirm resource locks are in place on critical subscriptions",
                "Complete root cause analysis: how did the actor gain delete permissions?",
                "Recommend Azure RBAC review and principle of least privilege audit",
            ]),
        ],
        "Anomalous Remote Access Tool Usage": [
            ("TRIAGE", [
                "Identify the host, user, and specific remote access tool flagged (AnyDesk, TeamViewer, ngrok, RustDesk, ScreenConnect, Cobalt Strike)",
                "Determine whether this tool is sanctioned and used legitimately",
                "Check whether the tool was pre-installed, freshly dropped, or installed by a process",
                "Identify the parent process that installed or launched the tool",
                "Confirm whether an outbound connection was established and to which IP/domain",
            ]),
            ("INVESTIGATION", [
                "Pull process creation events — note full path, hash, parent process, and command-line",
                "Review the tool's network connections: destination IP, port, and protocol",
                "Check installation directory — legitimate tools use Program Files; malicious often use temp/AppData",
                "Submit the file hash to VirusTotal",
                "Check the destination IP/domain against AbuseIPDB and threat intel",
                "Review the host's full process timeline for signs of prior compromise",
                "Check for persistence: startup, scheduled tasks, or services",
                "Review whether the session resulted in interactive activity: file access, command execution",
                "Search SIEM for the same tool binary hash or C2 IP/domain across other endpoints",
                "If ngrok or similar: identify what service was being exposed externally",
            ]),
            ("CONTAINMENT", [
                "Isolate the host if an active RAT session is confirmed or suspected",
                "Terminate the RAT process if still running",
                "Block the destination IP and domain at firewall and proxy",
                "Remove persistence mechanisms",
                "Disable the affected user account and revoke active sessions",
                "Quarantine and hash-block the RAT binary",
            ]),
            ("ESCALATION CHECK", [
                "Confirmed active C2 session? → Escalate to L2 / IR immediately",
                "Tool installed by malware dropper or phishing? → Escalate to L2",
                "Multiple hosts running the same RAT? → Escalate to L2 / IR",
                "ngrok or tunnel exposing internal services? → Escalate to L2 immediately",
            ]),
            ("CLOSURE", [
                "Confirm host is isolated, tool removed, and persistence cleared",
                "Confirm all C2 infrastructure is blocked at network level",
                "Document binary hash, C2 IP/domain, persistence mechanism, and process chain",
                "Recommend EDR policy to block unsanctioned remote access tools",
            ]),
        ],
        "Time Series Anomaly for Data Size Transferred to Public Internet": [
            ("TRIAGE", [
                "Identify the source host, user, and destination responsible for the anomalous transfer",
                "Determine the volume and how it compares to baseline — 2x, 10x, or 100x normal?",
                "Identify the protocol and application: HTTPS, FTP, cloud sync client?",
                "Check whether this was during or outside business hours",
                "Check whether this matches any known backup, update, or legitimate business activity",
            ]),
            ("INVESTIGATION", [
                "Pull firewall/proxy logs for source host and destination — bytes transferred, duration, protocol",
                "Identify the process responsible for the outbound traffic on the host",
                "Review the destination: personal cloud storage, file sharing site, or unknown IP?",
                "Check DLP alerts for the same timeframe on the same host or user",
                "Review host process timeline: was a staging or archiving tool used (7zip, WinRAR)?",
                "Check whether large files were recently created on the host before the transfer",
                "Review the user's recent access to sensitive file shares or databases",
                "Search SIEM for the same destination IP/domain from other hosts",
            ]),
            ("IOC ENRICHMENT", [
                "Check the destination IP against AbuseIPDB and threat intel",
                "Check the destination domain against VirusTotal and WHOIS for age/registration",
                "Search SIEM for other anomalous outbound transfers from the same host or user",
            ]),
            ("CONTAINMENT", [
                "Block the destination IP and domain at proxy/firewall if malicious or unauthorised",
                "Isolate the host if active exfiltration is ongoing or malware is confirmed",
                "Disable the user account if compromise or insider threat is suspected",
                "Preserve all relevant logs before any rotation occurs",
            ]),
            ("ESCALATION CHECK", [
                "Sensitive or regulated data confirmed in transfer? → Escalate to L2 / DPO — potential breach",
                "Deliberate staging and exfiltration by insider? → Escalate to L2 / HR / Legal",
                "Malware confirmed responsible? → Escalate to L2 / IR",
                "Multiple hosts transferring to same external destination? → Escalate to L2 / IR",
            ]),
            ("CLOSURE", [
                "Confirm exfiltration has stopped and destination is blocked",
                "Document volume, destination, responsible process, and data classification",
                "Assess whether formal breach notification is required under GDPR",
                "Recommend DLP policy review to detect and block this type of transfer earlier",
            ]),
        ],
        "Email Messages Removed After Delivery": [
            ("TRIAGE", [
                "Identify who or what removed the emails: user self-deletion, admin purge, ZAP, or inbox rule",
                "Identify the emails removed: sender, subject, attachment, number of mailboxes affected",
                "Determine the timeframe between delivery and removal",
                "If ZAP: confirm which threat type triggered the recall (malware, phish, spam)",
                "If inbox rule or user action: treat as suspicious and investigate further",
            ]),
            ("INVESTIGATION", [
                "Pull Unified Audit Log for RemoveMalware, HardDelete, SoftDelete, or MoveToDeletedItems operations",
                "If ZAP triggered: review the ZAP report in Defender portal for the full threat verdict",
                "If an inbox rule removed the emails: pull rule details — name, conditions, action, and when created",
                "Identify all mailboxes from which the email was removed",
                "Check whether any users interacted with the email before removal: links clicked, attachments opened",
                "For any users who interacted: review their endpoint activity in MDE",
                "Review sender reputation, SPF/DKIM/DMARC, and sending IP",
                "Check Threat Explorer for the full campaign scope",
                "If inbox rule deletion: check for other suspicious inbox rules (forwarding, deletion by keyword)",
            ]),
            ("IOC ENRICHMENT", [
                "Submit URLs from the removed email to VirusTotal / URLScan.io",
                "Submit attachment hashes to VirusTotal",
                "Check sender IP and domain against AbuseIPDB",
                "Search SIEM for the same sender, subject, or attachment hash across other users",
            ]),
            ("CONTAINMENT", [
                "Purge any remaining copies of the email via MDO Content Search",
                "Block sender address, sending IP, and malicious URLs or hashes at the email gateway",
                "If users clicked links or opened attachments: isolate affected endpoints",
                "If inbox rule is responsible: delete the rule and check for account compromise",
                "If account compromise suspected: reset password, revoke sessions, re-enrol MFA",
            ]),
            ("ESCALATION CHECK", [
                "Users confirmed to have clicked links or opened malicious attachments? → Escalate to L2 / IR",
                "Inbox rule created by attacker to auto-delete emails? → Escalate to L2 — active compromise",
                "Large-scale campaign targeting multiple users? → Escalate to L2",
                "Malware delivered and executed before ZAP removed the email? → Escalate to L2 / IR",
            ]),
            ("CLOSURE", [
                "Confirm all copies of the email are removed across the tenant",
                "Confirm all IOCs are blocked at the email gateway",
                "Confirm affected endpoints are remediated if any interaction occurred",
                "Document campaign scope, threat verdict, removal method, and user interaction",
                "Review Defender for Office 365 policies to ensure ZAP is enabled",
            ]),
        ],
        "TI Map Domain Entity to DeviceNetworkEvents": [
            ("TRIAGE", [
                "Identify the device, user, and process responsible for the DNS resolution or connection to the TI-matched domain",
                "Note the threat intelligence classification: C2, malware distribution, phishing, botnet, cryptomining",
                "Determine whether the connection was blocked or allowed through",
                "Establish when the connection occurred and whether it is ongoing",
                "Check if the device is a server, workstation, or shared system",
            ]),
            ("INVESTIGATION", [
                "Pull DeviceNetworkEvents from MDE Advanced Hunting — note RemoteUrl, RemoteIP, RemotePort, InitiatingProcessFileName",
                "Identify the initiating process: what application resolved or connected to the domain?",
                "Check whether the domain resolved successfully and whether a full session was established",
                "Review the initiating process's parent process chain",
                "Check the process binary hash against VirusTotal",
                "Search DeviceNetworkEvents across the estate for other devices contacting the same domain",
                "Check for file downloads from the domain correlated with the same process/timeframe",
                "Check DNS query logs for historical lookups to the domain from the device",
                "Assess whether this is a beaconing pattern: regular intervals, consistent byte sizes",
            ]),
            ("IOC ENRICHMENT", [
                "Check the domain and resolved IP against VirusTotal, AbuseIPDB, and URLScan.io",
                "Check WHOIS for domain registration age and registrar",
                "Check passive DNS records: does this domain resolve to known malicious infrastructure?",
                "Search threat intel for the domain for actor attribution",
                "Check Shodan for the resolved IP",
            ]),
            ("CONTAINMENT", [
                "Block the domain and resolved IP at DNS, proxy, and firewall immediately",
                "If C2 communication confirmed: isolate the device from the network",
                "Terminate the malicious process if still running",
                "Disable the user account if credential compromise is suspected",
                "Block the process binary hash at MDE if confirmed malicious",
            ]),
            ("ESCALATION CHECK", [
                "Confirmed C2 beacon to known threat actor infrastructure? → Escalate to L2 / IR immediately",
                "File download from domain confirmed? → Escalate to L2",
                "Multiple devices beaconing to same domain? → Escalate to L2 / IR",
                "Domain linked to known ransomware or APT actor? → Escalate to L2 / CISO immediately",
            ]),
            ("CLOSURE", [
                "Confirm domain and IP are blocked across all enforcement points",
                "Confirm device is remediated or reimaged if compromise was confirmed",
                "Document initiating process, domain, resolved IP, connection details, and TI classification",
                "Update the SIEM TI feed with the new IOC if not already present",
            ]),
        ],
        "Rare Subscription-Level Operations in Azure": [
            ("TRIAGE", [
                "Identify the specific Azure operation flagged: policy assignment, role assignment, diagnostic setting, key vault access policy?",
                "Identify the caller account or service principal and confirm whether this is expected",
                "Check whether the operation was from a known trusted IP and location",
                "Determine whether a change request exists that authorises this activity",
                "Note the subscription and resource scope — tenant-wide changes are higher severity",
            ]),
            ("INVESTIGATION", [
                "Pull the full Azure Activity Log entry: Caller, CallerIpAddress, OperationName, ResourceId, SubscriptionId",
                "Review the caller account's sign-in history: unusual IP, location, device, or time",
                "Check whether MFA was satisfied for the session",
                "Review all Activity Log entries for the same caller in the past 7 days",
                "Identify the blast radius: what does this operation change, expose, or enable?",
                "If a role assignment: who was granted what role on which scope?",
                "If a diagnostic setting was modified: has security logging been impaired?",
                "If Key Vault access policy changed: what secrets/keys may now be accessible?",
                "If policy assignment changed: have security controls been weakened?",
            ]),
            ("IOC ENRICHMENT", [
                "Check the caller IP against AbuseIPDB — residential IP, VPN, Tor, or known attacker?",
                "If a service principal: review its permissions and recent credential changes",
                "Check Azure AD audit log for the caller: MFA bypass, conditional access failure, risky sign-in?",
            ]),
            ("CONTAINMENT", [
                "If unauthorised: disable the calling account or service principal immediately",
                "Revoke all active sessions and refresh tokens",
                "Reverse the operation where possible: remove role, restore policy, revert diagnostic setting",
                "Apply resource locks on critical subscriptions",
                "If Key Vault access was modified: rotate all secrets and keys that may have been accessed",
            ]),
            ("ESCALATION CHECK", [
                "Diagnostic settings deleted — security logging impaired? → Escalate to L2 immediately",
                "Owner or Contributor role granted at subscription scope? → Escalate to L2 / CISO",
                "Key Vault access policy changed — secrets may be exposed? → Escalate to L2",
                "Security policies weakened? → Escalate to L2 / CISO",
                "Multiple anomalous operations in same session? → Escalate to L2",
            ]),
            ("CLOSURE", [
                "Confirm the operation has been reversed and account secured",
                "Document the operation type, resource scope, caller IP, and timeline",
                "Confirm Azure security logging is fully restored if impaired",
                "Complete an RBAC audit on the affected subscription",
                "Recommend implementing Azure PIM for just-in-time privileged access",
            ]),
        ],
        "Suspicious DNS Tunnel Behaviour Blocked": [
            ("TRIAGE", [
                "Identify the device, user, and process that generated the flagged DNS traffic",
                "Confirm the traffic was blocked and at which enforcement point",
                "Note the destination domain flagged for DNS tunnelling behaviour",
                "Determine whether this is a known tunnelling tool (iodine, dnscat2, DNSExfiltrator) or anomalous patterns",
                "Assess whether any data was successfully exfiltrated before blocking",
            ]),
            ("INVESTIGATION", [
                "Pull DNS query logs — look for: unusually long subdomain labels, high query frequency, TXT/NULL/MX queries with encoded data, base32/base64 encoded subdomains",
                "Identify the initiating process responsible for the DNS queries",
                "Submit the process binary hash to VirusTotal",
                "Review the process parent chain — spawned by malicious document, script, or lateral movement?",
                "Check the device's full process and network event timeline",
                "Assess query volume and pattern: is there a beaconing interval suggesting C2 over DNS?",
                "Check whether the same domain was queried historically before the block",
                "Search across all devices in SIEM for queries to the same domain",
            ]),
            ("IOC ENRICHMENT", [
                "Check the destination domain against VirusTotal, AbuseIPDB, and passive DNS",
                "Check WHOIS for domain registration — newly registered or bulletproof hosting?",
                "Identify the DNS server used — is the device using a custom external resolver to bypass filtering?",
                "Search threat intel for the domain — known threat actor or malware family?",
            ]),
            ("CONTAINMENT", [
                "Confirm the domain is blocked at all DNS enforcement points across the estate",
                "Isolate the affected device — DNS tunnelling with active C2 is a critical indicator",
                "Terminate the tunnelling process if still running",
                "Remove any persistence mechanisms identified",
                "Disable the user account if credential compromise is suspected",
                "Block the tunnelling tool binary hash at MDE",
            ]),
            ("ESCALATION CHECK", [
                "Data exfiltration via DNS confirmed or suspected? → Escalate to L2 / IR and DPO immediately",
                "Active C2 session established via DNS tunnel? → Escalate to L2 / IR immediately",
                "Known malware family identified as the tunnelling agent? → Escalate to L2 / IR",
                "Multiple devices using DNS tunnelling to same domain? → Escalate to L2 / IR",
            ]),
            ("CLOSURE", [
                "Confirm device is isolated and fully remediated or reimaged",
                "Confirm domain is blocked at all DNS enforcement points",
                "Document the tunnelling tool, domain, query patterns, and process chain",
                "Assess whether any data was successfully exfiltrated and initiate breach assessment if required",
                "Recommend DNS logging improvements (Sysmon DNS, PDNS)",
                "Recommend blocking custom DNS resolvers to prevent bypass of DNS filtering",
            ]),
        ],
    }

    def setup_training_wheels_panel(self):
        """Build the Training Wheels panel (hidden by default unless enabled)."""
        self.tw_frame = tk.Frame(self.root, relief=tk.RIDGE, bd=1)
        self.tw_form_mode = False  # False = checklist mode, True = form mode

        # ── Header row ──────────────────────────────────────────────────────
        header = tk.Frame(self.tw_frame)
        header.pack(fill="x", padx=6, pady=(4, 2))

        tk.Label(header, text="🎓 Training Wheels -- Incident Checklist",
                 font=("Consolas", 10, "bold")).pack(side="left")

        # Incident type selector — searchable Entry + popup Listbox
        tk.Label(header, text="  Type:").pack(side="left")
        self.tw_incident_var = tk.StringVar(value="Phishing")
        self._tw_popup = None
        self.tw_search_entry = tk.Entry(header, textvariable=self.tw_incident_var,
            font=("Consolas", 9), width=38)
        self.tw_search_entry.pack(side="left", padx=(2, 10))
        self.tw_search_entry.bind("<KeyRelease>", self._tw_on_search_key)
        self.tw_search_entry.bind("<FocusIn>", self._tw_show_popup)
        self.tw_search_entry.bind("<FocusOut>", lambda e: self.root.after(150, self._tw_hide_popup))
        self.tw_search_entry.bind("<Return>", self._tw_confirm_from_entry)
        self.tw_search_entry.bind("<Escape>", lambda e: self._tw_hide_popup())
        self.tw_search_entry.bind("<Down>", self._tw_focus_popup)

        # Progress label
        self.tw_progress_label = tk.Label(header, text="0 / 0 completed", font=("Consolas", 9))
        self.tw_progress_label.pack(side="left", padx=6)

        # Progress bar
        self.tw_progress_bar = ttk.Progressbar(header, length=160, mode="determinate")
        self.tw_progress_bar.pack(side="left", padx=4)

        # Right-side controls (built right-to-left so order reads left-to-right visually)
        tk.Button(header, text="↺ Reset", command=self._tw_reset,
                  font=("Consolas", 9), relief="flat", cursor="hand2").pack(side="right", padx=4)

        # Mode toggle button
        self.tw_mode_btn = tk.Button(
            header, text="📋 Form Mode", command=self._tw_toggle_mode,
            font=("Consolas", 9), relief="flat", cursor="hand2"
        )
        self.tw_mode_btn.pack(side="right", padx=4)

        # Insert and Copy buttons -- only meaningful in form mode, shown always
        self.tw_insert_btn = tk.Button(
            header, text="⬇ Insert Note", command=self._tw_insert_note,
            font=("Consolas", 9), relief="flat", cursor="hand2", state="disabled"
        )
        self.tw_insert_btn.pack(side="right", padx=2)

        self.tw_copy_btn = tk.Button(
            header, text="📄 Copy Note", command=self._tw_copy_note,
            font=("Consolas", 9), relief="flat", cursor="hand2", state="disabled"
        )
        self.tw_copy_btn.pack(side="right", padx=2)

        # ── Scrollable checklist area ────────────────────────────────────────
        list_container = tk.Frame(self.tw_frame)
        list_container.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        tw_canvas = tk.Canvas(list_container, height=160, highlightthickness=0)
        tw_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=tw_canvas.yview)
        self.tw_scroll_frame = tk.Frame(tw_canvas)

        self.tw_scroll_frame.bind(
            "<Configure>",
            lambda e: tw_canvas.configure(scrollregion=tw_canvas.bbox("all"))
        )
        tw_canvas.create_window((0, 0), window=self.tw_scroll_frame, anchor="nw")
        tw_canvas.configure(yscrollcommand=tw_scrollbar.set)

        tw_scrollbar.pack(side="right", fill="y")
        tw_canvas.pack(side="left", fill="both", expand=True)

        # Mouse-wheel scrolling -- works on the canvas AND all child widgets
        def _on_mousewheel(event):
            tw_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_mousewheel(child)

        tw_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.tw_scroll_frame.bind("<MouseWheel>", _on_mousewheel)
        self._tw_bind_mousewheel = lambda: _bind_mousewheel(self.tw_scroll_frame)

        self.tw_canvas = tw_canvas
        self.tw_check_vars = []
        self.tw_note_vars = {}   # {(section_name, item_text): StringVar} for form mode
        self._tw_load_checklist()

        # Show or hide based on saved setting
        if self.config.TRAINING_WHEELS:
            self.tw_frame.pack(fill="x", padx=5, pady=(0, 2))

    def _tw_show_popup(self, event=None):
        self._tw_hide_popup()
        query = self.tw_incident_var.get().strip().lower()
        all_types = list(self.TRAINING_CHECKLISTS.keys())
        matches = [t for t in all_types if query in t.lower()] if query else all_types
        if not matches:
            return
        x = self.tw_search_entry.winfo_rootx()
        y = self.tw_search_entry.winfo_rooty() + self.tw_search_entry.winfo_height()
        popup = tk.Toplevel(self.root)
        popup.wm_overrideredirect(True)
        popup.wm_geometry(f"+{x}+{y}")
        self._tw_popup = popup
        frame = tk.Frame(popup, bd=1, relief="solid")
        frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical")
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set,
            font=("Consolas", 9), activestyle="dotbox",
            width=52, height=min(14, len(matches)), exportselection=False)
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)
        for item in matches:
            listbox.insert(tk.END, item)
        def on_select(e):
            sel = listbox.curselection()
            if sel:
                self.tw_incident_var.set(listbox.get(sel[0]))
                self._tw_hide_popup()
                self._tw_load_checklist()
                self.tw_search_entry.focus_set()
        listbox.bind("<<ListboxSelect>>", on_select)
        listbox.bind("<Return>", on_select)
        listbox.bind("<Escape>", lambda e: self._tw_hide_popup())
        listbox.bind("<FocusOut>", lambda e: self.root.after(150, self._tw_hide_popup))
        self._tw_popup_listbox = listbox
        popup.lift()

    def _tw_hide_popup(self, event=None):
        if self._tw_popup and self._tw_popup.winfo_exists():
            try:
                self._tw_popup.destroy()
            except Exception:
                pass
        self._tw_popup = None

    def _tw_on_search_key(self, event=None):
        if event and event.keysym in ("Return", "Escape", "Down", "Up"):
            return
        self._tw_show_popup()

    def _tw_focus_popup(self, event=None):
        if self._tw_popup and self._tw_popup.winfo_exists():
            try:
                self._tw_popup_listbox.focus_set()
                if self._tw_popup_listbox.size() > 0:
                    self._tw_popup_listbox.selection_set(0)
                    self._tw_popup_listbox.activate(0)
            except Exception:
                pass

    def _tw_confirm_from_entry(self, event=None):
        if self._tw_popup and self._tw_popup.winfo_exists():
            try:
                if self._tw_popup_listbox.size() == 1:
                    self.tw_incident_var.set(self._tw_popup_listbox.get(0))
                    self._tw_hide_popup()
                    self._tw_load_checklist()
                    return
            except Exception:
                pass
        self._tw_hide_popup()
        self._tw_load_checklist()

    def _tw_load_checklist(self, event=None):
        """Populate the checklist or form for the selected incident type."""
        for widget in self.tw_scroll_frame.winfo_children():
            widget.destroy()
        self.tw_check_vars = []
        # Preserve any note text already typed when switching incident type
        # (note vars are keyed by (section, item) so switching type naturally starts fresh)
        if not hasattr(self, 'tw_note_vars'):
            self.tw_note_vars = {}

        incident_type = self.tw_incident_var.get()
        sections = self.TRAINING_CHECKLISTS.get(incident_type, [])

        # Configure column weights so the entry column stretches
        self.tw_scroll_frame.columnconfigure(1, weight=1)

        row = 0
        for section_name, items in sections:
            # Section heading
            lbl = tk.Label(self.tw_scroll_frame,
                           text=f"  {section_name}",
                           font=("Consolas", 9, "bold"),
                           anchor="w", padx=4)
            lbl.grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 1))
            row += 1

            for item_text in items:
                if self.tw_form_mode:
                    # ── Form mode: label + entry box ────────────────────────
                    lbl_item = tk.Label(
                        self.tw_scroll_frame,
                        text=item_text,
                        font=("Consolas", 9),
                        anchor="w",
                        justify="left",
                        wraplength=340,
                    )
                    lbl_item.grid(row=row, column=0, sticky="w", padx=(16, 6), pady=2)

                    key = (incident_type, section_name, item_text)
                    if key not in self.tw_note_vars:
                        self.tw_note_vars[key] = tk.StringVar()
                    entry = tk.Entry(
                        self.tw_scroll_frame,
                        textvariable=self.tw_note_vars[key],
                        font=("Consolas", 9),
                        width=52,
                    )
                    entry.grid(row=row, column=1, sticky="ew", padx=(0, 8), pady=2)
                else:
                    # ── Checklist mode: checkbox only ────────────────────────
                    var = tk.BooleanVar(value=False)
                    self.tw_check_vars.append(var)
                    cb = tk.Checkbutton(
                        self.tw_scroll_frame,
                        text=item_text,
                        variable=var,
                        font=("Consolas", 9),
                        anchor="w",
                        justify="left",
                        wraplength=900,
                        command=self._tw_update_progress,
                        cursor="hand2",
                    )
                    cb.grid(row=row, column=0, columnspan=2, sticky="w", padx=(16, 4), pady=1)

                row += 1

        self._tw_update_progress()

        # Rebind mousewheel to all newly created widgets
        if hasattr(self, '_tw_bind_mousewheel'):
            self._tw_bind_mousewheel()

        # Apply dark theme to new widgets if dark mode is active
        if self.config.DARK_MODE:
            self.apply_dark_theme_to_widgets(self.tw_scroll_frame)

    def _tw_update_progress(self):
        """Update progress bar and label. In form mode shows fields filled."""
        if self.tw_form_mode:
            incident_type = self.tw_incident_var.get()
            sections = self.TRAINING_CHECKLISTS.get(incident_type, [])
            total = sum(len(items) for _, items in sections)
            done = sum(
                1 for _, section_name, item_text in self.tw_note_vars
                if self.tw_note_vars.get((incident_type, section_name, item_text), tk.StringVar()).get().strip()
            )
            # Recount properly using the actual stored vars for this incident type
            done = sum(
                1 for (itype, sname, itext), var in self.tw_note_vars.items()
                if itype == incident_type and var.get().strip()
            )
            self.tw_progress_label.config(text=f"{done} / {total} fields filled")
        else:
            total = len(self.tw_check_vars)
            done = sum(1 for v in self.tw_check_vars if v.get())
            self.tw_progress_label.config(text=f"{done} / {total} completed")
        if total > 0:
            self.tw_progress_bar["value"] = (done / total) * 100
        else:
            self.tw_progress_bar["value"] = 0

    def _tw_reset(self):
        """Reset checkboxes (checklist mode) or clear all note fields (form mode)."""
        if self.tw_form_mode:
            incident_type = self.tw_incident_var.get()
            for (itype, sname, itext), var in self.tw_note_vars.items():
                if itype == incident_type:
                    var.set("")
        else:
            for var in self.tw_check_vars:
                var.set(False)
        self._tw_update_progress()

    def _tw_toggle_mode(self):
        """Switch between checklist mode and form mode."""
        self.tw_form_mode = not self.tw_form_mode
        if self.tw_form_mode:
            self.tw_mode_btn.config(text="☑ Checklist Mode")
            self.tw_copy_btn.config(state="normal")
            self.tw_insert_btn.config(state="normal")
            self.tw_canvas.config(height=200)
        else:
            self.tw_mode_btn.config(text="📋 Form Mode")
            self.tw_copy_btn.config(state="disabled")
            self.tw_insert_btn.config(state="disabled")
            self.tw_canvas.config(height=160)
        self._tw_load_checklist()

    def _tw_build_note(self):
        """Build a formatted ticket-style note from the filled form fields."""
        incident_type = self.tw_incident_var.get()
        sections = self.TRAINING_CHECKLISTS.get(incident_type, [])
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = []
        lines.append("=" * 60)
        lines.append(f"  INCIDENT NOTE -- {incident_type.upper()}")
        lines.append(f"  Generated: {now}")
        lines.append("=" * 60)
        lines.append("")

        has_content = False
        for section_name, items in sections:
            section_lines = []
            for item_text in items:
                key = (incident_type, section_name, item_text)
                value = self.tw_note_vars.get(key, tk.StringVar()).get().strip()
                if value:
                    section_lines.append(f"  [{item_text}]")
                    section_lines.append(f"  {value}")
                    section_lines.append("")
                    has_content = True

            if section_lines:
                lines.append(f"── {section_name} " + "─" * max(0, 54 - len(section_name)))
                lines.extend(section_lines)

        if not has_content:
            return None

        lines.append("=" * 60)
        return "\n".join(lines)

    def _tw_copy_note(self):
        """Copy the formatted note to clipboard."""
        note = self._tw_build_note()
        if not note:
            self.update_status("Nothing to copy -- fill in at least one field first")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(note)
        self.update_status("Incident note copied to clipboard")

    def _tw_insert_note(self):
        """Insert the formatted note into the active tab at the cursor position."""
        note = self._tw_build_note()
        if not note:
            self.update_status("Nothing to insert -- fill in at least one field first")
            return
        current = self.notebook.select()
        if not current:
            self.update_status("No active tab to insert into")
            return
        current_frame = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(current_frame)
        text_widget.insert('insert', "\n" + note + "\n")
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)
        self.update_status("Incident note inserted into active tab")

    def toggle_training_wheels(self):
        """Toggle the Training Wheels panel on/off."""
        self.config.TRAINING_WHEELS = self.training_wheels_var.get()
        if self.config.TRAINING_WHEELS:
            self.tw_frame.pack(fill="x", padx=5, pady=(0, 2), before=self.notebook)
        else:
            self.tw_frame.pack_forget()
        self.save_settings()
        status = "enabled" if self.config.TRAINING_WHEELS else "disabled"
        self.update_status(f"Training Wheels {status}")

    # --------------------- Welcome Tab ---------------------
    def new_welcome_tab(self):
        """Create the welcome / README tab with ThreatPad ASCII logo."""
        WELCOME_CONTENT = (

            "  ████████╗ ██╗  ██╗ ██████╗  ███████╗  █████╗  ███████╗ ██████╗   █████╗  ██████╗ \n"
            "  ╚══██╔══╝ ██║  ██║ ██╔══██╗ ██╔════╝ ██╔══██╗ ╚══██╔══╝ ██╔══██╗ ██╔══██╗ ██╔══██╗\n"
            "     ██║    ███████║ ██████╔╝ █████╗   ███████║    ██║    ██████╔╝ ███████║ ██║  ██║\n"
            "     ██║    ██╔══██║ ██╔══██╗ ██╔══╝   ██╔══██║    ██║    ██╔══╝  ██╔══██║ ██║  ██║\n"
            "     ██║    ██║  ██║ ██║  ██║ ███████╗ ██║  ██║    ██║    ██║      ██║  ██║ ██████╔╝\n"
            "     ╚═╝    ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚══════╝ ╚═╝  ╚═╝    ╚═╝    ╚═╝      ╚═╝  ╚═╝ ╚═════╝ \n"
            "                         SOC Incident Notes  ─  v3\n"
            "\n"
            "  ═══════════════════════════════════════════════════════════════════════════════\n"
            "\n"
            "  QUICK START\n"
            "  ───────────\n"
            "  • New tab          Ctrl+N        • Defang IOCs       Ctrl+D\n"
            "  • Open file        Ctrl+O        • Refang IOCs       Ctrl+R\n"
            "  • Save             Ctrl+S        • Extract IOCs      Ctrl+I\n"
            "  • Find             Ctrl+F        • Export IOCs       Ctrl+E\n"
            "  • Find & Replace   Ctrl+H        • Enrich IOCs       Ctrl+Shift+E\n"
            "  • Close tab        Ctrl+W        • Safe Copy         button →\n"
            "  • Undo / Redo      Ctrl+Z / Y\n"
            "\n"
            "  ASCII QUICK MENU  (keyboard-driven rapid workflow)\n"
            "  ──────────────────────────────────────────────────\n"
            "  Ctrl+`  Open the Quick Menu (3-level keyboard navigator)\n"
            "  Ctrl+1  Defang current tab → copy to clipboard → save to history → reopen menu\n"
            "  Ctrl+2  Copy current note into a new Escalation Note tab\n"
            "  Ctrl+3  Close the current tab\n"
            "\n"
            "  Quick Menu levels:\n"
            "    1. Action      N=New Incident  O=Open Incident  P=Phone Call  M=Meeting Notes\n"
            "    2. Template    Pick from your Templates list, or [0] to skip (blank note)\n"
            "    3. Client      Pick from your Clients list, or [0] to skip (no client)\n"
            "  Choosing a client automatically selects it in the toolbar dropdown.\n"
            "  Templates and client names sync live from Settings — no restart needed.\n"
            "\n"
            "  TABS\n"
            "  ────\n"
            "  Each tab has an × close button. Middle-click also closes a tab.\n"
            "  Selecting a Template opens it in a new tab automatically.\n"
            "  Session is restored on next launch.\n"
            "\n"
            "  CLIENT SELECTOR & CROSS-CONTAMINATION DETECTION\n"
            "  ─────────────────────────────────────────────────\n"
            "  Select the active client from the Client: dropdown in the toolbar.\n"
            "  Register clients in Tools → Settings → Clients with their identifiers:\n"
            "    • Email domains       e.g.  lidl.com\n"
            "    • Hostname prefixes   e.g.  LIDL-WS\n"
            "    • IP ranges           e.g.  10.1.0.0/16\n"
            "    • Custom keywords     e.g.  LidlRetail\n"
            "  Press ⚠ Check to run a full scan. Contaminated text is highlighted red.\n"
            "  Safe Copy automatically blocks copying if contamination is detected.\n"
            "  Passive scanning also warns in the status bar as you type.\n"
            "\n"
            "  SAFE COPY\n"
            "  ─────────\n"
            "  Safe Copy runs three checks before copying your note:\n"
            "    1. Copy-Count    — warns if the same note has already been copied.\n"
            "    2. Contamination — BLOCKS copy if another client\'s data is present.\n"
            "    3. Defang check  — warns if live undefanged IOCs remain in the note.\n"
            "  Copy-Clear and Copy-Count can be toggled in Tools → Settings → General.\n"
            "\n"
            "  TRAINING WHEELS MODE\n"
            "  ────────────────────\n"
            "  Toggle via View → Training Wheels Mode (persists across sessions).\n"
            "  Search or type in the incident type box to filter the dropdown.\n"
            "  Two modes:\n"
            "    Checklist mode  — tick off investigation steps as you work.\n"
            "    Form mode       — fill in answers, then Insert Note or Copy Note\n"
            "                      to produce a clean formatted incident note.\n"
            "  Drag the sash between the panel and editor to resize (form mode).\n"
            "  Checklists cover: Phishing, Malware, Brute Force, Ransomware,\n"
            "    Unauthorised Access, Data Exfiltration, and 8 specific Sentinel/\n"
            "    Defender incident types including DNS Tunnel, Mass Cloud Deletions,\n"
            "    TI Map Domain, Rare Office Operations, and more.\n"
            "  Customise all checklists in Tools → Settings → Training Wheels.\n"
            "\n"
            "  IOC DEFANGING\n"
            "  ─────────────\n"
            "  Defang converts live indicators into safe-to-share format:\n"
            "    http://evil.com   →   hxxp[://]evil[.]com\n"
            "    192.168.1.1       →   192[.]168[.]1[.]1\n"
            "    user@domain.com   →   user[@]domain[.]com\n"
            "    user@corp         →   user[@]corp  (no-TLD addresses also caught)\n"
            "    #anchor           →   [#]anchor\n"
            "  Syntax highlighting colours IOCs automatically (toggleable).\n"
            "  Highlighting is debounced — runs after you stop typing, not per keystroke.\n"
            "  Skipped on documents over 100KB to maintain performance.\n"
            "\n"
            "  TEMPLATES & COPY PASTA\n"
            "  ──────────────────────\n"
            "  Templates open in a new tab. Manage under Tools → Settings → Templates.\n"
            "  Copy Pasta snippets insert at cursor. Manage under Tools → Settings → Copy Pasta.\n"
            "  Both support {date}, {time}, {datetime} placeholders.\n"
            "  Templates are also used by the ASCII Quick Menu for new note content.\n"
            "\n"
            "  TOOLS\n"
            "  ─────\n"
            "  Hashing    — MD5, SHA1, SHA256 generation and hash type identification.\n"
            "  Encoding   — Base64 encode / decode.\n"
            "  Enrich IOCs — Lookup IPs/domains/hashes via VirusTotal and AbuseIPDB.\n"
            "               API keys configured in Tools → Settings → API Keys.\n"
            "\n"
            "  ═══════════════════════════════════════════════════════════════════════════════\n"
            "  NOTICE: Access to this system is restricted to authorised users for\n"
            "  business purposes. Send all suggestions to Jack Wise\n"
            "  ═══════════════════════════════════════════════════════════════════════════════\n"
        )

        frame = tk.Frame(self.notebook)
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        text_widget = tk.Text(
            frame, wrap="none", font=("Consolas", 10),
            state="normal", cursor="arrow", takefocus=0,
            yscrollcommand=vsb.set, xscrollcommand=hsb.set
        )
        vsb.config(command=text_widget.yview)
        hsb.config(command=text_widget.xview)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        text_widget.pack(fill="both", expand=True)

        # Insert content
        text_widget.insert("1.0", WELCOME_CONTENT)

        # Colour tags
        text_widget.tag_config("title",   foreground="#ff6b35", font=("Consolas", 10, "bold"))
        text_widget.tag_config("heading", foreground="#f0c040", font=("Consolas", 10, "bold"))
        text_widget.tag_config("notice",  foreground="#888888", font=("Consolas", 9, "italic"))

        # Title block -- first 7 lines are the THREATPAD block art
        text_widget.tag_add("title", "1.0", "8.0")

        # Section headings
        for heading in ("QUICK START", "TABS", "IOC DEFANGING",
                        "TEMPLATES & COPY PASTA", "TRAINING WHEELS MODE",
                        "CLIENT SELECTOR", "SAFE COPY", "TOOLS", "NOTICE:"):
            pos = "1.0"
            while True:
                found = text_widget.search(heading, pos, stopindex="end")
                if not found:
                    break
                line = found.split(".")[0]
                text_widget.tag_add("heading", f"{line}.0", f"{line}.end")
                pos = f"{found}+1c"

        # Notice lines
        for marker in ("NOTICE:", "business purposes.", "Send all suggestions"):
            pos = "1.0"
            while True:
                found = text_widget.search(marker, pos, stopindex="end")
                if not found:
                    break
                line = found.split(".")[0]
                text_widget.tag_add("notice", f"{line}.0", f"{line}.end")
                pos = f"{found}+1c"

        text_widget.config(state="disabled")
        self._theme_welcome_tab(text_widget, frame)

        self.notebook.add(frame, text=" \u2302  Welcome")
        welcome_tab_id = self.notebook.tabs()[-1]
        self._add_close_button(welcome_tab_id)
        self.notebook.select(frame)
        self.welcome_frame = frame
        self.welcome_text_widget = text_widget

    def _theme_welcome_tab(self, text_widget, frame):
        """Apply terminal-style dark background to the welcome tab."""
        bg = "#0d0d0d"
        fg = "#cccccc"
        text_widget.config(
            bg=bg, fg=fg, insertbackground=fg,
            selectbackground="#2a4a6a", selectforeground="#ffffff"
        )
        frame.config(bg=bg)

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
        
        self.notebook.add(frame, text=title)
        self.notebook.select(frame)
        self.tabs[frame] = text_frame
        self.current_file_paths[frame] = None

        # Add a real close button widget over this tab
        tab_id = self.notebook.tabs()[-1]
        self._add_close_button(tab_id)

        # Start incident timer for this tab
        from datetime import datetime as _dt2
        self._tab_timers[frame] = _dt2.now()
        if not self._timer_job:
            self._timer_job = self.root.after(1000, self._tick_timer)

        # Log action
        self._log_action('tab_opened', title)

        # Initial syntax highlighting
        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_frame.text)

    def close_tab(self, tab_id=None):
        current = tab_id or self.notebook.select()
        if not current:
            return

        current_frame = self.notebook.nametowidget(current)

        # Block close if tab is pinned
        if current_frame in self._pinned_tabs:
            messagebox.showinfo("Tab Pinned",
                "This tab is pinned. Right-click the tab and choose 'Unpin Tab' to close it.")
            return

        text_widget = self.get_text_widget(current_frame)
        tab_text = text_widget.get("1.0", "end-1c")

        if tab_text.strip():
            if not messagebox.askyesno("Confirm", "Close tab without saving?"):
                return

        # Save to recently-closed stack (max 15)
        title    = self.notebook.tab(current, "text")
        filepath = self.current_file_paths.get(current)
        self._closed_tabs.append((title, tab_text, filepath))
        self._closed_tabs = self._closed_tabs[-15:]

        if current_frame in self.tabs:
            del self.tabs[current_frame]
        if current in self.current_file_paths:
            del self.current_file_paths[current]
        self._pinned_tabs.discard(current_frame)
        self._bookmarks.pop(current_frame, None)
        self.notebook.forget(current)

        if len(self.tabs) == 0:
            self.new_tab()

    def on_tab_changed(self, event):
        self.update_status("Tab changed")
        self._reposition_close_buttons()
        self._update_client_lock_ui()
        self.root.after(100, self._update_traffic_light)

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
            self.notebook.tab(current, text=os.path.basename(filepath))
            self._reposition_close_buttons()
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

        # Count items before defanging for the summary
        _url_count    = len(re.findall(r'https?://', text, re.IGNORECASE))
        _ip_count     = len(re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text))
        _email_count  = len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        _domain_count = len(re.findall(
            r'\b[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
            r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+\b', text))

        # Defang URLs first (to avoid double defanging)
        text = re.sub(r"https://", "hxxps[://]", text, flags=re.IGNORECASE)
        text = re.sub(r"http://", "hxxp[://]", text, flags=re.IGNORECASE)

        # Defang emails (must happen before domain/IP dot defanging)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        def defang_email(match):
            return match.group().replace('@', '[@]')
        text = re.sub(email_pattern, defang_email, text)
        # Pass 2: catch-all for any @ not yet defanged
        text = re.sub(r'(?<!\[)@(?!\])', '[@]', text)

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
        text = re.sub(r'@(?=\[#\])', '[@]', text)
        text = re.sub(r'(?<=\[#\])@', '[@]', text)

        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", text)

        if self.config.SYNTAX_HIGHLIGHTING:
            self.apply_syntax_highlighting(text_widget)

        self._mileage['defangs'] = self._mileage.get('defangs', 0) + 1
        self._log_action('defang', 'IOCs defanged')
        self.root.after(200, self._update_traffic_light)

        # Build a concise summary
        parts = []
        if _url_count:    parts.append(f"{_url_count} URL{'s' if _url_count>1 else ''}")
        if _ip_count:     parts.append(f"{_ip_count} IP{'s' if _ip_count>1 else ''}")
        if _email_count:  parts.append(f"{_email_count} email{'s' if _email_count>1 else ''}")
        if _domain_count: parts.append(f"{_domain_count} domain{'s' if _domain_count>1 else ''}")
        summary = "Defanged: " + ", ".join(parts) if parts else "Defanged (nothing found)"
        self.update_status(summary)

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
        self._mileage['iocs_extracted'] = self._mileage.get('iocs_extracted', 0) + 1
        self._log_action('ioc_extract', 'IOCs extracted')
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
                    window.after(0, lambda err=e: messagebox.showerror("Error", f"Enrichment failed: {err}"))
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
        if not text_widget:
            return
        text_widget.delete("1.0", "end")
        if current_frame in self._tab_copy_counts:
            self._tab_copy_counts[current_frame] = 0
        self.update_status("Text cleared")

    def safe_copy_text(self):
        current = self.notebook.select()
        if not current:
            return
        current_frame = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(current_frame)
        text = text_widget.get("1.0", "end-1c")
        if not text.strip():
            self.update_status("Nothing to copy")
            return
        # Surface any proactive mistake memory warnings
        warnings = self._analyse_mistake_patterns()
        if warnings:
            self.update_status(warnings[0][:90])
        # ── STEP 1: Copy-Count warning ──────────────────────────────
        if self.config.COPY_COUNT_WARN:
            count = self._tab_copy_counts.get(current_frame, 0)
            if count >= 1:
                if not messagebox.askyesno("Already Copied",
                    f"This note has already been copied {count} time(s).\n\n"
                    "This could mean you are copying the wrong note, or the same "
                    "note twice.\n\nCopy again anyway?"):
                    self.validation_label.config(text="Copy Cancelled", fg="red")
                    return

        # ── STEP 2: Cross-contamination check — must pass before anything else ──
        if self.active_client and self.clients:
            other_patterns = []
            for cname in self.clients:
                if cname != self.active_client:
                    other_patterns.extend(self._get_client_patterns(cname))
            if other_patterns:
                import re as _re2
                findings = []
                for pattern, label, client_name in other_patterns:
                    for match in pattern.finditer(text):
                        findings.append((match.group(), label, client_name))
                if findings:
                    # Build a short summary of what was found
                    summary_lines = []
                    seen = set()
                    for value, label, client_name in findings[:8]:
                        key = (value, client_name)
                        if key not in seen:
                            seen.add(key)
                            summary_lines.append(f"  \u2022 \"{value}\"  \u2192  {client_name} ({label})")
                    summary = "\n".join(summary_lines)
                    if len(findings) > 8:
                        summary += f"\n  ... and {len(findings) - 8} more match(es)"
                    self.validation_label.config(text="\u26a0 Contamination", fg="red")
                    messagebox.showerror(
                        "\u26a0 Cross-Client Contamination Detected — Copy Blocked",
                        f"This note contains data belonging to other clients.\n"
                        f"Active client: {self.active_client}\n\n"
                        f"Contaminated identifiers found:\n{summary}\n\n"
                        f"Copy has been blocked to prevent a data breach.\n"
                        f"Review and remove the highlighted content before copying."
                    )
                    # Highlight the contamination so the analyst can see exactly what to remove
                    import bisect as _bisect2
                    line_offsets = [0]
                    for i, ch in enumerate(text):
                        if ch == "\n":
                            line_offsets.append(i + 1)
                    def _oti(offset):
                        line = _bisect2.bisect_right(line_offsets, offset) - 1
                        col = offset - line_offsets[line]
                        return f"{line + 1}.{col}"
                    text_widget.tag_remove("contamination", "1.0", "end")
                    text_widget.tag_config("contamination", background="#FF4444",
                                           foreground="#ffffff", relief="raised", borderwidth=1)
                    for pattern, label, client_name in other_patterns:
                        for match in pattern.finditer(text):
                            text_widget.tag_add("contamination", _oti(match.start()), _oti(match.end()))
                    self.update_status(f"\u26a0 Copy blocked — {len(findings)} contamination match(es) in note")
                    return

        # ── STEP 3: Defang / unsafe content check ───────────────────
        unsafe_patterns = [
            r'https?://',
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b'
        ]
        is_unsafe = any(re.search(pattern, text, re.IGNORECASE) for pattern in unsafe_patterns)
        def _do_copy(txt):
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            self._tab_copy_counts[current_frame] = self._tab_copy_counts.get(current_frame, 0) + 1
            cnt = self._tab_copy_counts[current_frame]
            self._mileage['copies'] = self._mileage.get('copies', 0) + 1
            self._log_action('copy', f'copy #{cnt} for this tab')
            self._update_traffic_light()
            self.schedule_clipboard_clear()
            if self.config.COPY_CLEAR:
                text_widget.delete("1.0", "end")
                self._tab_copy_counts[current_frame] = 0
                self.validation_label.config(text="Copied & Cleared", fg="green")
                self.update_status(f"Copied safely — note cleared (copy #{cnt})")
            else:
                self.validation_label.config(text=f"Copied ({cnt}x)", fg="green")
                self.update_status(f"Text copied safely (copy #{cnt} for this tab)")
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
                self._mileage['near_misses'] = self._mileage.get('near_misses', 0) + 1
                self._log_action('near_miss_defang', 'Copied with undefanged IOCs')
                _do_copy(text)
                self.validation_label.config(text="Copied (Unsafe)", fg="orange")
                dialog.destroy()
            def cancel_copy():
                self.validation_label.config(text="Copy Cancelled", fg="red")
                dialog.destroy()
            tk.Button(button_frame, text="Copy Anyway", command=copy_anyway,
                bg="#ff6b6b", fg="white", activebackground="#ff4c4c",
                activeforeground="white", width=12).pack(side="left", padx=5)
            tk.Button(button_frame, text="Cancel", command=cancel_copy,
                bg="#666666", fg="white", activebackground="#888888",
                activeforeground="white", width=12).pack(side="left", padx=5)
            return
        _do_copy(text)

    # --------------------- Syntax Highlighting ---------------------
    def on_text_change_event(self, event=None):
        """Handle text change events - syntax highlighting and status update"""
        if event and event.widget:
            current = self.notebook.select()
            if current:
                frame = self.notebook.nametowidget(current)
                if frame in self._tab_copy_counts:
                    self._tab_copy_counts[frame] = 0
                # Lock client selector on first keystroke if content now exists
                tw = self.get_text_widget(frame)
                if tw and tw.get('1.0', 'end-1c').strip():
                    if self.active_client and frame not in self._tab_locked_client:
                        self._tab_locked_client[frame] = self.active_client
                        self.client_combo.config(state='disabled')
                        self.add_tooltip(self.client_combo,
                            f'Locked to: {self.active_client} — clear tab to change client')
                else:
                    # Tab is empty — unlock
                    self._tab_locked_client.pop(frame, None)
                    self.client_combo.config(state='readonly')
            # Mileage: count keystrokes that produce characters
            if event and event.keysym and len(event.keysym) == 1:
                self._mileage['chars_typed'] = self._mileage.get('chars_typed', 0) + 1
            # Debounce traffic light update
            if self._traffic_light_job:
                try:
                    self.root.after_cancel(self._traffic_light_job)
                except Exception:
                    pass
            self._traffic_light_job = self.root.after(500, self._update_traffic_light)
            text_widget = event.widget
            if self.config.SYNTAX_HIGHLIGHTING:
                job_attr = f'_hl_job_{id(text_widget)}'
                existing = getattr(self, job_attr, None)
                if existing:
                    try:
                        self.root.after_cancel(existing)
                    except Exception:
                        pass
                job = self.root.after(400, lambda tw=text_widget: self.apply_syntax_highlighting(tw))
                setattr(self, job_attr, job)
            self.root.after_idle(lambda: self.update_status("Ready"))
            if self.active_client and self.clients:
                if self._contamination_job:
                    try:
                        self.root.after_cancel(self._contamination_job)
                    except Exception:
                        pass
                self._contamination_job = self.root.after(600, self._passive_contamination_scan)
    
    def on_text_focus(self, event=None):
        """Handle text widget focus events"""
        self.update_status("Ready")
        # Reapply button colours -- tkinter can reset them when focus shifts
        self.update_button_colors()
    
    def on_cursor_move(self, event=None):
        """Handle cursor movement"""
        self.root.after_idle(lambda: self.update_status("Ready"))

    def apply_syntax_highlighting(self, text_widget):
        if not self.config.SYNTAX_HIGHLIGHTING:
            return
        text = text_widget.get("1.0", "end-1c")
        if len(text) > 100_000:
            return
        if self.config.DARK_MODE:
            colors = {'url':'#66B2FF','ip':'#FFB366','email':'#66FF66',
                      'hash':'#FF66FF','defanged':'#FFFF66'}
        else:
            colors = {'url':'#0066CC','ip':'#CC6600','email':'#009900',
                      'hash':'#CC00CC','defanged':'#CC9900'}
        patterns = {
            'url':      [self.ioc_patterns['url'], re.compile(r'hxxps?\[\:\/\/\][^\s<>"]{2,}', re.IGNORECASE)],
            'ip':       [self.ioc_patterns['ipv4'], self.ioc_patterns['ipv6']],
            'email':    [self.ioc_patterns['email']],
            'hash':     [self.ioc_patterns['hash_md5'], self.ioc_patterns['hash_sha1'], self.ioc_patterns['hash_sha256']],
            'defanged': [re.compile(r'\[[.:\@\/\#]+\]')],
        }
        import bisect as _bisect
        line_offsets = [0]
        for i, ch in enumerate(text):
            if ch == '\n':
                line_offsets.append(i + 1)
        def offset_to_index(offset):
            line = _bisect.bisect_right(line_offsets, offset) - 1
            col = offset - line_offsets[line]
            return f"{line + 1}.{col}"
        for tag in ['url', 'ip', 'email', 'hash', 'defanged']:
            text_widget.tag_remove(tag, '1.0', 'end')
            text_widget.tag_config(tag, foreground=colors[tag])
        for tag, pattern_list in patterns.items():
            for pattern in pattern_list:
                for match in pattern.finditer(text):
                    try:
                        text_widget.tag_add(tag,
                            offset_to_index(match.start()),
                            offset_to_index(match.end()))
                    except Exception:
                        pass

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
        """Open template in a new tab — requires client to be selected."""
        if not self.active_client:
            messagebox.showwarning(
                "Select a Client First",
                "Please select an active client from the 🏢 Client: dropdown before "
                "opening a template.\n\nThis ensures the note is associated with the "
                "correct client before you start writing."
            )
            return
        if template_name in self.templates:
            content = self.templates[template_name]
            content = content.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
            content = content.replace('{time}', datetime.now().strftime('%H:%M:%S'))
            content = content.replace('{datetime}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.new_tab(title=template_name, content=content)
            self._log_action('template_opened', template_name)
            self.update_status(f"Opened template in new tab: {template_name}")

    # --------------------- Find/Replace ---------------------
    def show_find_dialog(self):
        if self.find_dialog and self.find_dialog.winfo_exists():
            self.find_dialog.focus()
            return

        self._regex_find_var = tk.BooleanVar(value=False)

        self.find_dialog = tk.Toplevel(self.root)
        self.find_dialog.title("Find")
        self.find_dialog.geometry("380x130")
        self.find_dialog.transient(self.root)

        tk.Label(self.find_dialog, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.find_entry = tk.Entry(self.find_dialog, width=30)
        self.find_entry.grid(row=0, column=1, padx=5, pady=5)
        self.find_entry.focus()

        tk.Checkbutton(self.find_dialog, text="Regex",
                       variable=self._regex_find_var).grid(row=0, column=2, padx=4)

        button_frame = tk.Frame(self.find_dialog)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)

        tk.Button(button_frame, text="Find Next", command=self.find_next).pack(side="left", padx=5)
        tk.Button(button_frame, text="Find All",  command=self.find_all).pack(side="left", padx=5)
        tk.Button(button_frame, text="Clear",     command=self.clear_find).pack(side="left", padx=5)

        self.find_entry.bind('<Return>', lambda e: self.find_next())

    def show_replace_dialog(self):
        if self.find_dialog and self.find_dialog.winfo_exists():
            self.find_dialog.destroy()

        self._regex_find_var = tk.BooleanVar(value=False)

        self.find_dialog = tk.Toplevel(self.root)
        self.find_dialog.title("Find and Replace")
        self.find_dialog.geometry("400x200")
        self.find_dialog.transient(self.root)

        tk.Label(self.find_dialog, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.find_entry = tk.Entry(self.find_dialog, width=30)
        self.find_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Checkbutton(self.find_dialog, text="Regex",
                       variable=self._regex_find_var).grid(row=0, column=2, padx=4)

        tk.Label(self.find_dialog, text="Replace:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.replace_entry = tk.Entry(self.find_dialog, width=30)
        self.replace_entry.grid(row=1, column=1, padx=5, pady=5)

        self.find_entry.focus()

        button_frame = tk.Frame(self.find_dialog)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)

        tk.Button(button_frame, text="Find Next",   command=self.find_next).pack(side="left", padx=2)
        tk.Button(button_frame, text="Replace",     command=self.replace_current).pack(side="left", padx=2)
        tk.Button(button_frame, text="Replace All", command=self.replace_all).pack(side="left", padx=2)
        tk.Button(button_frame, text="Clear",       command=self.clear_find).pack(side="left", padx=2)

        self.find_entry.bind('<Return>', lambda e: self.find_next())

    def _use_regex(self):
        return getattr(self, '_regex_find_var', None) and self._regex_find_var.get()

    def find_next(self):
        if not hasattr(self, 'find_entry'):
            return

        term = self.find_entry.get()
        current = self.notebook.select()
        if not current or not term:
            return

        use_regex = self._use_regex()
        current_frame = self.notebook.nametowidget(current)
        text_widget   = self.get_text_widget(current_frame)
        count_var     = tk.IntVar()

        try:
            start_pos = text_widget.index(tk.INSERT)
            pos = text_widget.search(term, start_pos, stopindex="end",
                                     nocase=not use_regex, regexp=use_regex, count=count_var)
            if not pos:
                pos = text_widget.search(term, "1.0", stopindex=start_pos,
                                         nocase=not use_regex, regexp=use_regex, count=count_var)
        except Exception:
            self.update_status("Invalid search pattern")
            return

        if pos:
            match_len = count_var.get() if use_regex else len(term)
            end_pos   = f"{pos}+{match_len}c"
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

        use_regex     = self._use_regex()
        current_frame = self.notebook.nametowidget(current)
        text_widget   = self.get_text_widget(current_frame)
        count_var     = tk.IntVar()

        text_widget.tag_remove("found", "1.0", "end")
        idx   = "1.0"
        count = 0
        try:
            while True:
                idx = text_widget.search(term, idx, nocase=not use_regex,
                                         regexp=use_regex, stopindex="end", count=count_var)
                if not idx:
                    break
                match_len = count_var.get() if use_regex else len(term)
                lastidx   = f"{idx}+{match_len}c"
                text_widget.tag_add("found", idx, lastidx)
                idx = lastidx
                count += 1
        except Exception:
            self.update_status("Invalid search pattern")
            return
        text_widget.tag_config("found", background="yellow")
        self.update_status(f"Found {count} occurrence{'s' if count != 1 else ''}")

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

        find_term    = self.find_entry.get()
        replace_term = self.replace_entry.get()
        current      = self.notebook.select()

        if not current or not find_term:
            return

        use_regex     = self._use_regex()
        current_frame = self.notebook.nametowidget(current)
        text_widget   = self.get_text_widget(current_frame)
        text          = text_widget.get("1.0", "end-1c")

        try:
            if use_regex:
                new_text, count = re.subn(find_term, replace_term, text)
            else:
                count    = text.count(find_term)
                new_text = text.replace(find_term, replace_term)
        except Exception:
            self.update_status("Invalid regex pattern")
            return

        if count > 0:
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", new_text)
            if self.config.SYNTAX_HIGHLIGHTING:
                self.apply_syntax_highlighting(text_widget)
            self.update_status(f"Replaced {count} occurrence{'s' if count != 1 else ''}")

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
        # Restore theme preset if set
        if hasattr(self.config, 'THEME_NAME') and self.config.THEME_NAME not in ('Default Dark', 'Default Light', ''):
            self.root.after(200, lambda: self._apply_theme_preset(self.config.THEME_NAME))
        else:
            self.remove_dark_mode()
        self.update_button_colors()
        if hasattr(self, 'welcome_text_widget') and hasattr(self, 'welcome_frame'):
            self._theme_welcome_tab(self.welcome_text_widget, self.welcome_frame)
        self._reposition_close_buttons()
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
                    # Skip Safe Copy -- it keeps its own green colour
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
                    # Skip Safe Copy -- it keeps its own green colour
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
        settings_window.geometry("700x580")
        settings_window.transient(self.root)
        settings_window.grab_set()
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text="OK", command=lambda: self.save_and_close_settings(settings_window)).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Apply", command=self.apply_settings_changes).pack(side="right", padx=5)
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=(10,0))
        
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

        tw_frame = ttk.Frame(notebook)
        notebook.add(tw_frame, text="Training Wheels")
        self.create_training_wheels_tab(tw_frame)
        
        clients_frm = ttk.Frame(notebook)
        notebook.add(clients_frm, text="Clients")
        self.create_clients_tab(clients_frm)

        mileage_frm = ttk.Frame(notebook)
        notebook.add(mileage_frm, text="Session Mileage")
        self.create_mileage_tab(mileage_frm)
        if IOC_ENRICHMENT_AVAILABLE:
            apikeys_frame = ttk.Frame(notebook)
            notebook.add(apikeys_frame, text="API Keys")
            self.create_apikeys_tab(apikeys_frame)
        
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
                                 values=[
                                     "Consolas", "Courier New", "Lucida Console",
                                     "Monaco", "Menlo", "Source Code Pro", "Ubuntu Mono",
                                     "Fira Code", "JetBrains Mono", "Cascadia Code",
                                     "Hack", "Inconsolata", "DejaVu Sans Mono",
                                     "Segoe UI", "Arial", "Calibri",
                                 ])
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
        copy_frame = ttk.LabelFrame(parent, text="Safe Copy Behaviour")
        copy_frame.pack(fill="x", padx=10, pady=5)
        self.copy_clear_var = tk.BooleanVar(value=self.config.COPY_CLEAR)
        ttk.Checkbutton(copy_frame,
            text="Copy-Clear: automatically clear the note after Safe Copy",
            variable=self.copy_clear_var).pack(anchor="w", padx=5, pady=2)
        ttk.Label(copy_frame, text="Clears the tab immediately after a successful copy.",
            foreground="grey", font=("Arial", 8)).pack(anchor="w", padx=20, pady=(0,4))
        self.copy_count_warn_var = tk.BooleanVar(value=self.config.COPY_COUNT_WARN)
        ttk.Checkbutton(copy_frame,
            text="Copy-Count: warn if the same note is copied more than once",
            variable=self.copy_count_warn_var).pack(anchor="w", padx=5, pady=2)
        ttk.Label(copy_frame, text="Warns if Safe Copy is pressed again before the note changes.",
            foreground="grey", font=("Arial", 8)).pack(anchor="w", padx=20, pady=(0,4))

        cb_frame = ttk.Frame(copy_frame)
        cb_frame.pack(fill="x", padx=5, pady=(2, 6))
        ttk.Label(cb_frame, text="Auto-clear clipboard after (seconds, 0 = off):").pack(side="left")
        self.clipboard_clear_var = tk.IntVar(value=self.config.CLIPBOARD_CLEAR_DELAY)
        ttk.Spinbox(cb_frame, from_=0, to=300, textvariable=self.clipboard_clear_var,
                    width=5).pack(side="left", padx=6)
        ttk.Label(cb_frame, text="(clears clipboard automatically after each Safe Copy)",
                  foreground="grey", font=("Arial", 8)).pack(side="left")
        lock_frame = ttk.LabelFrame(parent, text="Session Lock  (Ctrl+L)")
        lock_frame.pack(fill="x", padx=10, pady=5)
        pw_row = ttk.Frame(lock_frame)
        pw_row.pack(fill="x", padx=5, pady=4)
        ttk.Label(pw_row, text="Lock passphrase:").pack(side="left")
        self._lock_pw_var = tk.StringVar(value=self.config.LOCK_PASSWORD)
        self._lock_pw_entry = ttk.Entry(pw_row, textvariable=self._lock_pw_var,
                                        show="●", width=22)
        self._lock_pw_entry.pack(side="left", padx=6)

        def _toggle_show_lock():
            cur = self._lock_pw_entry.cget("show")
            self._lock_pw_entry.config(show="" if cur else "●")
            lock_show_btn.config(text="Hide" if cur else "Show")

        lock_show_btn = ttk.Button(pw_row, text="Show", width=6, command=_toggle_show_lock)
        lock_show_btn.pack(side="left")
        ttk.Label(lock_frame, text="Leave blank to disable passphrase check.",
                  foreground="grey", font=("Arial", 8)).pack(anchor="w", padx=5, pady=(0, 4))

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
        if hasattr(self, 'copy_clear_var'):
            self.config.COPY_CLEAR = self.copy_clear_var.get()
        if hasattr(self, 'copy_count_warn_var'):
            self.config.COPY_COUNT_WARN = self.copy_count_warn_var.get()
        if hasattr(self, 'clipboard_clear_var'):
            self.config.CLIPBOARD_CLEAR_DELAY = self.clipboard_clear_var.get()
        if hasattr(self, '_lock_pw_var'):
            self.config.LOCK_PASSWORD = self._lock_pw_var.get()
        if hasattr(self, 'theme_preset_var'):
            self.config.THEME_NAME = self.theme_preset_var.get()
        
        if hasattr(self, 'vt_api_key_var'):
            self.config.API_KEYS['virustotal'] = self.vt_api_key_var.get().strip()
        if hasattr(self, 'abuse_api_key_var'):
            self.config.API_KEYS['abuseipdb'] = self.abuse_api_key_var.get().strip()
        
        if IOC_ENRICHMENT_AVAILABLE:
            self.enrichment_engine = IOCEnrichment(api_keys=self.config.API_KEYS)
        
        if self.config.DARK_MODE:
            self.apply_dark_mode()
        # Restore theme preset if set
        if hasattr(self.config, 'THEME_NAME') and self.config.THEME_NAME not in ('Default Dark', 'Default Light', ''):
            self.root.after(200, lambda: self._apply_theme_preset(self.config.THEME_NAME))
        else:
            self.remove_dark_mode()
        
        self.update_all_fonts()
        self.save_snippets()
        self.save_templates_data()
        self.update_copypasta_menu()
        self.update_templates_menu()
        self.update_status("Settings applied")
    
    def save_and_close_settings(self, window):
        self.apply_settings_changes()
        window.destroy()
    
    # --------------------- Training Wheels Checklist Editor ---------------------
    def create_training_wheels_tab(self, parent):
        """Settings tab for editing Training Wheels checklists."""
        ttk.Label(parent, text="Edit checklists for each incident type:").pack(anchor="w", padx=10, pady=5)

        top = ttk.Frame(parent)
        top.pack(fill="both", expand=True, padx=10, pady=5)

        # ── Left: incident type list ─────────────────────────────────────
        left = ttk.Frame(top)
        left.pack(side="left", fill="y", padx=(0, 6))

        ttk.Label(left, text="Incident Type:").pack(anchor="w")
        self.tw_edit_type_listbox = tk.Listbox(left, width=22, exportselection=False)
        self.tw_edit_type_listbox.pack(fill="y", expand=True)
        for name in self.TRAINING_CHECKLISTS.keys():
            self.tw_edit_type_listbox.insert(tk.END, name)
        self.tw_edit_type_listbox.bind("<<ListboxSelect>>", self._tw_edit_on_type_select)

        type_btn_frame = ttk.Frame(left)
        type_btn_frame.pack(fill="x", pady=2)
        ttk.Button(type_btn_frame, text="+ Type", command=self._tw_edit_add_type, width=9).pack(side="left", padx=1)
        ttk.Button(type_btn_frame, text="✕ Type", command=self._tw_edit_del_type, width=9).pack(side="left", padx=1)

        # ── Middle: section list ─────────────────────────────────────────
        mid = ttk.Frame(top)
        mid.pack(side="left", fill="y", padx=(0, 6))

        ttk.Label(mid, text="Section:").pack(anchor="w")
        self.tw_edit_section_listbox = tk.Listbox(mid, width=22, exportselection=False)
        self.tw_edit_section_listbox.pack(fill="y", expand=True)
        self.tw_edit_section_listbox.bind("<<ListboxSelect>>", self._tw_edit_on_section_select)

        sec_btn_frame = ttk.Frame(mid)
        sec_btn_frame.pack(fill="x", pady=2)
        ttk.Button(sec_btn_frame, text="+ Section", command=self._tw_edit_add_section, width=10).pack(side="left", padx=1)
        ttk.Button(sec_btn_frame, text="✕ Section", command=self._tw_edit_del_section, width=10).pack(side="left", padx=1)

        # ── Right: item editor ───────────────────────────────────────────
        right = ttk.Frame(top)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(right, text="Checklist Items (one per line):").pack(anchor="w")
        self.tw_edit_items_text = tk.Text(right, font=("Consolas", 9), wrap="word")
        self.tw_edit_items_text.pack(fill="both", expand=True)

        item_btn_frame = ttk.Frame(right)
        item_btn_frame.pack(fill="x", pady=2)
        ttk.Button(item_btn_frame, text="Save Items", command=self._tw_edit_save_items).pack(side="left", padx=2)
        ttk.Label(item_btn_frame, text="  (one checklist item per line)",
                  font=("Arial", 8), foreground="gray").pack(side="left")

        # Restore button
        restore_frame = ttk.Frame(parent)
        restore_frame.pack(fill="x", padx=10, pady=(0, 5))
        ttk.Button(restore_frame, text="Restore Defaults",
                   command=self._tw_edit_restore_defaults).pack(side="left")
        ttk.Label(restore_frame, text="  Resets all checklists to built-in defaults",
                  font=("Arial", 8), foreground="gray").pack(side="left")

        # Pre-select first type
        if self.tw_edit_type_listbox.size() > 0:
            self.tw_edit_type_listbox.selection_set(0)
            self._tw_edit_on_type_select()

    def _tw_edit_current_type(self):
        sel = self.tw_edit_type_listbox.curselection()
        if not sel:
            return None
        return self.tw_edit_type_listbox.get(sel[0])

    def _tw_edit_current_section_index(self):
        sel = self.tw_edit_section_listbox.curselection()
        if not sel:
            return None
        return sel[0]

    def _tw_edit_on_type_select(self, event=None):
        """Populate sections list when an incident type is selected."""
        type_name = self._tw_edit_current_type()
        if not type_name:
            return
        self.tw_edit_section_listbox.delete(0, tk.END)
        self.tw_edit_items_text.delete("1.0", tk.END)
        for section_name, _ in self.TRAINING_CHECKLISTS.get(type_name, []):
            self.tw_edit_section_listbox.insert(tk.END, section_name)

    def _tw_edit_on_section_select(self, event=None):
        """Populate items editor when a section is selected."""
        type_name = self._tw_edit_current_type()
        idx = self._tw_edit_current_section_index()
        if type_name is None or idx is None:
            return
        sections = self.TRAINING_CHECKLISTS.get(type_name, [])
        if idx < len(sections):
            _, items = sections[idx]
            self.tw_edit_items_text.delete("1.0", tk.END)
            self.tw_edit_items_text.insert("1.0", "\n".join(items))

    def _tw_edit_save_items(self):
        """Save edited items back to the checklist for the selected section."""
        type_name = self._tw_edit_current_type()
        idx = self._tw_edit_current_section_index()
        if type_name is None or idx is None:
            messagebox.showerror("Error", "Please select an incident type and section first.")
            return
        raw = self.tw_edit_items_text.get("1.0", "end-1c")
        items = [line for line in raw.splitlines() if line.strip()]
        sections = self.TRAINING_CHECKLISTS[type_name]
        section_name = sections[idx][0]
        sections[idx] = (section_name, items)
        self.update_status(f"Saved items for {type_name} → {section_name}")
        # Refresh live panel if visible
        if self.config.TRAINING_WHEELS and self.tw_incident_var.get() == type_name:
            self._tw_load_checklist()

    def _tw_edit_add_type(self):
        name = simpledialog.askstring("New Incident Type", "Enter incident type name:", parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self.TRAINING_CHECKLISTS:
            messagebox.showerror("Error", f"'{name}' already exists.")
            return
        self.TRAINING_CHECKLISTS[name] = [("TRIAGE", ["Add your first checklist item here"])]
        self.tw_edit_type_listbox.insert(tk.END, name)
        # Also update the live panel dropdown
        self.tw_type_combo["values"] = list(self.TRAINING_CHECKLISTS.keys())
        self.update_status(f"Added incident type: {name}")

    def _tw_edit_del_type(self):
        type_name = self._tw_edit_current_type()
        if not type_name:
            messagebox.showerror("Error", "Please select an incident type to delete.")
            return
        if len(self.TRAINING_CHECKLISTS) <= 1:
            messagebox.showerror("Error", "Cannot delete the last incident type.")
            return
        if not messagebox.askyesno("Confirm", f"Delete incident type '{type_name}' and all its checklists?"):
            return
        del self.TRAINING_CHECKLISTS[type_name]
        sel = self.tw_edit_type_listbox.curselection()
        self.tw_edit_type_listbox.delete(sel[0])
        self.tw_edit_section_listbox.delete(0, tk.END)
        self.tw_edit_items_text.delete("1.0", tk.END)
        self.tw_type_combo["values"] = list(self.TRAINING_CHECKLISTS.keys())
        self.update_status(f"Deleted incident type: {type_name}")

    def _tw_edit_add_section(self):
        type_name = self._tw_edit_current_type()
        if not type_name:
            messagebox.showerror("Error", "Please select an incident type first.")
            return
        name = simpledialog.askstring("New Section", "Enter section name (e.g. CONTAINMENT):", parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip().upper()
        self.TRAINING_CHECKLISTS[type_name].append((name, ["Add checklist item here"]))
        self.tw_edit_section_listbox.insert(tk.END, name)
        self.update_status(f"Added section: {name}")

    def _tw_edit_del_section(self):
        type_name = self._tw_edit_current_type()
        idx = self._tw_edit_current_section_index()
        if type_name is None or idx is None:
            messagebox.showerror("Error", "Please select a section to delete.")
            return
        sections = self.TRAINING_CHECKLISTS[type_name]
        if len(sections) <= 1:
            messagebox.showerror("Error", "Cannot delete the last section in an incident type.")
            return
        sec_name = sections[idx][0]
        if not messagebox.askyesno("Confirm", f"Delete section '{sec_name}'?"):
            return
        del sections[idx]
        self.tw_edit_section_listbox.delete(idx)
        self.tw_edit_items_text.delete("1.0", tk.END)
        self.update_status(f"Deleted section: {sec_name}")

    def _tw_edit_restore_defaults(self):
        if not messagebox.askyesno("Restore Defaults",
                                   "This will reset all checklists to the built-in defaults.\nAny custom edits will be lost. Continue?"):
            return
        # Reload from the class-level defaults
        self.TRAINING_CHECKLISTS = {
            k: [(s, list(items)) for s, items in v]
            for k, v in SOCNotesApp.TRAINING_CHECKLISTS.items()
        }
        # Refresh the editor listboxes
        self.tw_edit_type_listbox.delete(0, tk.END)
        for name in self.TRAINING_CHECKLISTS.keys():
            self.tw_edit_type_listbox.insert(tk.END, name)
        self.tw_edit_section_listbox.delete(0, tk.END)
        self.tw_edit_items_text.delete("1.0", tk.END)
        self.tw_type_combo["values"] = list(self.TRAINING_CHECKLISTS.keys())
        if self.config.TRAINING_WHEELS:
            self._tw_load_checklist()
        self.update_status("Training Wheels checklists restored to defaults")


    # --------------------- Client Management & Contamination Detection ---------------------

    def _refresh_client_combo(self):
        names = ["— None —"] + sorted(self.clients.keys())
        self.client_combo["values"] = names
        if self.active_client_var.get() not in names:
            self.active_client_var.set("— None —")

    def _on_client_selected(self, event=None):
        chosen = self.active_client_var.get()
        new_client = "" if chosen == "— None —" else chosen
        # If tab has content and is locked to a different client, confirm change
        current = self.notebook.select()
        if current:
            frame = self.notebook.nametowidget(current)
            tw = self.get_text_widget(frame)
            if tw and tw.get('1.0', 'end-1c').strip() and frame in self._tab_locked_client:
                if not messagebox.askyesno('Change Client?',
                    f'This tab is locked to client "{self._tab_locked_client[frame]}".\n\n'
                    'Changing client will clear the tab content. Continue?'):
                    # Revert combo to previous value
                    self.active_client_var.set(self.active_client or '— None —')
                    return
                tw.delete('1.0', 'end')
                self._tab_copy_counts.pop(frame, None)
                self._tab_locked_client.pop(frame, None)
        self.active_client = new_client
        self.save_settings()
        self._clear_contamination_highlights()
        self._log_action('client_selected', self.active_client or 'None')
        # Apply client colour to the current tab
        if self.active_client:
            colour = self.clients.get(self.active_client, {}).get("colour", "none") or "none"
            if colour != "none" and current:
                self._set_tab_colour(self.notebook.nametowidget(current), colour)
            self.update_status(f"Active client: {self.active_client} — press ⚠ Check to scan")
        else:
            self.update_status("No active client selected")

    def _get_client_patterns(self, client_name):
        import re as _re
        data = self.clients.get(client_name, {})
        patterns = []
        for domain in data.get("email_domains", []):
            domain = domain.strip().lower()
            if domain:
                patterns.append((_re.compile(_re.escape(domain), _re.IGNORECASE), f"email domain ({domain})", client_name))
        for prefix in data.get("hostname_prefixes", []):
            prefix = prefix.strip()
            if prefix:
                patterns.append((_re.compile(_re.escape(prefix), _re.IGNORECASE), f"hostname prefix ({prefix})", client_name))
        for cidr in data.get("ip_ranges", []):
            cidr = cidr.strip()
            if cidr:
                base = cidr.split("/")[0].rsplit(".", 1)[0]
                if base:
                    patterns.append((_re.compile(_re.escape(base), _re.IGNORECASE), f"IP range ({cidr})", client_name))
        for kw in data.get("keywords", []):
            kw = kw.strip()
            if kw:
                patterns.append((_re.compile("\\b" + _re.escape(kw) + "\\b", _re.IGNORECASE), f"keyword ({kw})", client_name))
        return patterns

    def _clear_contamination_highlights(self):
        current = self.notebook.select()
        if not current:
            return
        frame = self.notebook.nametowidget(current)
        tw = self.get_text_widget(frame)
        if tw:
            tw.tag_remove("contamination", "1.0", "end")

    def run_contamination_check(self):
        if not self.active_client:
            messagebox.showinfo("No Client Selected",
                "Please select an active client from the toolbar dropdown first.")
            return
        current = self.notebook.select()
        if not current:
            return
        frame = self.notebook.nametowidget(current)
        tw = self.get_text_widget(frame)
        if not tw:
            return
        text = tw.get("1.0", "end-1c")
        other_patterns = []
        for cname in self.clients:
            if cname != self.active_client:
                other_patterns.extend(self._get_client_patterns(cname))
        if not other_patterns:
            messagebox.showinfo("No Other Clients",
                "No other clients are registered. Add clients in Tools → Settings → Clients.")
            return
        import bisect as _bisect, re as _re
        line_offsets = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                line_offsets.append(i + 1)
        def offset_to_index(offset):
            line = _bisect.bisect_right(line_offsets, offset) - 1
            col = offset - line_offsets[line]
            return f"{line + 1}.{col}"
        tw.tag_remove("contamination", "1.0", "end")
        tw.tag_config("contamination", background="#FF4444", foreground="#ffffff",
                      relief="raised", borderwidth=1)
        findings = []
        for pattern, label, client_name in other_patterns:
            for match in pattern.finditer(text):
                start = offset_to_index(match.start())
                end = offset_to_index(match.end())
                tw.tag_add("contamination", start, end)
                findings.append({"client": client_name, "type": label,
                                  "value": match.group(), "line": start.split(".")[0]})
        if not findings:
            self.update_status(f"✓ No contamination detected for client: {self.active_client}")
            messagebox.showinfo("Clean", f"No cross-client data detected for '{self.active_client}'.")
            return
        self._mileage['contamination_checks'] = self._mileage.get('contamination_checks', 0) + 1
        self._log_action('contamination_found',
            f"{len(findings)} match(es): " + ", ".join(f['value'] for f in findings[:3]))
        self.update_status(f"⚠ {len(findings)} contamination match(es) found — see report")
        self._show_contamination_report(findings)

    def _passive_contamination_scan(self):
        self._contamination_job = None
        if not self.active_client or not self.clients:
            return
        current = self.notebook.select()
        if not current:
            return
        frame = self.notebook.nametowidget(current)
        tw = self.get_text_widget(frame)
        if not tw:
            return
        text = tw.get("1.0", "end-1c")
        if len(text) > 200_000:
            return
        other_patterns = []
        for cname in self.clients:
            if cname != self.active_client:
                other_patterns.extend(self._get_client_patterns(cname))
        import re as _re
        count = sum(len(p.findall(text)) for p, _, _ in other_patterns)
        if count:
            self.update_status(f"⚠ {count} possible contamination match(es) — press ⚠ Check for details")

    def _show_contamination_report(self, findings):
        win = tk.Toplevel(self.root)
        win.title(f"Contamination Report — Active: {self.active_client}")
        win.geometry("720x480")
        win.transient(self.root)
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        header = tk.Frame(win, bg="#CC2222", pady=6)
        header.pack(fill="x")
        tk.Label(header, text=f"⚠  {len(findings)} cross-client identifier(s) detected",
                 bg="#CC2222", fg="white", font=("Consolas", 11, "bold")).pack(side="left", padx=12)
        tk.Label(header, text=f"Active: {self.active_client}",
                 bg="#CC2222", fg="#ffcccc", font=("Consolas", 9)).pack(side="right", padx=12)
        cols = ("Line", "Matched Value", "Identifier Type", "Belongs To")
        tree_frame = tk.Frame(win)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        for col, w in zip(cols, [60, 220, 200, 160]):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=50)
        clients_seen = {}
        for f in findings:
            cname = f["client"]
            if cname not in clients_seen:
                clients_seen[cname] = len(clients_seen) % 2
            tag = f"client_{clients_seen[cname]}"
            tree.insert("", "end", values=(f["line"], f["value"], f["type"], cname), tags=(tag,))
        tree.tag_configure("client_0", background="#fff0f0")
        tree.tag_configure("client_1", background="#ffe0e0")
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        def copy_report():
            lines = [f"Contamination Report — Active: {self.active_client}",
                     f"Matches: {len(findings)}", ""]
            for f in findings:
                lines.append(f"Line {f['line']:>4}  {f['value']:<30}  {f['type']:<30}  {f['client']}")
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(lines))
            self.update_status("Report copied to clipboard")
        def clear_highlights():
            self._clear_contamination_highlights()
            win.destroy()
        ttk.Button(btn_frame, text="Copy Report", command=copy_report).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Clear Highlights", command=clear_highlights).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side="right", padx=4)

    def create_clients_tab(self, parent):
        ttk.Label(parent, text="Register clients and their identifiers for cross-contamination detection:").pack(
            anchor="w", padx=10, pady=(8, 4))
        pane = tk.Frame(parent)
        pane.pack(fill="both", expand=True, padx=10, pady=4)
        left = tk.Frame(pane)
        left.pack(side="left", fill="y", padx=(0, 8))
        ttk.Label(left, text="Clients:").pack(anchor="w")
        self._client_listbox = tk.Listbox(left, width=20, exportselection=False)
        self._client_listbox.pack(fill="y", expand=True)
        self._client_listbox.bind("<<ListboxSelect>>", self._client_tab_on_select)
        btn_row = tk.Frame(left)
        btn_row.pack(fill="x", pady=2)
        ttk.Button(btn_row, text="+ Add", command=self._client_tab_add, width=8).pack(side="left", padx=1)
        ttk.Button(btn_row, text="✕ Delete", command=self._client_tab_delete, width=8).pack(side="left", padx=1)
        right = tk.Frame(pane)
        right.pack(side="left", fill="both", expand=True)
        def _field(label, attr, tip):
            f = ttk.LabelFrame(right, text=label)
            f.pack(fill="x", pady=3)
            ttk.Label(f, text=tip, foreground="grey", font=("Arial", 8)).pack(anchor="w", padx=4)
            t = tk.Text(f, height=3, font=("Consolas", 9), wrap="word")
            t.pack(fill="x", padx=4, pady=(0, 4))
            setattr(self, attr, t)
        _field("Email Domains", "_ct_email_text", "One per line  e.g.  lidl.com")
        _field("Hostname Prefixes", "_ct_host_text", "One per line  e.g.  LIDL-WS")
        _field("IP Ranges", "_ct_ip_text", "One per line  e.g.  10.1.0.0/16")
        _field("Custom Keywords", "_ct_kw_text", "One per line  e.g.  LidlRetail")

        # Default template + tab colour
        meta_frame = ttk.LabelFrame(right, text="Quick Menu Defaults")
        meta_frame.pack(fill="x", pady=3)

        tmpl_row = ttk.Frame(meta_frame)
        tmpl_row.pack(fill="x", padx=4, pady=2)
        ttk.Label(tmpl_row, text="Default template:").pack(side="left")
        self._ct_tmpl_var = tk.StringVar(value="")
        self._ct_tmpl_combo = ttk.Combobox(tmpl_row, textvariable=self._ct_tmpl_var,
                                           state="readonly", width=28)
        self._ct_tmpl_combo["values"] = ["(none)"] + list(getattr(self, 'templates', {}).keys())
        self._ct_tmpl_combo.pack(side="left", padx=6)
        ttk.Label(meta_frame,
                  text="Used when [0] Skip Template is pressed in Quick Menu",
                  foreground="grey", font=("Arial", 8)).pack(anchor="w", padx=4, pady=(0, 2))

        colour_row = ttk.Frame(meta_frame)
        colour_row.pack(fill="x", padx=4, pady=(2, 4))
        ttk.Label(colour_row, text="Tab colour:").pack(side="left")
        self._ct_colour_var = tk.StringVar(value="none")
        for col, emoji in [("none","\u2716"),("red","\U0001f7e5"),("orange","\U0001f7e7"),
                           ("yellow","\U0001f7e8"),("green","\U0001f7e9"),
                           ("blue","\U0001f7e6"),("purple","\U0001f7ea")]:
            ttk.Radiobutton(colour_row, text=emoji, variable=self._ct_colour_var,
                            value=col).pack(side="left", padx=2)

        save_row = tk.Frame(right)
        save_row.pack(fill="x", pady=4)
        ttk.Button(save_row, text="💾 Save Identifiers",
                   command=self._client_tab_save_identifiers).pack(side="left", padx=2)
        ttk.Label(save_row, text="Select a client first, then edit and save.",
                  foreground="grey", font=("Arial", 8)).pack(side="left", padx=6)
        for name in sorted(self.clients.keys()):
            self._client_listbox.insert(tk.END, name)

    def _client_tab_current(self):
        sel = self._client_listbox.curselection()
        return self._client_listbox.get(sel[0]) if sel else None

    def _client_tab_on_select(self, event=None):
        name = self._client_tab_current()
        if not name:
            return
        data = self.clients.get(name, {})
        for attr, key in [("_ct_email_text", "email_domains"),
                           ("_ct_host_text", "hostname_prefixes"),
                           ("_ct_ip_text", "ip_ranges"),
                           ("_ct_kw_text", "keywords")]:
            w = getattr(self, attr, None)
            if w:
                w.delete("1.0", "end")
                w.insert("1.0", "\n".join(data.get(key, [])))
        # Populate default template + colour
        if hasattr(self, '_ct_tmpl_var'):
            self._ct_tmpl_combo["values"] = ["(none)"] + list(getattr(self, 'templates', {}).keys())
            self._ct_tmpl_var.set(data.get("default_template", "(none)") or "(none)")
        if hasattr(self, '_ct_colour_var'):
            self._ct_colour_var.set(data.get("colour", "none") or "none")

    def _client_tab_save_identifiers(self):
        name = self._client_tab_current()
        if not name:
            messagebox.showerror("No Client Selected", "Please select a client from the list first.")
            return
        def _lines(attr):
            w = getattr(self, attr, None)
            return [l.strip() for l in w.get("1.0","end-1c").splitlines() if l.strip()] if w else []
        tmpl  = getattr(self, '_ct_tmpl_var', None)
        col   = getattr(self, '_ct_colour_var', None)
        self.clients[name] = {
            "email_domains":     _lines("_ct_email_text"),
            "hostname_prefixes": _lines("_ct_host_text"),
            "ip_ranges":         _lines("_ct_ip_text"),
            "keywords":          _lines("_ct_kw_text"),
            "default_template":  (tmpl.get() if tmpl and tmpl.get() != "(none)" else ""),
            "colour":            (col.get() if col else "none"),
        }
        self.save_settings()
        self._refresh_client_combo()
        self.update_status(f"Client '{name}' identifiers saved")

    def _client_tab_add(self):
        name = simpledialog.askstring("New Client", "Enter client name:", parent=self.root)
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self.clients:
            messagebox.showerror("Duplicate", f"Client '{name}' already exists.")
            return
        self.clients[name] = {"email_domains":[], "hostname_prefixes":[],
                              "ip_ranges":[], "keywords":[],
                              "default_template":"", "colour":"none"}
        self._client_listbox.insert(tk.END, name)
        self.save_settings()
        self._refresh_client_combo()
        self.update_status(f"Client '{name}' added")

    def _client_tab_delete(self):
        name = self._client_tab_current()
        if not name:
            return
        if not messagebox.askyesno("Delete", f"Delete client '{name}' and all their identifiers?"):
            return
        del self.clients[name]
        sel = self._client_listbox.curselection()
        self._client_listbox.delete(sel[0])
        if self.active_client == name:
            self.active_client = ""
            self.active_client_var.set("— None —")
        self.save_settings()
        self._refresh_client_combo()
        self.update_status(f"Client '{name}' deleted")


    # --------------------- Action Log ---------------------

    def _log_action(self, action, detail=''):
        """Append a timestamped entry to the in-memory action log."""
        from datetime import datetime as _dt
        entry = {
            'time': _dt.now().strftime('%H:%M:%S'),
            'action': action,
            'detail': str(detail)[:200],
            'client': self.active_client or '',
        }
        self._action_log.append(entry)
        # Keep last 500 entries to avoid unbounded growth
        if len(self._action_log) > 500:
            self._action_log = self._action_log[-500:]

    # --------------------- Traffic Light ---------------------

    def _update_traffic_light(self):
        """Update the traffic light canvas based on current note health."""
        self._traffic_light_job = None
        if not hasattr(self, 'traffic_light_canvas'):
            return
        current = self.notebook.select()
        if not current:
            self.traffic_light_canvas.itemconfig(self._tl_circle, fill='#555555')
            return
        frame = self.notebook.nametowidget(current)
        tw = self.get_text_widget(frame)
        if not tw:
            self.traffic_light_canvas.itemconfig(self._tl_circle, fill='#555555')
            return
        text = tw.get('1.0', 'end-1c')
        if not text.strip():
            # Grey — empty
            self.traffic_light_canvas.itemconfig(self._tl_circle, fill='#555555')
            return
        # Red — contamination detected
        if self.active_client and self.clients:
            import re as _re_tl
            other_patterns = []
            for cname in self.clients:
                if cname != self.active_client:
                    other_patterns.extend(self._get_client_patterns(cname))
            if other_patterns and len(text) <= 200_000:
                for pattern, _, _ in other_patterns:
                    if pattern.search(text):
                        self.traffic_light_canvas.itemconfig(self._tl_circle, fill='#FF3333')
                        return
        # Amber — undefanged IOCs present
        unsafe = [
            r'https?://',
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ]
        import re as _re_tl2
        for p in unsafe:
            if _re_tl2.search(p, text, _re_tl2.IGNORECASE):
                self.traffic_light_canvas.itemconfig(self._tl_circle, fill='#FFAA00')
                return
        # Green — clean
        self.traffic_light_canvas.itemconfig(self._tl_circle, fill='#44CC44')

    # --------------------- Client Lock UI ---------------------

    def _update_client_lock_ui(self):
        """Update client combo lock state to match the current tab."""
        current = self.notebook.select()
        if not current:
            self.client_combo.config(state='readonly')
            return
        frame = self.notebook.nametowidget(current)
        if frame in self._tab_locked_client:
            self.client_combo.config(state='disabled')
        else:
            self.client_combo.config(state='readonly')

    # --------------------- Incident Timer ---------------------

    def _tick_timer(self):
        """Update the per-tab incident timer label every second."""
        self._timer_job = None
        current = self.notebook.select()
        if current:
            from datetime import datetime as _dt3
            frame = self.notebook.nametowidget(current)
            if frame in self._tab_timers:
                elapsed = _dt3.now() - self._tab_timers[frame]
                total_seconds = int(elapsed.total_seconds())
                h = total_seconds // 3600
                m = (total_seconds % 3600) // 60
                s = total_seconds % 60
                if h > 0:
                    self.timer_label.config(text=f"\u23f1 {h}:{m:02d}:{s:02d}", fg="#ff9944")
                elif m >= 30:
                    self.timer_label.config(text=f"\u23f1 {m:02d}:{s:02d}", fg="#ff6644")
                elif m >= 15:
                    self.timer_label.config(text=f"\u23f1 {m:02d}:{s:02d}", fg="#ffaa44")
                else:
                    self.timer_label.config(text=f"\u23f1 {m:02d}:{s:02d}", fg="#88aa88")
            else:
                self.timer_label.config(text="\u23f1 --:--", fg="#888888")
        if self._tab_timers:
            self._timer_job = self.root.after(1000, self._tick_timer)

    # --------------------- Breakglass Mode ---------------------

    def show_breakglass_mode(self):
        """Emergency incident review — surfaces action log and containment prompts."""
        from datetime import datetime as _dt4
        self._mileage['breakglass_events'] = self._mileage.get('breakglass_events', 0) + 1
        self._log_action('breakglass_triggered', 'Emergency mode activated')

        win = tk.Toplevel(self.root)
        win.title("\U0001f6a8  Breakglass Mode — Emergency Review")
        win.geometry("820x600")
        win.transient(self.root)
        win.grab_set()
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")

        # Red header
        header = tk.Frame(win, bg="#8B0000", pady=8)
        header.pack(fill="x")
        tk.Label(header, text="\U0001f6a8  I Think I've Made a Mistake — Emergency Review",
                 bg="#8B0000", fg="white", font=("Consolas", 12, "bold")).pack(side="left", padx=12)
        tk.Label(header, text=_dt4.now().strftime("%H:%M:%S"),
                 bg="#8B0000", fg="#ffaaaa", font=("Consolas", 9)).pack(side="right", padx=12)

        paned = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # Left — contextual prompts
        left_frame = tk.Frame(paned)
        paned.add(left_frame, weight=1)

        tk.Label(left_frame, text="IMMEDIATE CHECKS", font=("Consolas", 10, "bold"),
                 fg="#ff4444").pack(anchor="w", pady=(0, 4))

        # Build contextual prompts from action log
        prompts = self._build_breakglass_prompts()
        prompt_box = tk.Text(left_frame, wrap="word", font=("Consolas", 9),
                             bg="#1a0000", fg="#ffcccc", relief="flat",
                             height=20, state="normal")
        prompt_box.pack(fill="both", expand=True)
        prompt_box.tag_config("heading", foreground="#ff6666", font=("Consolas", 9, "bold"))
        prompt_box.tag_config("item", foreground="#ffdddd")
        prompt_box.tag_config("ok", foreground="#44cc44")
        prompt_box.tag_config("warn", foreground="#ffaa00")
        prompt_box.tag_config("critical", foreground="#ff3333", font=("Consolas", 9, "bold"))
        for p_type, p_text in prompts:
            prompt_box.insert("end", p_text + "\n", p_type)
        prompt_box.config(state="disabled")

        # Right — action log
        right_frame = tk.Frame(paned)
        paned.add(right_frame, weight=1)

        tk.Label(right_frame, text="SESSION ACTIVITY LOG", font=("Consolas", 10, "bold"),
                 fg="#aaaaff").pack(anchor="w", pady=(0, 4))

        log_frame = tk.Frame(right_frame)
        log_frame.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(log_frame, orient="vertical")
        cols = ("Time", "Action", "Client", "Detail")
        tree = ttk.Treeview(log_frame, columns=cols, show="headings",
                            yscrollcommand=vsb.set, height=18)
        vsb.config(command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        for col, w in zip(cols, [55, 120, 80, 220]):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=30)

        # Insert log newest-first
        for entry in reversed(self._action_log[-100:]):
            tag = ""
            if entry['action'] in ('contamination_found', 'near_miss_defang',
                                    'near_miss_contamination'):
                tag = "warn"
            elif entry['action'] == 'breakglass_triggered':
                tag = "critical"
            tree.insert("", "end", values=(
                entry['time'], entry['action'],
                entry.get('client', ''), entry['detail']
            ), tags=(tag,))
        tree.tag_configure("warn", foreground="#cc6600")
        tree.tag_configure("critical", foreground="#cc0000")

        # Footer
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))

        def copy_log():
            lines = ["ThreatPad — Breakglass Mode Log",
                     f"Generated: {_dt4.now().strftime('%Y-%m-%d %H:%M:%S')}",
                     f"Active client: {self.active_client or 'None'}", ""]
            for entry in self._action_log:
                lines.append(f"[{entry['time']}] {entry['action']:<30} "
                             f"client={entry.get('client',''):<15} {entry['detail']}")
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(lines))
            self.update_status("Activity log copied to clipboard")

        ttk.Button(btn_frame, text="Copy Full Log", command=copy_log).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Close", command=win.destroy).pack(side="right", padx=4)

    def _build_breakglass_prompts(self):
        """Analyse the action log and return contextual containment prompts."""
        prompts = []
        log = self._action_log

        prompts.append(("heading", "=== BASED ON YOUR SESSION ACTIVITY ==="))
        prompts.append(("item", ""))

        # Check for recent near-miss copies
        near_misses = [e for e in log if e['action'] == 'near_miss_defang']
        if near_misses:
            last = near_misses[-1]
            prompts.append(("critical", f"\u26a0  DEFANG WARNING OVERRIDDEN at {last['time']}"))
            prompts.append(("warn", "    Check: was that note pasted into a ticket?"))
            prompts.append(("warn", "    If yes: defang the ticket content immediately."))
            prompts.append(("item", ""))

        # Check for contamination events
        contamination = [e for e in log if e['action'] == 'contamination_found']
        if contamination:
            last_c = contamination[-1]
            prompts.append(("critical", f"\u26a0  CONTAMINATION DETECTED at {last_c['time']}"))
            prompts.append(("warn", f"    Detail: {last_c['detail']}"))
            prompts.append(("warn", "    Check: was any note copied after this point?"))
            prompts.append(("warn", "    If yes: review what was in the clipboard at copy time."))
            prompts.append(("item", ""))

        # Check for multiple clients in the session
        clients_used = list(set(e.get('client', '') for e in log if e.get('client')))
        if len(clients_used) > 1:
            prompts.append(("warn", f"\u26a0  Multiple clients in session: {', '.join(clients_used)}"))
            prompts.append(("warn", "    Verify each tab was associated with the correct client."))
            prompts.append(("item", ""))

        # Copies with no client set
        unclean_copies = [e for e in log
                          if e['action'] == 'copy' and not e.get('client')]
        if unclean_copies:
            prompts.append(("warn", f"\u26a0  {len(unclean_copies)} copy(s) made with NO client selected"))
            prompts.append(("warn", "    Check those notes were not mixed with client data."))
            prompts.append(("item", ""))

        # General always-present advice
        prompts.append(("heading", "=== GENERAL CONTAINMENT STEPS ==="))
        prompts.append(("item", ""))
        for step in [
            "1. Stop and breathe. Identify exactly what you think went wrong.",
            "2. Check your SIEM/ticketing system for any notes just pasted.",
            "3. If client data was mixed: notify your team lead immediately.",
            "4. Document what happened in your incident ticket.",
            "5. If a data breach is suspected: follow your MSSP breach procedure.",
        ]:
            prompts.append(("item", f"  {step}"))
        prompts.append(("item", ""))
        prompts.append(("ok", "  The activity log on the right shows everything"))
        prompts.append(("ok", "  ThreatPad logged in this session."))

        return prompts

    # --------------------- Mistake Memory ---------------------

    def _analyse_mistake_patterns(self):
        """
        Analyse the action log for recurring patterns.
        Returns a list of warning strings to surface proactively.
        """
        warnings = []
        log = self._action_log
        if len(log) < 5:
            return warnings

        near_misses = [e for e in log if e['action'] == 'near_miss_defang']
        contaminations = [e for e in log if e['action'] == 'contamination_found']
        copies_no_client = [e for e in log if e['action'] == 'copy' and not e.get('client')]

        if len(near_misses) >= 3:
            warnings.append(
                f"\u26a0  You have overridden the defang warning {len(near_misses)} time(s) this session. "
                "Consider defanging before copying rather than after the warning fires."
            )

        if len(contaminations) >= 2:
            # Find which clients keep appearing
            all_details = " ".join(e['detail'] for e in contaminations)
            warnings.append(
                f"\u26a0  Contamination has been detected {len(contaminations)} time(s) this session. "
                f"Check whether client identifiers need updating in Settings \u2192 Clients."
            )

        if len(copies_no_client) >= 2:
            warnings.append(
                f"\u26a0  {len(copies_no_client)} note(s) copied with no active client set. "
                "Make a habit of selecting a client before opening a template."
            )

        return warnings

    # --------------------- Session Mileage Tab ---------------------

    def create_mileage_tab(self, parent):
        """Settings tab showing session mileage counters."""
        from datetime import datetime as _dt5

        ttk.Label(parent, text="Session Mileage — resets whenever you choose.",
                  font=("Consolas", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        ttk.Label(parent,
                  text="Tracks your activity since the last reset. "
                       "Like a trip odometer — reset it whenever a new shift begins.",
                  foreground="grey", font=("Arial", 8), wraplength=450).pack(
                      anchor="w", padx=10, pady=(0, 8))

        # Stats grid
        stats_frame = ttk.LabelFrame(parent, text="Current Session")
        stats_frame.pack(fill="x", padx=10, pady=4)

        start_str = self._mileage.get('session_start', '')
        if start_str:
            try:
                start_dt = _dt5.fromisoformat(start_str)
                elapsed = _dt5.now() - start_dt
                h = int(elapsed.total_seconds()) // 3600
                m = (int(elapsed.total_seconds()) % 3600) // 60
                session_age = f"{h}h {m}m" if h else f"{m}m"
            except Exception:
                session_age = "Unknown"
        else:
            session_age = "Unknown"

        stats = [
            ("Session age",          session_age),
            ("Characters typed",     str(self._mileage.get('chars_typed', 0))),
            ("Safe copies",          str(self._mileage.get('copies', 0))),
            ("Defangs performed",    str(self._mileage.get('defangs', 0))),
            ("Contamination checks", str(self._mileage.get('contamination_checks', 0))),
            ("IOC extractions",      str(self._mileage.get('iocs_extracted', 0))),
            ("Near-misses logged",   str(self._mileage.get('near_misses', 0))),
            ("Breakglass events",       str(self._mileage.get('breakglass_events', 0))),
            ("Actions logged",       str(len(self._action_log))),
        ]

        for i, (label, value) in enumerate(stats):
            row = ttk.Frame(stats_frame)
            row.pack(fill="x", padx=8, pady=1)
            bg = "#f8f8f0" if i % 2 == 0 else "#f0f0e8"
            ttk.Label(row, text=label, width=24, anchor="w").pack(side="left")
            ttk.Label(row, text=value, font=("Consolas", 10, "bold"),
                      foreground="#0066cc").pack(side="left", padx=8)

        # Mistake memory section
        warnings = self._analyse_mistake_patterns()
        if warnings:
            warn_frame = ttk.LabelFrame(parent, text="\u26a0  Mistake Memory — Patterns Detected")
            warn_frame.pack(fill="x", padx=10, pady=(8, 4))
            for w in warnings:
                ttk.Label(warn_frame, text=w, foreground="#cc4400",
                          font=("Arial", 9), wraplength=420,
                          justify="left").pack(anchor="w", padx=8, pady=3)
        else:
            ok_frame = ttk.LabelFrame(parent, text="Mistake Memory")
            ok_frame.pack(fill="x", padx=10, pady=(8, 4))
            ttk.Label(ok_frame, text="\u2713  No recurring patterns detected in this session.",
                      foreground="#009900", font=("Arial", 9)).pack(anchor="w", padx=8, pady=4)

        # Reset button
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=8)

        def reset_mileage():
            from datetime import datetime as _dt6
            if messagebox.askyesno("Reset Mileage",
                "Reset all session mileage counters and action log?\n\n"
                "This is like resetting a trip odometer — previous totals are lost."):
                self._mileage = {
                    'chars_typed': 0, 'copies': 0, 'defangs': 0,
                    'contamination_checks': 0, 'iocs_extracted': 0,
                    'near_misses': 0, 'breakglass_events': 0,
                    'session_start': _dt6.now().isoformat(),
                }
                self._action_log = []
                self.save_settings()
                self.update_status("Session mileage reset")
                # Refresh the tab
                for widget in parent.winfo_children():
                    widget.destroy()
                self.create_mileage_tab(parent)

        ttk.Button(btn_frame, text="\u21ba Reset Mileage",
                   command=reset_mileage).pack(side="left")
        ttk.Label(btn_frame, text="  Clears all counters and the action log.",
                  foreground="grey", font=("Arial", 8)).pack(side="left")

    # --------------------- Theme Presets ---------------------

    def _apply_theme_preset(self, theme_name):
        """Apply a colour theme preset to all text widgets."""
        themes = {
            "Default Dark": {
                "bg": "#2b2b2b", "fg": "#ffffff", "sel_bg": "#505050",
                "line_bg": "#404040", "line_fg": "#888888", "cursor": "#ffffff",
            },
            "Default Light": {
                "bg": "#ffffff", "fg": "#000000", "sel_bg": "#0078D4",
                "line_bg": "#f0f0f0", "line_fg": "#666666", "cursor": "#000000",
            },
            "Solarized Dark": {
                "bg": "#002b36", "fg": "#839496", "sel_bg": "#073642",
                "line_bg": "#073642", "line_fg": "#586e75", "cursor": "#839496",
            },
            "Nord": {
                "bg": "#2e3440", "fg": "#d8dee9", "sel_bg": "#434c5e",
                "line_bg": "#3b4252", "line_fg": "#4c566a", "cursor": "#d8dee9",
            },
            "Dracula": {
                "bg": "#282a36", "fg": "#f8f8f2", "sel_bg": "#44475a",
                "line_bg": "#44475a", "line_fg": "#6272a4", "cursor": "#f8f8f2",
            },
            "High Contrast": {
                "bg": "#000000", "fg": "#ffffff", "sel_bg": "#0000ff",
                "line_bg": "#1a1a1a", "line_fg": "#ffffff", "cursor": "#ffff00",
            },
            "Warm Terminal": {
                "bg": "#1c1008", "fg": "#e8d5a3", "sel_bg": "#3d2b0a",
                "line_bg": "#241608", "line_fg": "#8a7040", "cursor": "#e8d5a3",
            },
            "Ocean": {
                "bg": "#0a1628", "fg": "#c5d8f0", "sel_bg": "#1a3a5c",
                "line_bg": "#0e1f38", "line_fg": "#3a5878", "cursor": "#c5d8f0",
            },
        }
        t = themes.get(theme_name, themes["Default Dark"])
        self.config.THEME_NAME = theme_name
        for frame in self.tabs:
            tc = self.tabs[frame]
            tw = tc.text if hasattr(tc, 'text') else tc
            tw.config(bg=t["bg"], fg=t["fg"],
                      insertbackground=t["cursor"],
                      selectbackground=t["sel_bg"],
                      selectforeground=t["fg"])
            if hasattr(tc, 'line_numbers'):
                tc.line_numbers.config(bg=t["line_bg"], fg=t["line_fg"],
                                       selectbackground=t["sel_bg"])
        self.root.configure(bg=t["bg"])
        self.frame_buttons.config(bg=t["bg"])
        self.status_bar.config(bg=t["bg"])
        self.status_left.config(bg=t["bg"], fg=t["fg"])
        self.status_right.config(bg=t["bg"], fg=t["fg"])
        self.save_settings()
        self.update_status(f"Theme applied: {theme_name}")
        if self.config.SYNTAX_HIGHLIGHTING:
            for frame in self.tabs:
                tc = self.tabs[frame]
                tw = tc.text if hasattr(tc, 'text') else tc
                self.apply_syntax_highlighting(tw)

    # --------------------- Tab Colour Coding ---------------------

    def _set_tab_colour(self, frame, colour):
        """Set a coloured square indicator on a tab using a PhotoImage."""
        if not hasattr(self, '_tab_colours'):
            self._tab_colours = {}
        if not hasattr(self, '_tab_colour_images'):
            self._tab_colour_images = {}

        self._tab_colours[frame] = colour

        _HEX = {
            "red":    "#ff6b6b",
            "orange": "#ff8c42",
            "yellow": "#ffd700",
            "green":  "#4caf50",
            "blue":   "#4488ff",
            "purple": "#9c59d1",
        }
        try:
            # Strip any legacy emoji prefix from the title
            current_title = self.notebook.tab(frame, "text")
            for pfx in ("\U0001f7e5 ", "\U0001f7e7 ", "\U0001f7e8 ",
                        "\U0001f7e9 ", "\U0001f7e6 ", "\U0001f7ea ", "📌 "):
                current_title = current_title.lstrip()
                if current_title.startswith(pfx):
                    current_title = current_title[len(pfx):]
            self.notebook.tab(frame, text=current_title)

            if colour == "none":
                self._tab_colour_images.pop(frame, None)
                self.notebook.tab(frame, image="", compound="none")
            else:
                hex_col = _HEX.get(colour, "#888888")
                img = tk.PhotoImage(width=12, height=12)
                img.put(hex_col, to=(0, 0, 12, 12))
                # Slightly darken the 1-px border for a framed look
                border = _darken_hex(hex_col, 0.6)
                img.put(border, to=(0, 0, 12, 1))
                img.put(border, to=(0, 11, 12, 12))
                img.put(border, to=(0, 0, 1, 12))
                img.put(border, to=(11, 0, 12, 12))
                self._tab_colour_images[frame] = img   # keep reference
                self.notebook.tab(frame, image=img, compound="left")
        except Exception:
            pass

    def show_tab_colour_menu(self, event=None):
        """Right-click context menu for tab colour coding."""
        current = self.notebook.select()
        if not current:
            return
        frame = self.notebook.nametowidget(current)
        menu = tk.Menu(self.root, tearoff=0)

        # Pin / Unpin
        if frame in self._pinned_tabs:
            menu.add_command(label="📌 Unpin Tab", command=lambda: self.toggle_pin_tab(frame))
        else:
            menu.add_command(label="📌 Pin Tab",   command=lambda: self.toggle_pin_tab(frame))

        # Reopen last closed
        if self._closed_tabs:
            last_title = self._closed_tabs[-1][0]
            menu.add_command(label=f"↩ Reopen '{last_title[:30]}'",
                             command=self.reopen_closed_tab)

        menu.add_separator()
        menu.add_command(label="Tab colour:")
        menu.add_separator()
        for colour, label in [("none", "\u2716 No colour"),
                               ("red", "\U0001f7e5 Red"),
                               ("orange", "\U0001f7e7 Orange"),
                               ("yellow", "\U0001f7e8 Yellow"),
                               ("green", "\U0001f7e9 Green"),
                               ("blue", "\U0001f7e6 Blue"),
                               ("purple", "\U0001f7ea Purple")]:
            menu.add_command(label=label,
                             command=lambda c=colour, f=frame: self._set_tab_colour(f, c))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass
        finally:
            menu.grab_release()

    # --------------------- Recently Closed / Pin / Bookmark / Lock / Redaction ---------------------

    def reopen_closed_tab(self):
        if not self._closed_tabs:
            self.update_status("No recently closed tabs")
            return
        title, content, filepath = self._closed_tabs.pop()
        self.new_tab(title, content)
        if filepath:
            current = self.notebook.select()
            self.current_file_paths[current] = filepath
        self.update_status(f"Reopened: {title}")

    def toggle_pin_tab(self, frame=None):
        current = self.notebook.select()
        if not current:
            return
        frame = frame or self.notebook.nametowidget(current)
        if frame in self._pinned_tabs:
            self._pinned_tabs.discard(frame)
            title = self.notebook.tab(frame, "text")
            if title.startswith("📌 "):
                self.notebook.tab(frame, text=title[3:])
            self.update_status("Tab unpinned")
        else:
            self._pinned_tabs.add(frame)
            title = self.notebook.tab(frame, "text")
            if not title.startswith("📌 "):
                self.notebook.tab(frame, text="📌 " + title)
            self.update_status("Tab pinned — Ctrl+W and ×  will be blocked")
        self._reposition_close_buttons()

    def jump_to_line(self):
        current = self.notebook.select()
        if not current:
            return
        frame       = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(frame)
        line_count  = int(text_widget.index("end-1c").split(".")[0])

        dialog = tk.Toplevel(self.root)
        dialog.title("Jump to Line")
        dialog.geometry("280x90")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text=f"Line number  (1 – {line_count}):").pack(pady=(12, 4))
        entry = tk.Entry(dialog, width=10, justify="center")
        entry.pack()
        entry.focus()

        def _go():
            try:
                n = max(1, min(int(entry.get()), line_count))
                text_widget.mark_set(tk.INSERT, f"{n}.0")
                text_widget.see(f"{n}.0")
                text_widget.focus_set()
                dialog.destroy()
            except ValueError:
                pass

        entry.bind("<Return>", lambda e: _go())
        tk.Button(dialog, text="Go", command=_go).pack(pady=6)

    def toggle_bookmark(self):
        current = self.notebook.select()
        if not current:
            return
        frame       = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(frame)
        line = int(text_widget.index(tk.INSERT).split(".")[0])

        self._bookmarks.setdefault(frame, set())
        if line in self._bookmarks[frame]:
            self._bookmarks[frame].discard(line)
            text_widget.tag_remove("bookmark", f"{line}.0", f"{line+1}.0")
            self.update_status(f"Bookmark removed (line {line})")
        else:
            self._bookmarks[frame].add(line)
            text_widget.tag_add("bookmark", f"{line}.0", f"{line+1}.0")
            text_widget.tag_config("bookmark", background="#1a3a1a",
                                   foreground="#00ff88", font=("Consolas", self.config.FONT_SIZE))
            self.update_status(f"Bookmark set (line {line})")

    def next_bookmark(self):
        current = self.notebook.select()
        if not current:
            return
        frame       = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(frame)
        cur_line    = int(text_widget.index(tk.INSERT).split(".")[0])
        marks       = sorted(self._bookmarks.get(frame, set()))
        if not marks:
            self.update_status("No bookmarks in this tab  (F2 to set one)")
            return
        nxt = next((m for m in marks if m > cur_line), marks[0])
        text_widget.mark_set(tk.INSERT, f"{nxt}.0")
        text_widget.see(f"{nxt}.0")
        self.update_status(f"Bookmark → line {nxt}")

    def prev_bookmark(self):
        current = self.notebook.select()
        if not current:
            return
        frame       = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(frame)
        cur_line    = int(text_widget.index(tk.INSERT).split(".")[0])
        marks       = sorted(self._bookmarks.get(frame, set()), reverse=True)
        if not marks:
            self.update_status("No bookmarks in this tab  (F2 to set one)")
            return
        prv = next((m for m in marks if m < cur_line), marks[0])
        text_widget.mark_set(tk.INSERT, f"{prv}.0")
        text_widget.see(f"{prv}.0")
        self.update_status(f"Bookmark ← line {prv}")

    def lock_session(self):
        self.root.update_idletasks()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w = self.root.winfo_width()
        h = self.root.winfo_height()

        lock_win = tk.Toplevel(self.root)
        lock_win.overrideredirect(True)           # no title bar / borders
        lock_win.geometry(f"{w}x{h}+{x}+{y}")
        lock_win.attributes("-topmost", True)
        lock_win.configure(bg="#0d0d0d")
        lock_win.protocol("WM_DELETE_WINDOW", lambda: None)

        # Keep overlay aligned when root window moves/resizes
        def _follow(event=None):
            try:
                lock_win.geometry(
                    f"{self.root.winfo_width()}x{self.root.winfo_height()}"
                    f"+{self.root.winfo_x()}+{self.root.winfo_y()}"
                )
            except Exception:
                pass
        self.root.bind("<Configure>", _follow, add=True)

        tk.Label(lock_win, text="🔒  SESSION LOCKED",
                 font=("Consolas", 26, "bold"), bg="#0d0d0d", fg="#00bfff").pack(pady=(80, 16))
        tk.Label(lock_win, text="Enter passphrase to unlock",
                 font=("Consolas", 11), bg="#0d0d0d", fg="#555555").pack()

        entry = tk.Entry(lock_win, show="●", font=("Consolas", 14),
                         width=24, justify="center", bg="#1a1a1a", fg="white",
                         insertbackground="white")
        entry.pack(pady=14)
        entry.focus()

        msg_lbl = tk.Label(lock_win, text="", font=("Consolas", 11),
                           bg="#0d0d0d", fg="#ff6b6b")
        msg_lbl.pack()

        stored = self.config.LOCK_PASSWORD

        def _try_unlock():
            if not stored or entry.get() == stored:
                self.root.unbind("<Configure>")
                lock_win.destroy()
                self.update_status("Session unlocked")
            else:
                msg_lbl.config(text="Incorrect passphrase")
                entry.delete(0, "end")

        entry.bind("<Return>", lambda e: _try_unlock())
        tk.Button(lock_win, text="  Unlock  ", command=_try_unlock,
                  font=("Consolas", 13, "bold"), bg="#00bfff", fg="#0d0d0d",
                  activebackground="#0099cc", bd=0, pady=8).pack(pady=10)
        lock_win.grab_set()

    def toggle_redaction(self):
        self._redaction_on = not self._redaction_on
        for frame, text_frame in self.tabs.items():
            try:
                tw = text_frame.text if hasattr(text_frame, 'text') else text_frame
                if self._redaction_on:
                    bg = tw.cget("background")
                    tw.tag_add("redacted", "1.0", "end")
                    tw.tag_config("redacted", foreground=bg, selectforeground=bg)
                else:
                    tw.tag_remove("redacted", "1.0", "end")
            except Exception:
                pass
        if self._redaction_on:
            self.validation_label.config(text="🔴 REDACTED", fg="red")
            self.update_status("Redaction ON — text hidden from view")
        else:
            self.validation_label.config(text="")
            self.update_status("Redaction OFF")

    # --------------------- Clipboard Auto-Clear ---------------------

    def schedule_clipboard_clear(self):
        delay = self.config.CLIPBOARD_CLEAR_DELAY
        if delay <= 0:
            return
        if self._clipboard_clear_job:
            self.root.after_cancel(self._clipboard_clear_job)
        self._clipboard_clear_job = self.root.after(
            int(delay * 1000), self._do_clipboard_clear)

    def _do_clipboard_clear(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("")
            self.update_status(f"Clipboard auto-cleared after {self.config.CLIPBOARD_CLEAR_DELAY}s")
        except Exception:
            pass
        self._clipboard_clear_job = None

    # --------------------- IOC Live Panel ---------------------

    def toggle_ioc_panel(self):
        if self._ioc_panel_win and self._ioc_panel_win.winfo_exists():
            self._ioc_panel_win.destroy()
            self._ioc_panel_win = None
            return
        self._open_ioc_panel()

    def _open_ioc_panel(self):
        win = tk.Toplevel(self.root)
        win.title("IOC Panel")
        win.geometry("460x500")
        win.attributes("-topmost", True)
        self._ioc_panel_win = win

        header = tk.Frame(win, bg="#111111")
        header.pack(fill="x")
        tk.Label(header, text="Live IOC Panel", font=("Consolas", 10, "bold"),
                 bg="#111111", fg="#00bfff", pady=6).pack(side="left", padx=10)
        self._ioc_panel_status = tk.Label(header, text="", font=("Consolas", 9),
                                          bg="#111111", fg="#888888")
        self._ioc_panel_status.pack(side="right", padx=10)

        # Scrollable canvas for IOC rows
        canvas_frame = tk.Frame(win)
        canvas_frame.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(canvas_frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        self._ioc_canvas = tk.Canvas(canvas_frame, bg="#0d0d0d",
                                     yscrollcommand=vsb.set, highlightthickness=0)
        self._ioc_canvas.pack(side="left", fill="both", expand=True)
        vsb.config(command=self._ioc_canvas.yview)
        self._ioc_inner = tk.Frame(self._ioc_canvas, bg="#0d0d0d")
        self._ioc_canvas_window = self._ioc_canvas.create_window(
            (0, 0), window=self._ioc_inner, anchor="nw")
        self._ioc_inner.bind("<Configure>",
            lambda e: self._ioc_canvas.configure(
                scrollregion=self._ioc_canvas.bbox("all")))

        footer = tk.Frame(win, bg="#111111")
        footer.pack(fill="x")
        tk.Button(footer, text="Refresh", font=("Consolas", 9),
                  command=self._refresh_ioc_panel,
                  bg="#333333", fg="white", bd=0, pady=4).pack(side="left", padx=8, pady=4)
        tk.Button(footer, text="Close", font=("Consolas", 9),
                  command=lambda: (win.destroy(), setattr(self, '_ioc_panel_win', None)),
                  bg="#333333", fg="white", bd=0, pady=4).pack(side="right", padx=8, pady=4)

        self._refresh_ioc_panel()
        # Auto-refresh every 3 seconds while panel is open
        self._schedule_ioc_refresh()
        win.protocol("WM_DELETE_WINDOW",
                     lambda: (win.destroy(), setattr(self, '_ioc_panel_win', None)))

    def _schedule_ioc_refresh(self):
        if self._ioc_panel_win and self._ioc_panel_win.winfo_exists():
            self._refresh_ioc_panel()
            self._ioc_panel_win.after(3000, self._schedule_ioc_refresh)

    def _refresh_ioc_panel(self):
        if not self._ioc_panel_win or not self._ioc_panel_win.winfo_exists():
            return
        for w in self._ioc_inner.winfo_children():
            w.destroy()

        current = self.notebook.select()
        if not current:
            tk.Label(self._ioc_inner, text="No tab open", bg="#0d0d0d",
                     fg="#555555", font=("Consolas", 10)).pack(pady=20)
            return

        frame       = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(frame)
        text        = text_widget.get("1.0", "end-1c")
        tab_title   = self.notebook.tab(current, "text")

        iocs = {}
        for ioc_type, pattern in self.ioc_patterns.items():
            matches = list(set(pattern.findall(text)))
            if matches:
                iocs[ioc_type] = sorted(matches)

        total = sum(len(v) for v in iocs.values())
        self._ioc_panel_status.config(text=f"{total} IOC{'s' if total!=1 else ''}  •  {tab_title[:30]}")

        TYPE_COLOURS = {
            "ipv4":"#ff6b6b","ipv6":"#ff9999","email":"#ffd700",
            "url":"#ff8c00","domain":"#87ceeb","hash_md5":"#98fb98",
            "hash_sha1":"#90ee90","hash_sha256":"#00fa9a",
        }
        if not iocs:
            tk.Label(self._ioc_inner, text="No IOCs detected",
                     bg="#0d0d0d", fg="#555555", font=("Consolas", 10)).pack(pady=20)
            return

        for ioc_type, values in iocs.items():
            hdr = tk.Frame(self._ioc_inner, bg="#1a1a1a")
            hdr.pack(fill="x", pady=(6, 2), padx=4)
            tk.Label(hdr, text=f"  {ioc_type.upper().replace('_',' ')}  ({len(values)})",
                     bg="#1a1a1a", fg="#888888", font=("Consolas", 9, "bold"),
                     anchor="w").pack(fill="x")

            for value in values:
                row = tk.Frame(self._ioc_inner, bg="#0d0d0d", cursor="hand2")
                row.pack(fill="x", padx=8, pady=1)
                colour = TYPE_COLOURS.get(ioc_type, "#e0e0e0")
                lbl = tk.Label(row, text=value, bg="#0d0d0d", fg=colour,
                               font=("Consolas", 9), anchor="w", padx=6)
                lbl.pack(side="left", fill="x", expand=True)
                # Copy button
                def _copy(v=value):
                    self.root.clipboard_clear()
                    self.root.clipboard_append(v)
                    self.update_status(f"Copied: {v}")
                cp_btn = tk.Label(row, text="⎘", bg="#0d0d0d", fg="#555555",
                                  font=("Consolas", 9), cursor="hand2")
                cp_btn.pack(side="right", padx=4)
                cp_btn.bind("<Button-1>", lambda e, v=value: _copy(v))

                # Click row → jump to IOC in text
                def _jump(e, v=value, tw=text_widget):
                    try:
                        pos = tw.search(v, "1.0", stopindex="end", nocase=False)
                        if pos:
                            tw.mark_set(tk.INSERT, pos)
                            tw.see(pos)
                            tw.focus_set()
                    except Exception:
                        pass
                for widget in (row, lbl):
                    widget.bind("<Button-1>", _jump)
                    widget.bind("<Enter>", lambda e, r=row: r.config(bg="#1a2a1a"))
                    widget.bind("<Leave>", lambda e, r=row: r.config(bg="#0d0d0d"))

    # --------------------- Export Reports ---------------------

    def export_html_report(self):
        import html as _html
        current = self.notebook.select()
        if not current:
            return
        frame       = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(frame)
        content     = text_widget.get("1.0", "end-1c")
        title       = self.notebook.tab(current, "text")
        for pfx in ("📌 ","\U0001f7e5 ","\U0001f7e7 ","\U0001f7e8 ",
                    "\U0001f7e9 ","\U0001f7e6 ","\U0001f7ea "):
            title = title.replace(pfx, "")
        title = title.strip()

        from datetime import datetime as _dt
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_html.escape(title)}</title>
<style>
  body {{font-family: Consolas, monospace; background:#0d1117; color:#e0e0e0;
         padding:32px; max-width:960px; margin:auto;}}
  h1   {{color:#00bfff; border-bottom:1px solid #333; padding-bottom:8px;}}
  .meta{{color:#888; font-size:0.85em; margin-bottom:20px;}}
  pre  {{white-space:pre-wrap; word-wrap:break-word; line-height:1.5;}}
  @media print {{body{{background:#fff;color:#000;}} h1{{color:#000;}}}}
</style>
</head>
<body>
<h1>{_html.escape(title)}</h1>
<p class="meta">Client: {_html.escape(self.active_client or '—')} &nbsp;•&nbsp;
Exported: {_dt.now().strftime('%Y-%m-%d %H:%M')}</p>
<pre>{_html.escape(content)}</pre>
</body>
</html>"""

        safe_name = re.sub(r'[^A-Za-z0-9 _-]', '_', title)
        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")],
            initialfile=safe_name + ".html")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_doc)
            self.update_status(f"HTML report exported → {filepath}")

    def export_json_report(self):
        current = self.notebook.select()
        if not current:
            return
        frame       = self.notebook.nametowidget(current)
        text_widget = self.get_text_widget(frame)
        content     = text_widget.get("1.0", "end-1c")
        title       = self.notebook.tab(current, "text")

        from datetime import datetime as _dt
        iocs = {}
        for ioc_type, pattern in self.ioc_patterns.items():
            matches = list(set(pattern.findall(content)))
            if matches:
                iocs[ioc_type] = sorted(matches)

        export = {
            "incident_title": title,
            "client":         self.active_client or "",
            "exported_at":    _dt.now().isoformat(),
            "filepath":       self.current_file_paths.get(current) or "",
            "content":        content,
            "iocs":           iocs,
        }

        safe_name = re.sub(r'[^A-Za-z0-9 _-]', '_', title)
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile=safe_name + ".json")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
            self.update_status(f"JSON report exported → {filepath}")

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
            except Exception:
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
        self.root.after(self.config.AUTO_SAVE_INTERVAL, self.auto_save)

    def on_closing(self):
        # Cancel all pending after() timers before destroying the window
        for attr in list(vars(self)):
            if attr.startswith('_hl_job_'):
                try:
                    self.root.after_cancel(getattr(self, attr))
                except Exception:
                    pass
        if self._contamination_job:
            try:
                self.root.after_cancel(self._contamination_job)
            except Exception:
                pass
        if self._timer_job:
            try:
                self.root.after_cancel(self._timer_job)
            except Exception:
                pass
        if self._traffic_light_job:
            try:
                self.root.after_cancel(self._traffic_light_job)
            except Exception:
                pass
        self._log_action('session_end', 'App closed')
        self.save_settings()  # persist mileage on close
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


# --------------------- Main ---------------------
if __name__ == "__main__":
    app = SOCNotesApp()
    app.run()