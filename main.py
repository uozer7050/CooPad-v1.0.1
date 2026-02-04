import os
import sys
import threading
import time
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    print("Error: tkinter is not installed. Please install it for your platform.")
    sys.exit(1)


from PIL import Image, ImageOps, ImageTk
from gp_backend import GpController
from platform_info import get_platform_info
import socket
from queue import Queue
import logging


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
        make_tab_button('Settings')

        # content frames
        tabs_frame = ttk.Frame(right)
        tabs_frame.pack(fill='both', expand=True, padx=12, pady=(0,0))
        host_tab = ttk.Frame(tabs_frame)
        client_tab = ttk.Frame(tabs_frame)
        settings_tab = ttk.Frame(tabs_frame)
        self._content_frames = {'Host': host_tab, 'Client': client_tab, 'Settings': settings_tab}

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

        # Settings content
        ttk.Label(settings_tab, text='Network Settings', font=(None, 12, 'bold')).pack(anchor='nw', padx=8, pady=(8,4))
        
        # Update rate setting
        rate_frame = ttk.Frame(settings_tab)
        rate_frame.pack(fill='x', padx=8, pady=12)
        ttk.Label(rate_frame, text='Client Update Rate:', font=(None, 10, 'bold')).pack(anchor='w', pady=(0,4))
        ttk.Label(rate_frame, text='Higher rates provide smoother gameplay but use more bandwidth.', 
                 font=(None, 9), foreground='#888888').pack(anchor='w', pady=(0,8))
        
        self.update_rate_var = tk.IntVar(value=60)
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
        
        self.controller_profile_var = tk.StringVar(value='Generic')
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
        
        # Info section
        ttk.Separator(settings_tab, orient='horizontal').pack(fill='x', padx=8, pady=12)
        
        info_frame = ttk.Frame(settings_tab)
        info_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        ttk.Label(info_frame, text='About CooPad', font=(None, 12, 'bold')).pack(anchor='w', pady=(0,8))
        
        info_text = tk.Text(info_frame, wrap='word', height=12, font=(None, 9))
        info_text.pack(fill='both', expand=True)
        info_text.insert('1.0', '''CooPad - Remote Gamepad over Network

Version: 5.1
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

        # show initial tab
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
                else:
                    self.client_controls.pack(fill='x', padx=12)
                    self.host_controls.pack_forget()
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
                # Parse telemetry: "Latency: X.Xms | Jitter: X.Xms | Rate: XXHz | seq=XXX"
                parts = [p.strip() for p in t.split('|')]
                for part in parts:
                    if part.startswith('Latency:'):
                        self.host_latency_var.set(part)
                    elif part.startswith('Jitter:'):
                        self.host_jitter_var.set(part)
                    elif part.startswith('Rate:'):
                        # Extract rate and sequence
                        rate_part = part.split('seq=')[0].strip()
                        self.host_packets_var.set(rate_part)
                        if 'seq=' in part:
                            seq = part.split('seq=')[1].strip()
                            self.host_packets_var.set(f'{rate_part} | Seq: {seq}')
            elif text.startswith('CLIENT|'):
                t = text.split('|', 1)[1].strip()
                # Parse telemetry: "Latency: X.Xms | Jitter: X.Xms | Rate: XXHz | seq=XXX"
                parts = [p.strip() for p in t.split('|')]
                for part in parts:
                    if part.startswith('Latency:'):
                        self.client_latency_var.set(part)
                    elif part.startswith('Jitter:'):
                        self.client_jitter_var.set(part)
                    elif part.startswith('Rate:'):
                        # Extract rate and sequence
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


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
