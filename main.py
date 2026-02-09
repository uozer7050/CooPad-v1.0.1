import os
import sys
import threading
import time
import json
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:
    print("Error: tkinter is not installed. Please install it for your platform.")
    sys.exit(1)


from PIL import Image, ImageOps, ImageTk
from gp_backend import GpController
from platform_info import get_platform_info
import socket
from queue import Queue
import logging

# --- Config file helpers ---
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.coopad')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'settings.json')

def load_config() -> dict:
    """Load saved settings from disk. Returns empty dict on first run."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(cfg: dict):
    """Persist settings to disk."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


# Global queue for input states
input_queue = Queue()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Get platform info on startup
platform_info = get_platform_info()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CooPad — Remote Gamepad")
        self.geometry("1100x700")

        # icon - handle cross-platform icon loading
        base = os.path.dirname(__file__)
        try:
            if sys.platform == 'win32':
                # Windows can use .ico files directly
                ico_path = os.path.join(base, "img", "src_CooPad.ico")
                if os.path.exists(ico_path):
                    self.wm_iconbitmap(ico_path)
            else:
                # Other platforms - use PNG with iconphoto
                png_path = os.path.join(base, "img", "src_CooPad.png")
                if os.path.exists(png_path):
                    icon_img = Image.open(png_path)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.iconphoto(True, icon_photo)
        except Exception:
            pass

        # style
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self._mono_font = ("Consolas", 10)
        
        # Color palette for consistent styling
        self._palette = {
            'bg': '#0d0f10',
            'frame': '#111214',
            'panel': '#151617',
            'text_bg': '#0b0b0b',
            'text_fg': '#e6e6e6',
            'entry_bg': '#1a1c1d',
            'button_bg': '#2a7bd6',
            'accent': '#2a7bd6'
        }

        # controller (backend)
        self._gp = GpController(status_cb=self._append_status, telemetry_cb=self._set_telemetry)

        # Load saved config (or empty dict on first run)
        self._config = load_config()
        self._settings_confirmed = self._config.get('settings_confirmed', False)

        # Restore saved settings into backend
        saved_rate = self._config.get('update_rate', 60)
        saved_profile = self._config.get('controller_profile', 'generic')
        self._gp.set_update_rate(saved_rate)
        self._gp.set_controller_profile(saved_profile)

        # build UI
        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=12, pady=12)

        # left controls
        left = ttk.Frame(container, width=320)
        left.pack(side='left', fill='y', padx=(0,12), pady=6)

        # logo
        logo_path = os.path.join(os.path.dirname(__file__), 'img', 'src_CooPad.png')
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path).convert('RGBA')
                img = ImageOps.fit(img, (140, 140), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                logo_label = ttk.Label(left, image=tk_img)
                logo_label.image = tk_img
                logo_label.pack(pady=(12,6))
            except Exception:
                ttk.Label(left, text='CooPad', font=(None, 18, 'bold')).pack(pady=18)
        else:
            ttk.Label(left, text='CooPad', font=(None, 18, 'bold')).pack(pady=18)

        ttk.Label(left, text='Remote Gamepad').pack(pady=(0,12))
        
        # Platform Status Panel
        status_frame = tk.Frame(left, bg='#1a1d1f', relief='solid', borderwidth=1)
        status_frame.pack(fill='x', padx=12, pady=(0,12))
        
        # Platform name
        platform_name = platform_info.get_platform_name()
        ttk.Label(status_frame, text=f'Platform: {platform_name}', 
                  font=(None, 9, 'bold')).pack(anchor='w', padx=8, pady=(8,4))
        
        # Host status indicator
        host_status = platform_info.get_host_status()
        host_indicator = tk.Frame(status_frame, bg='#1a1d1f')
        host_indicator.pack(fill='x', padx=8, pady=2)
        
        self.host_status_icon = tk.Label(host_indicator, text=host_status['icon'], 
                                         font=(None, 12), fg=host_status['color'],
                                         bg='#1a1d1f', width=2)
        self.host_status_icon.pack(side='left')
        
        self.host_status_label = tk.Label(host_indicator, text=host_status['message'],
                                          font=(None, 8), fg='#e5e7eb',
                                          bg='#1a1d1f', anchor='w', justify='left')
        self.host_status_label.pack(side='left', fill='x', expand=True)
        
        # Client status indicator
        client_status = platform_info.get_client_status()
        client_indicator = tk.Frame(status_frame, bg='#1a1d1f')
        client_indicator.pack(fill='x', padx=8, pady=(2,8))
        
        self.client_status_icon = tk.Label(client_indicator, text=client_status['icon'],
                                           font=(None, 12), fg=client_status['color'],
                                           bg='#1a1d1f', width=2)
        self.client_status_icon.pack(side='left')
        
        self.client_status_label = tk.Label(client_indicator, text=client_status['message'],
                                            font=(None, 8), fg='#e5e7eb',
                                            bg='#1a1d1f', anchor='w', justify='left')
        self.client_status_label.pack(side='left', fill='x', expand=True)

        # left forms: separate frames for Host and Client controls (show one at a time)
        self.host_controls = ttk.Frame(left)
        self.client_controls = ttk.Frame(left)

        # Host controls
        hc = self.host_controls
        hc.pack(fill='x', padx=12)
        ttk.Label(hc, text='Host Controls', font=(None, 10, 'bold')).pack(anchor='w', padx=8, pady=(6,2))
        self.host_btn = ttk.Button(hc, text='Start Host', command=self._toggle_host)
        self.host_btn.pack(fill='x', pady=(6,6), padx=8)
        self.host_state_label = ttk.Label(hc, text='Host: stopped', foreground='#b22222')
        self.host_state_label.pack(anchor='w', padx=8, pady=(0,6))

        # Client controls
        cc = self.client_controls
        cc.pack(fill='x', padx=12)
        ttk.Label(cc, text='Client Controls', font=(None, 10, 'bold')).pack(anchor='w', padx=8, pady=(6,2))
        ttk.Label(cc, text='Target IP', anchor='w').pack(fill='x', padx=8, pady=(6,0))
        self.ip_entry = ttk.Entry(cc)
        self.ip_entry.insert(0, '127.0.0.1')
        self.ip_entry.pack(fill='x', padx=8, pady=6)
        ttk.Label(cc, text='Port', anchor='w').pack(fill='x', padx=8, pady=(4,0))
        self.port_entry = ttk.Entry(cc)
        self.port_entry.insert(0, '7777')
        self.port_entry.pack(fill='x', padx=8, pady=6)
        self.client_btn = ttk.Button(cc, text='Start Client', command=self._toggle_client)
        self.client_btn.pack(fill='x', pady=(6,6), padx=8)
        self.client_state_label = ttk.Label(cc, text='Client: stopped', foreground='#b22222')
        self.client_state_label.pack(anchor='w', padx=8, pady=(0,6))

        ttk.Button(left, text='Clear Logs', command=self._clear_log).pack(fill='x', pady=(6,6), padx=12)
        ttk.Button(left, text='Platform Help', command=self._show_platform_help).pack(fill='x', pady=(0,12), padx=12)

        # initially show host controls only
        try:
            self.client_controls.pack_forget()
        except Exception:
            pass

        # right area
        right = ttk.Frame(container)
        right.pack(side='left', fill='both', expand=True, pady=6)

        # top black bar
        top_bar = tk.Frame(right, height=56, bg='#000000')
        top_bar.pack(fill='x', padx=0, pady=(0,8))
        self._top_bar = top_bar

        self._header_label = ttk.Label(top_bar, text='CooPad Remote — Dashboard', font=(None, 14, 'bold'))
        self._header_label.pack(side='left', padx=12)

        # Compatibility info notice
        compat_info = platform_info.get_compatibility_info()
        if compat_info['can_host'] and compat_info['can_client']:
            notice_text = (
                f"✓ {compat_info['platform']} system ready for Host and Client modes. "
                "Ensure both devices are on the same network or use VPN (ZeroTier, Tailscale)."
            )
            notice_fg = '#22c55e'
        elif compat_info['can_host']:
            notice_text = (
                f"⚠ {compat_info['platform']} system ready for Host mode. "
                "Client mode needs pygame installed. Click 'Platform Help' for setup instructions."
            )
            notice_fg = '#f59e0b'
        elif compat_info['can_client']:
            notice_text = (
                f"⚠ {compat_info['platform']} system ready for Client mode. "
                "Host mode needs virtual gamepad driver. Click 'Platform Help' for setup instructions."
            )
            notice_fg = '#f59e0b'
        else:
            notice_text = (
                f"✗ {compat_info['platform']} system not ready. "
                "Missing required drivers. Click 'Platform Help' for setup instructions."
            )
            notice_fg = '#ef4444'
        
        notice = tk.Label(right, text=notice_text, wraplength=760, justify='left',
                         fg=notice_fg, bg=self._palette['frame'], font=(None, 9))
        notice.pack(anchor='nw', padx=12, pady=(0,8))

        # custom tab buttons
        tab_btn_frame = tk.Frame(top_bar, bg=top_bar['bg'])
        tab_btn_frame.pack(side='right', padx=8)
        self._tab_buttons = {}
        self._tab_active = 'Host'

        def make_tab_button(name):
            b = tk.Button(
                tab_btn_frame,
                text=name,
                bd=0,
                bg=top_bar['bg'],
                fg='#bbbbbb',
                activebackground='#111111',
                activeforeground='#ffffff',
                padx=18,
                pady=10,
                font=('Segoe UI', 10, 'bold'),
                relief='flat',
                highlightthickness=0,
                cursor='hand2'
            )
            b.pack(side='left', padx=(8,0))
            b.config(command=lambda n=name: self._show_tab(n))
            self._tab_buttons[name] = b
            return b

        make_tab_button('Host')
        make_tab_button('Client')
        make_tab_button('Monitor')
        make_tab_button('Settings')

        # content frames
        tabs_frame = ttk.Frame(right)
        tabs_frame.pack(fill='both', expand=True, padx=12, pady=(0,0))
        host_tab = ttk.Frame(tabs_frame)
        client_tab = ttk.Frame(tabs_frame)
        monitor_tab = ttk.Frame(tabs_frame)
        settings_tab = ttk.Frame(tabs_frame)
        self._content_frames = {'Host': host_tab, 'Client': client_tab, 'Monitor': monitor_tab, 'Settings': settings_tab}

        # Host content
        ttk.Label(host_tab, text='Host Status', font=(None, 12, 'bold')).pack(anchor='nw', padx=8, pady=(8,4))
        self.host_latency_var = tk.StringVar(value='Latency: — ms')
        ttk.Label(host_tab, textvariable=self.host_latency_var).pack(anchor='nw', padx=8, pady=4)
        self.host_jitter_var = tk.StringVar(value='Jitter: — ms')
        ttk.Label(host_tab, textvariable=self.host_jitter_var).pack(anchor='nw', padx=8, pady=4)
        self.host_packets_var = tk.StringVar(value='Packets: —')
        ttk.Label(host_tab, textvariable=self.host_packets_var).pack(anchor='nw', padx=8, pady=4)
        ttk.Label(host_tab, text='Host Log', anchor='w').pack(fill='x', padx=8, pady=(8,0))
        self.host_box = tk.Text(host_tab, wrap='word', height=10, font=self._mono_font)
        self.host_box.pack(fill='both', expand=True, padx=8, pady=8)
        self.host_box.config(state='disabled')

        # Client content
        ttk.Label(client_tab, text='Client Status', font=(None, 12, 'bold')).pack(anchor='nw', padx=8, pady=(8,4))
        self.client_latency_var = tk.StringVar(value='Latency: — ms')
        ttk.Label(client_tab, textvariable=self.client_latency_var).pack(anchor='nw', padx=8, pady=4)
        self.client_jitter_var = tk.StringVar(value='Jitter: — ms')
        ttk.Label(client_tab, textvariable=self.client_jitter_var).pack(anchor='nw', padx=8, pady=4)
        self.client_packets_var = tk.StringVar(value='Packets: —')
        ttk.Label(client_tab, textvariable=self.client_packets_var).pack(anchor='nw', padx=8, pady=4)
        ttk.Label(client_tab, text='Client Log', anchor='w').pack(fill='x', padx=8, pady=(8,0))
        self.client_box = tk.Text(client_tab, wrap='word', height=10, font=self._mono_font)
        self.client_box.pack(fill='both', expand=True, padx=8, pady=8)
        self.client_box.config(state='disabled')

        # ======== Monitor tab (multi-gamepad player dashboard) ========
        monitor_header = tk.Frame(monitor_tab, bg='#111214')
        monitor_header.pack(fill='x', padx=0, pady=(0, 8))
        tk.Label(monitor_header, text='\U0001f3ae  Player Monitor', font=('Segoe UI', 14, 'bold'),
                 fg='#ffffff', bg='#111214').pack(side='left', padx=12, pady=10)
        self._monitor_status_label = tk.Label(
            monitor_header, text='Multi-Gamepad: OFF', font=('Segoe UI', 10),
            fg='#888888', bg='#111214')
        self._monitor_status_label.pack(side='right', padx=12, pady=10)

        # Scrollable player cards area
        monitor_canvas_frame = tk.Frame(monitor_tab, bg=self._palette['frame'])
        monitor_canvas_frame.pack(fill='both', expand=True, padx=0, pady=0)
        self._monitor_canvas = tk.Canvas(monitor_canvas_frame, bg=self._palette['frame'],
                                         highlightthickness=0, bd=0)
        self._monitor_scrollbar = ttk.Scrollbar(monitor_canvas_frame, orient='vertical',
                                                 command=self._monitor_canvas.yview)
        self._monitor_cards_frame = tk.Frame(self._monitor_canvas, bg=self._palette['frame'])
        self._monitor_cards_frame.bind('<Configure>',
            lambda e: self._monitor_canvas.configure(scrollregion=self._monitor_canvas.bbox('all')))
        self._monitor_canvas.create_window((0, 0), window=self._monitor_cards_frame, anchor='nw')
        self._monitor_canvas.configure(yscrollcommand=self._monitor_scrollbar.set)
        self._monitor_canvas.pack(side='left', fill='both', expand=True)
        self._monitor_scrollbar.pack(side='right', fill='y')

        # Empty state label
        self._monitor_empty_label = tk.Label(
            self._monitor_cards_frame,
            text='No players connected.\n\nEnable Multi-Gamepad Co-op in Settings\nand start the Host to see connected players here.',
            font=('Segoe UI', 11), fg='#555555', bg=self._palette['frame'],
            justify='center'
        )
        self._monitor_empty_label.pack(expand=True, pady=80)

        # Dict to track player card widgets: client_id -> {frame, name_lbl, ...}
        self._player_cards = {}

        # Host event log at the bottom of monitor tab
        tk.Label(monitor_tab, text='Connection Events', font=('Segoe UI', 10, 'bold'),
                 fg='#aaaaaa', bg=self._palette['frame'], anchor='w').pack(fill='x', padx=12, pady=(8, 2))
        self._monitor_log = tk.Text(monitor_tab, wrap='word', height=5, font=self._mono_font,
                                     bg=self._palette['text_bg'], fg=self._palette['text_fg'])
        self._monitor_log.pack(fill='x', padx=12, pady=(0, 8))
        self._monitor_log.config(state='disabled')

        # Settings content
        ttk.Label(settings_tab, text='Network Settings', font=(None, 12, 'bold')).pack(anchor='nw', padx=8, pady=(8,4))
        
        # Update rate setting
        rate_frame = ttk.Frame(settings_tab)
        rate_frame.pack(fill='x', padx=8, pady=12)
        ttk.Label(rate_frame, text='Client Update Rate:', font=(None, 10, 'bold')).pack(anchor='w', pady=(0,4))
        ttk.Label(rate_frame, text='Higher rates provide smoother gameplay but use more bandwidth.', 
                 font=(None, 9), foreground='#888888').pack(anchor='w', pady=(0,8))
        
        self.update_rate_var = tk.IntVar(value=self._config.get('update_rate', 60))
        rate_options_frame = ttk.Frame(rate_frame)
        rate_options_frame.pack(anchor='w', pady=4)
        
        ttk.Radiobutton(rate_options_frame, text='30 Hz (Low bandwidth)', 
                       variable=self.update_rate_var, value=30,
                       command=self._on_rate_change).pack(anchor='w', pady=2)
        ttk.Radiobutton(rate_options_frame, text='60 Hz (Recommended)', 
                       variable=self.update_rate_var, value=60,
                       command=self._on_rate_change).pack(anchor='w', pady=2)
        ttk.Radiobutton(rate_options_frame, text='90 Hz (High performance)', 
                       variable=self.update_rate_var, value=90,
                       command=self._on_rate_change).pack(anchor='w', pady=2)
        
        # Controller profile setting
        ttk.Separator(settings_tab, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        controller_frame = ttk.Frame(settings_tab)
        controller_frame.pack(fill='x', padx=8, pady=12)
        ttk.Label(controller_frame, text='Controller Profile:', font=(None, 10, 'bold')).pack(anchor='w', pady=(0,4))
        ttk.Label(controller_frame, text='Select your controller type for proper button and axis mapping.', 
                 font=(None, 9), foreground='#888888').pack(anchor='w', pady=(0,8))
        
        # Import controller profiles to get available options
        try:
            from gp.core.controller_profiles import get_profile_names
            profile_names = get_profile_names()
        except Exception:
            profile_names = ['Generic', 'PS4 Controller', 'PS5 Controller', 'Xbox 360 Controller']
        
        self.controller_profile_var = tk.StringVar(value=self._config.get('controller_profile_display', 'Generic'))
        controller_dropdown_frame = ttk.Frame(controller_frame)
        controller_dropdown_frame.pack(anchor='w', pady=4)
        
        ttk.Label(controller_dropdown_frame, text='Profile:').pack(side='left', padx=(0,8))
        controller_dropdown = ttk.Combobox(controller_dropdown_frame, 
                                          textvariable=self.controller_profile_var,
                                          values=profile_names,
                                          state='readonly',
                                          width=30)
        controller_dropdown.pack(side='left')
        controller_dropdown.bind('<<ComboboxSelected>>', self._on_controller_change)
        
        ttk.Label(controller_frame, text='Note: Change takes effect when client restarts.', 
                 font=(None, 8), foreground='#888888').pack(anchor='w', pady=(8,0))

        # --- Multi-Gamepad Co-op setting ---
        ttk.Separator(settings_tab, orient='horizontal').pack(fill='x', padx=8, pady=12)

        multi_gp_frame = ttk.Frame(settings_tab)
        multi_gp_frame.pack(fill='x', padx=8, pady=12)
        ttk.Label(multi_gp_frame, text='Multi-Gamepad Co-op:', font=(None, 10, 'bold')).pack(anchor='w', pady=(0,4))
        ttk.Label(multi_gp_frame, text='Allow up to 4 remote players to connect as separate virtual controllers for local co-op games.',
                 font=(None, 9), foreground='#888888', wraplength=500).pack(anchor='w', pady=(0,8))

        self._multi_gp_var = tk.BooleanVar(value=self._config.get('multi_gamepad', False))
        self._multi_gp_check = ttk.Checkbutton(
            multi_gp_frame, text='Enable Multi-Gamepad Co-op Mode',
            variable=self._multi_gp_var,
            command=self._on_multi_gamepad_toggle
        )
        self._multi_gp_check.pack(anchor='w', pady=4)

        self._multi_gp_status = tk.Label(
            multi_gp_frame,
            text='Enabled' if self._multi_gp_var.get() else 'Disabled',
            font=(None, 9, 'bold'),
            fg='#22c55e' if self._multi_gp_var.get() else '#888888',
            bg=self._palette['frame']
        )
        self._multi_gp_status.pack(anchor='w', pady=(2,0))

        # Apply saved multi-gamepad state to backend
        if self._multi_gp_var.get():
            self._gp.set_multi_gamepad(True)

        # --- Confirm & Save button ---
        ttk.Separator(settings_tab, orient='horizontal').pack(fill='x', padx=8, pady=12)

        confirm_frame = ttk.Frame(settings_tab)
        confirm_frame.pack(fill='x', padx=8, pady=(0, 8))

        self._settings_status_var = tk.StringVar(
            value='✓ Settings saved – ready to play!' if self._settings_confirmed
                  else '⚠ Please review and confirm your settings before starting.'
        )
        self._settings_status_label = tk.Label(
            confirm_frame,
            textvariable=self._settings_status_var,
            font=(None, 10, 'bold'),
            fg='#22c55e' if self._settings_confirmed else '#f59e0b',
            bg=self._palette['frame'],
            anchor='w'
        )
        self._settings_status_label.pack(anchor='w', pady=(0,8))

        self._confirm_btn = tk.Button(
            confirm_frame,
            text='  ✓  Confirm Settings & Save  ',
            font=(None, 11, 'bold'),
            bg='#22883a',
            fg='#ffffff',
            activebackground='#1a6b2e',
            activeforeground='#ffffff',
            relief='flat',
            cursor='hand2',
            command=self._confirm_settings
        )
        self._confirm_btn.pack(anchor='w', pady=(0, 4))

        # Info section
        ttk.Separator(settings_tab, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        info_frame = ttk.Frame(settings_tab)
        info_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        ttk.Label(info_frame, text='About CooPad', font=(None, 12, 'bold')).pack(anchor='w', pady=(0,8))
        
        info_text = tk.Text(info_frame, wrap='word', height=12, font=(None, 9))
        info_text.pack(fill='both', expand=True)
        info_text.insert('1.0', '''CooPad - Remote Gamepad over Network

Version: 1.0.2
License: Open Source

CooPad allows you to use a gamepad over a network connection. The client captures gamepad inputs and sends them to the host, which creates a virtual gamepad that games can use.

Features:
• Windows support for Host and Client modes
• Low latency gameplay
• Configurable update rates
• Controller profile selection (PS4, PS5, Xbox 360, Nintendo Switch)
• Real-time network statistics
• Automatic platform detection

Network Requirements:
• Both devices on same LAN, or
• Connected via VPN (ZeroTier, Tailscale, etc.)
• UDP port 7777 must be accessible

For setup help, click the "Platform Help" button.
''')
        info_text.config(state='disabled', bg=self._palette['text_bg'], 
                        fg=self._palette['text_fg'], insertbackground=self._palette['text_fg'])

        # footer
        footer = ttk.Frame(self)
        footer.pack(side='bottom', fill='x')
        self._footer_label = ttk.Label(footer, text='Ready', anchor='w')
        self._footer_label.pack(side='left', padx=8, pady=6)

        # show initial tab – go to Settings on first run
        if not self._settings_confirmed:
            self._tab_active = 'Settings'
        self._apply_tab_styles()
        self._show_tab(self._tab_active)

    def _apply_tab_styles(self):
        # make header contrast and set initial button styles
        try:
            # Use instance palette
            pal = self._palette
            self.configure(bg=pal['bg'])
            try:
                self.style.configure('TFrame', background=pal['frame'])
                self.style.configure('TLabel', background=pal['frame'], foreground=pal['text_fg'])
                self.style.configure('TButton', background=pal['button_bg'], foreground=pal['text_fg'])
                self.style.configure('TEntry', fieldbackground=pal['entry_bg'], foreground=pal['text_fg'])
            except Exception:
                pass

            self._top_bar.config(bg='#000000')
            for n, b in self._tab_buttons.items():
                try:
                    b.config(bg=self._top_bar.cget('bg'), fg='#9a9a9a')
                except Exception:
                    pass
            if self._tab_active in self._tab_buttons:
                self._tab_buttons[self._tab_active].config(bg='#111111', fg='#ffffff')
            self._header_label.config(background=self._top_bar.cget('bg'), foreground='#ffffff')
            # text widgets
            try:
                self.host_box.config(bg=pal['text_bg'], fg=pal['text_fg'], insertbackground=pal['text_fg'])
                self.client_box.config(bg=pal['text_bg'], fg=pal['text_fg'], insertbackground=pal['text_fg'])
                self._monitor_log.config(bg=pal['text_bg'], fg=pal['text_fg'], insertbackground=pal['text_fg'])
            except Exception:
                pass
        except Exception:
            pass

    def _show_tab(self, name: str):
        # switch visible content
        try:
            for n, f in self._content_frames.items():
                if n == name:
                    f.pack(fill='both', expand=True)
                else:
                    f.pack_forget()
            # show relevant left controls
            try:
                if name == 'Host':
                    self.host_controls.pack(fill='x', padx=12)
                    self.client_controls.pack_forget()
                elif name == 'Client':
                    self.client_controls.pack(fill='x', padx=12)
                    self.host_controls.pack_forget()
                else:
                    # Monitor & Settings — show host controls for convenience
                    self.host_controls.pack(fill='x', padx=12)
                    self.client_controls.pack_forget()
            except Exception:
                pass
            # update buttons
            for n, b in self._tab_buttons.items():
                try:
                    if n == name:
                        b.config(bg='#111111', fg='#ffffff')
                    else:
                        b.config(bg=self._top_bar.cget('bg'), fg='#7f7f7f')
                except Exception:
                    pass
            self._tab_active = name
        except Exception:
            pass

    def _append_status(self, text: str) -> None:
        try:
            if text.startswith('HOST|'):
                t = text.split('|', 1)[1]
                self._append_text(self.host_box, t)
            elif text.startswith('CLIENT|'):
                t = text.split('|', 1)[1]
                self._append_text(self.client_box, t)
            else:
                self._append_text(self.host_box, text)
        except Exception:
            pass

    def _append_text(self, widget: tk.Text, text: str) -> None:
        try:
            widget.config(state='normal')
            widget.insert('end', text + '\n')
            widget.see('end')
            widget.config(state='disabled')
        except Exception:
            pass

    def _set_telemetry(self, text: str) -> None:
        try:
            if text.startswith('HOST|'):
                t = text.split('|', 1)[1].strip()
                # Check for multi-gamepad telemetry messages
                # Format: HOST|PLAYER_STATS|client_id|name|color|slot|latency|jitter|rate|seq
                # Format: HOST|PLAYER_JOIN|client_id|name|color|slot
                # Format: HOST|PLAYER_LEAVE|client_id|name|color|slot
                if t.startswith('PLAYER_STATS|'):
                    self._handle_player_stats(t)
                    return
                elif t.startswith('PLAYER_JOIN|'):
                    self._handle_player_join(t)
                    return
                elif t.startswith('PLAYER_LEAVE|'):
                    self._handle_player_leave(t)
                    return
                # Legacy single-mode telemetry
                parts = [p.strip() for p in t.split('|')]
                for part in parts:
                    if part.startswith('Latency:'):
                        self.host_latency_var.set(part)
                    elif part.startswith('Jitter:'):
                        self.host_jitter_var.set(part)
                    elif part.startswith('Rate:'):
                        rate_part = part.split('seq=')[0].strip()
                        self.host_packets_var.set(rate_part)
                        if 'seq=' in part:
                            seq = part.split('seq=')[1].strip()
                            self.host_packets_var.set(f'{rate_part} | Seq: {seq}')
            elif text.startswith('CLIENT|'):
                t = text.split('|', 1)[1].strip()
                parts = [p.strip() for p in t.split('|')]
                for part in parts:
                    if part.startswith('Latency:'):
                        self.client_latency_var.set(part)
                    elif part.startswith('Jitter:'):
                        self.client_jitter_var.set(part)
                    elif part.startswith('Rate:'):
                        rate_part = part.split('seq=')[0].strip()
                        self.client_packets_var.set(rate_part)
                        if 'seq=' in part:
                            seq = part.split('seq=')[1].strip()
                            self.client_packets_var.set(f'{rate_part} | Seq: {seq}')
            else:
                self._footer_label.config(text=text)
        except Exception:
            pass

    def _toggle_host(self):
        if getattr(self, '_host_running', False) is not True:
            # --- Guard: settings must be confirmed first ---
            if not self._settings_confirmed:
                self._prompt_settings_first()
                return

            # Check if host is ready
            host_status = platform_info.get_host_status()
            if host_status['status'] == 'error':
                self._append_status(f"HOST|✗ Cannot start: {host_status['message']}")
                self._append_status(f"HOST|→ Solution: {host_status.get('action', host_status.get('details', ''))}")
                return
            elif host_status['status'] == 'warning':
                self._append_status(f"HOST|⚠ Warning: {host_status['message']}")
                self._append_status(f"HOST|→ {host_status.get('details', '')}")
            
            self._append_status('HOST|Starting host...')
            try:
                port = int(self.port_entry.get())
            except Exception:
                port = 7777
                self._append_status(f'HOST|Invalid port, using default: {port}')
            
            # Configure host before starting
            self._gp.set_host_config(bind_ip='', port=port)
            self._gp.set_multi_gamepad(self._multi_gp_var.get())
            if self._multi_gp_var.get():
                self._append_status('HOST|Multi-Gamepad Co-op mode ENABLED (up to 4 controllers)')
                self._monitor_status_label.config(text='Multi-Gamepad: ON', fg='#22c55e')
            self._gp.start_host()
            self._host_running = True
            self.host_btn.config(text='Stop Host')
            self.host_state_label.config(text='Host: running', foreground='#228B22')
        else:
            self._append_status('HOST|Stopping host...')
            self._gp.stop_host()
            self._host_running = False
            self.host_btn.config(text='Start Host')
            self.host_state_label.config(text='Host: stopped', foreground='#b22222')

    def _toggle_client(self):
        if getattr(self, '_client_running', False) is not True:
            # --- Guard: settings must be confirmed first ---
            if not self._settings_confirmed:
                self._prompt_settings_first()
                return

            # Check if client is ready
            client_status = platform_info.get_client_status()
            if client_status['status'] == 'warning':
                self._append_status(f"CLIENT|⚠ Note: {client_status['message']}")
                self._append_status(f"CLIENT|  Will send test data (no physical gamepad)")
            
            self._append_status('CLIENT|Starting client...')
            target_ip = self.ip_entry.get().strip()
            if not target_ip:
                target_ip = '127.0.0.1'
                self._append_status(f'CLIENT|No IP provided, using default: {target_ip}')
            
            try:
                port = int(self.port_entry.get())
            except Exception:
                port = 7777
                self._append_status(f'CLIENT|Invalid port, using default: {port}')
            
            # Configure client before starting
            self._gp.set_client_target(target_ip, port)
            self._gp.start_client()
            self._client_running = True
            self.client_btn.config(text='Stop Client')
            self.client_state_label.config(text='Client: running', foreground='#228B22')
        else:
            self._append_status('CLIENT|Stopping client...')
            self._gp.stop_client()
            self._client_running = False
            self.client_btn.config(text='Start Client')
            self.client_state_label.config(text='Client: stopped', foreground='#b22222')

    def _clear_log(self):
        try:
            self.host_box.config(state='normal')
            self.host_box.delete('1.0', 'end')
            self.host_box.config(state='disabled')
            self.client_box.config(state='normal')
            self.client_box.delete('1.0', 'end')
            self.client_box.config(state='disabled')
        except Exception:
            pass
    
    def _show_platform_help(self):
        """Show platform-specific help dialog."""
        help_window = tk.Toplevel(self)
        help_window.title("Platform Setup Help")
        help_window.geometry("700x600")
        help_window.transient(self)
        
        # Create scrollable text widget
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        help_text = tk.Text(text_frame, wrap='word', font=(None, 10),
                           yscrollcommand=scrollbar.set, bg='#1a1d1f', fg='#e5e7eb')
        help_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=help_text.yview)
        
        # Build help content
        platform_name = platform_info.get_platform_name()
        host_status = platform_info.get_host_status()
        client_status = platform_info.get_client_status()
        setup_instructions = platform_info.get_setup_instructions()
        
        help_content = f"""═══════════════════════════════════════════════════════
CooPad Platform Setup Help - {platform_name}
═══════════════════════════════════════════════════════

CURRENT STATUS:
───────────────────────────────────────────────────────

Host Mode: {host_status['icon']} {host_status['status'].upper()}
{host_status['message']}
{host_status.get('details', '')}

Client Mode: {client_status['icon']} {client_status['status'].upper()}
{client_status['message']}
{client_status.get('details', '')}

═══════════════════════════════════════════════════════
SETUP INSTRUCTIONS
═══════════════════════════════════════════════════════

HOST MODE SETUP:
"""
        for instruction in setup_instructions['host']:
            help_content += f"  {instruction}\n"
        
        help_content += "\nCLIENT MODE SETUP:\n"
        for instruction in setup_instructions['client']:
            help_content += f"  {instruction}\n"
        
        help_content += """
═══════════════════════════════════════════════════════
CROSS-PLATFORM COMPATIBILITY
═══════════════════════════════════════════════════════

✓ SUPPORTED CONFIGURATIONS:
  • Windows Host ↔ Windows Client

📡 NETWORK REQUIREMENTS:
  • Both devices on same local network (LAN)
  • OR connected via VPN (ZeroTier, Tailscale, etc.)
  • UDP port 7777 must be accessible
  • Firewall may need to allow Python/CooPad

🎮 HOW IT WORKS:
  1. Client captures gamepad input (or sends test data)
  2. Input is sent as UDP packets to Host
  3. Host receives packets and creates virtual gamepad
  4. Games see the virtual gamepad as real hardware

⚠️ COMMON ISSUES:
"""
        
        # Add platform-specific issues
        if host_status.get('action'):
            help_content += f"\n  HOST: {host_status['action']}\n"
        if client_status.get('action'):
            help_content += f"\n  CLIENT: {client_status['action']}\n"
        
        help_content += """
═══════════════════════════════════════════════════════
TROUBLESHOOTING
═══════════════════════════════════════════════════════

Cannot start Host:
  → Check status indicators above
  → Install required virtual gamepad driver
  → Run with appropriate permissions

Cannot connect Client to Host:
  → Verify both are on same network
  → Check IP address is correct
  → Disable firewall temporarily to test
  → Try localhost (127.0.0.1) for same-machine test

No gamepad detected:
  → Install pygame: pip install pygame
  → Connect USB gamepad
  → Client can still run without gamepad (sends test data)

═══════════════════════════════════════════════════════
For more information, see README.md
═══════════════════════════════════════════════════════
"""
        
        help_text.insert('1.0', help_content)
        help_text.config(state='disabled')
        
        # Close button
        ttk.Button(help_window, text='Close', 
                  command=help_window.destroy).pack(pady=(0,20))
    
    # ---------- Settings helpers ----------

    def _confirm_settings(self):
        """User explicitly confirms their settings - persist and unlock Host/Client."""
        rate = self.update_rate_var.get()
        display_name = self.controller_profile_var.get()
        multi_gp = self._multi_gp_var.get()

        # Apply to backend
        self._gp.set_update_rate(rate)
        self._gp.set_multi_gamepad(multi_gp)
        try:
            from gp.core.controller_profiles import get_profile_by_display_name
            profile_key = get_profile_by_display_name(display_name)
        except Exception:
            profile_key = 'generic'
        self._gp.set_controller_profile(profile_key)

        # Persist
        self._settings_confirmed = True
        self._config['settings_confirmed'] = True
        self._config['update_rate'] = rate
        self._config['controller_profile'] = profile_key
        self._config['controller_profile_display'] = display_name
        self._config['multi_gamepad'] = multi_gp
        save_config(self._config)

        # Update UI feedback
        self._settings_status_var.set('✓ Settings saved – ready to play!')
        self._settings_status_label.config(fg='#22c55e')
        self._confirm_btn.config(text='  ✓  Settings Saved  ', bg='#1a6b2e')

        # Update monitor status
        if multi_gp:
            self._monitor_status_label.config(text='Multi-Gamepad: ON', fg='#22c55e')
        else:
            self._monitor_status_label.config(text='Multi-Gamepad: OFF', fg='#888888')

        self._append_status(f'Settings confirmed \u2192 {rate} Hz / {display_name} / Multi-Gamepad: {"ON" if multi_gp else "OFF"}')

    def _prompt_settings_first(self):
        """Show a dialog telling the user to configure settings first."""
        answer = messagebox.askyesno(
            'Settings Required',
            'You haven\'t confirmed your settings yet.\n\n'
            'For the best experience, please go to the Settings tab first '
            'and select your controller profile and update rate, then click '
            '"Confirm Settings & Save".\n\n'
            'Open the Settings tab now?',
            icon='warning'
        )
        if answer:
            self._show_tab('Settings')

    def _on_rate_change(self):
        """Handle update rate change."""
        rate = self.update_rate_var.get()
        self._gp.set_update_rate(rate)
        self._append_status(f'CLIENT|Update rate changed to {rate} Hz')
    
    def _on_controller_change(self, event=None):
        """Handle controller profile change."""
        display_name = self.controller_profile_var.get()
        # Convert display name to profile key
        try:
            from gp.core.controller_profiles import get_profile_by_display_name
            profile_key = get_profile_by_display_name(display_name)
            self._gp.set_controller_profile(profile_key)
            self._append_status(f'CLIENT|Controller profile changed to {display_name}')
        except Exception as e:
            self._append_status(f'CLIENT|Error changing controller profile: {e}')

    # =====================  Multi-Gamepad Co-op  =====================

    def _on_multi_gamepad_toggle(self):
        """Called when the multi-gamepad checkbox is clicked."""
        enabled = self._multi_gp_var.get()
        if enabled:
            # Show confirmation dialog
            answer = messagebox.askyesno(
                'Enable Multi-Gamepad Co-op',
                'Are you sure you want to enable Multi-Gamepad Co-op mode?\n\n'
                'This will have the following effects:\n\n'
                '\u2022 The Host will create up to 4 separate virtual Xbox 360\n'
                '   controllers (one per connected client).\n\n'
                '\u2022 Each remote player\u2019s inputs will be routed to their own\n'
                '   virtual controller, so inputs never mix between players.\n\n'
                '\u2022 The Host machine must also have this option enabled.\n'
                '   Both sides need to confirm settings before starting.\n\n'
                '\u2022 Windows XInput supports a maximum of 4 controllers.\n\n'
                '\u2022 ViGEmBus driver must be installed on the Host machine.\n\n'
                'Continue?',
                icon='warning'
            )
            if not answer:
                self._multi_gp_var.set(False)
                return
            self._multi_gp_status.config(text='Enabled', fg='#22c55e')
            self._gp.set_multi_gamepad(True)
            self._monitor_status_label.config(text='Multi-Gamepad: ON', fg='#22c55e')
            self._append_status('HOST|Multi-Gamepad Co-op mode enabled')
        else:
            self._multi_gp_status.config(text='Disabled', fg='#888888')
            self._gp.set_multi_gamepad(False)
            self._monitor_status_label.config(text='Multi-Gamepad: OFF', fg='#888888')
            self._append_status('HOST|Multi-Gamepad Co-op mode disabled')

    # =====================  Player Card Management  =====================

    def _handle_player_join(self, raw: str):
        """Handle PLAYER_JOIN|client_id|name|color|slot telemetry."""
        try:
            parts = raw.split('|')
            # PLAYER_JOIN|client_id|name|color|slot
            cid = int(parts[1])
            name = parts[2]
            color = parts[3]
            slot = int(parts[4])
            self._create_player_card(cid, name, color, slot)
            self._log_monitor_event(f'\u25b6 Player {slot} "{name}" connected', color)
        except Exception:
            pass

    def _handle_player_leave(self, raw: str):
        """Handle PLAYER_LEAVE|client_id|name|color|slot telemetry."""
        try:
            parts = raw.split('|')
            cid = int(parts[1])
            name = parts[2]
            color = parts[3]
            slot = int(parts[4])
            self._remove_player_card(cid)
            self._log_monitor_event(f'\u25a0 Player {slot} "{name}" disconnected', '#888888')
        except Exception:
            pass

    def _handle_player_stats(self, raw: str):
        """Handle PLAYER_STATS|client_id|name|color|slot|latency|jitter|rate|seq."""
        try:
            parts = raw.split('|')
            cid = int(parts[1])
            name = parts[2]
            color = parts[3]
            slot = int(parts[4])
            latency = parts[5]
            jitter = parts[6]
            rate = parts[7]
            seq = parts[8]
            self._update_player_card(cid, name, color, slot, latency, jitter, rate, seq)
        except Exception:
            pass

    def _create_player_card(self, cid: int, name: str, color: str, slot: int):
        """Create a player card widget in the Monitor tab."""
        if cid in self._player_cards:
            return
        # Hide the empty label
        try:
            self._monitor_empty_label.pack_forget()
        except Exception:
            pass

        card = tk.Frame(self._monitor_cards_frame, bg='#1a1d1f', relief='flat',
                        highlightbackground=color, highlightthickness=2, padx=16, pady=12)
        card.pack(fill='x', padx=16, pady=8)

        # Row 1: colored circle + name + slot badge
        top_row = tk.Frame(card, bg='#1a1d1f')
        top_row.pack(fill='x')

        # Colored dot
        dot = tk.Canvas(top_row, width=16, height=16, bg='#1a1d1f', highlightthickness=0)
        dot.create_oval(2, 2, 14, 14, fill=color, outline=color)
        dot.pack(side='left', padx=(0, 8))

        name_lbl = tk.Label(top_row, text=name, font=('Segoe UI', 13, 'bold'),
                            fg=color, bg='#1a1d1f')
        name_lbl.pack(side='left')

        slot_badge = tk.Label(top_row, text=f'  PLAYER {slot}  ', font=('Segoe UI', 8, 'bold'),
                              fg='#000000', bg=color, relief='flat')
        slot_badge.pack(side='right', padx=(8, 0))

        # Row 2: stats
        stats_row = tk.Frame(card, bg='#1a1d1f')
        stats_row.pack(fill='x', pady=(8, 0))

        lat_lbl = tk.Label(stats_row, text='Latency: \u2014', font=('Consolas', 10),
                           fg='#aaaaaa', bg='#1a1d1f')
        lat_lbl.pack(side='left', padx=(0, 20))

        jit_lbl = tk.Label(stats_row, text='Jitter: \u2014', font=('Consolas', 10),
                           fg='#aaaaaa', bg='#1a1d1f')
        jit_lbl.pack(side='left', padx=(0, 20))

        rate_lbl = tk.Label(stats_row, text='Rate: \u2014', font=('Consolas', 10),
                            fg='#aaaaaa', bg='#1a1d1f')
        rate_lbl.pack(side='left', padx=(0, 20))

        seq_lbl = tk.Label(stats_row, text='Seq: \u2014', font=('Consolas', 10),
                           fg='#666666', bg='#1a1d1f')
        seq_lbl.pack(side='right')

        self._player_cards[cid] = {
            'frame': card,
            'name_lbl': name_lbl,
            'lat_lbl': lat_lbl,
            'jit_lbl': jit_lbl,
            'rate_lbl': rate_lbl,
            'seq_lbl': seq_lbl,
            'slot_badge': slot_badge,
            'color': color,
        }

    def _update_player_card(self, cid: int, name: str, color: str, slot: int,
                            latency: str, jitter: str, rate: str, seq: str):
        """Update an existing player card with new stats."""
        if cid not in self._player_cards:
            self._create_player_card(cid, name, color, slot)
        card = self._player_cards.get(cid)
        if card is None:
            return
        try:
            lat_f = float(latency)
            # Color-code latency
            if lat_f < 10:
                lat_color = '#22c55e'  # green
            elif lat_f < 30:
                lat_color = '#f59e0b'  # amber
            else:
                lat_color = '#ef4444'  # red
            card['lat_lbl'].config(text=f'Latency: {latency} ms', fg=lat_color)
            card['jit_lbl'].config(text=f'Jitter: {jitter} ms')
            rate_f = float(rate)
            if rate_f > 0:
                card['rate_lbl'].config(text=f'Rate: {rate} Hz')
            card['seq_lbl'].config(text=f'Seq: {seq}')
        except Exception:
            pass

    def _remove_player_card(self, cid: int):
        """Remove a player card from the Monitor tab."""
        card = self._player_cards.pop(cid, None)
        if card is not None:
            try:
                card['frame'].destroy()
            except Exception:
                pass
        # Show empty label if no players left
        if not self._player_cards:
            try:
                self._monitor_empty_label.pack(expand=True, pady=80)
            except Exception:
                pass

    def _log_monitor_event(self, text: str, color: str = '#aaaaaa'):
        """Append a line to the monitor event log."""
        try:
            import time as _t
            ts = _t.strftime('%H:%M:%S')
            self._monitor_log.config(state='normal')
            tag_name = f'c_{color.replace("#", "")}'
            self._monitor_log.tag_configure(tag_name, foreground=color)
            self._monitor_log.insert('end', f'[{ts}] {text}\n', tag_name)
            self._monitor_log.see('end')
            self._monitor_log.config(state='disabled')
        except Exception:
            pass


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
