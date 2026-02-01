import os
import sys
import threading
import time
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    print("Error: tkinter is not installed. Please install it using 'sudo apt-get install python3-tk' on Linux.")
    sys.exit(1)


from PIL import Image, ImageOps, ImageTk
from gp_backend import GpController
import socket
from queue import Queue
import logging


# Global queue for input states
input_queue = Queue()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CooPad — Remote Gamepad")
        self.geometry("980x620")

        # icon - handle cross-platform icon loading
        base = os.path.dirname(__file__)
        try:
            if sys.platform == 'win32':
                # Windows can use .ico files directly
                ico_path = os.path.join(base, "img", "src_CooPad.ico")
                if os.path.exists(ico_path):
                    self.wm_iconbitmap(ico_path)
            else:
                # Linux/Unix - use PNG with iconphoto
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

        ttk.Button(left, text='Clear Logs', command=self._clear_log).pack(fill='x', pady=(6,12), padx=12)

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

        # english notice
        notice_text = (
            'Note: Host and Client must be on the same local network. '
            'If you are on different networks, create a secure virtual LAN (e.g., ZeroTier, Tailscale) '
            'and use the Host IP from that network.'
        )
        notice = ttk.Label(right, text=notice_text, wraplength=760, justify='left')
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

        # content frames
        tabs_frame = ttk.Frame(right)
        tabs_frame.pack(fill='both', expand=True, padx=12, pady=(0,0))
        host_tab = ttk.Frame(tabs_frame)
        client_tab = ttk.Frame(tabs_frame)
        self._content_frames = {'Host': host_tab, 'Client': client_tab}

        # Host content
        ttk.Label(host_tab, text='Host Status', font=(None, 12, 'bold')).pack(anchor='nw', padx=8, pady=(8,4))
        self.host_latency_var = tk.StringVar(value='Latency: — ms')
        ttk.Label(host_tab, textvariable=self.host_latency_var).pack(anchor='nw', padx=8, pady=4)
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
        self.client_packets_var = tk.StringVar(value='Packets: —')
        ttk.Label(client_tab, textvariable=self.client_packets_var).pack(anchor='nw', padx=8, pady=4)
        ttk.Label(client_tab, text='Client Log', anchor='w').pack(fill='x', padx=8, pady=(8,0))
        self.client_box = tk.Text(client_tab, wrap='word', height=10, font=self._mono_font)
        self.client_box.pack(fill='both', expand=True, padx=8, pady=8)
        self.client_box.config(state='disabled')

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
            # dark palette
            pal = {
                'bg': '#0d0f10',
                'frame': '#111214',
                'panel': '#151617',
                'text_bg': '#0b0b0b',
                'text_fg': '#e6e6e6',
                'entry_bg': '#1a1c1d',
                'button_bg': '#2a7bd6',
                'accent': '#2a7bd6'
            }
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
                if 'Latency' in t:
                    parts = t.split('|')
                    self.host_latency_var.set(parts[0].strip())
                    import re
                    if len(parts) > 1:
                        m = re.search(r'seq=(\d+)', parts[1])
                        if m:
                            self.host_packets_var.set(f'Packets: {m.group(1)}')
                else:
                    self.host_latency_var.set(t)
            elif text.startswith('CLIENT|'):
                t = text.split('|', 1)[1].strip()
                if 'Latency' in t:
                    parts = t.split('|')
                    self.client_latency_var.set(parts[0].strip())
                    import re
                    if len(parts) > 1:
                        m = re.search(r'seq=(\d+)', parts[1])
                        if m:
                            self.client_packets_var.set(f'Packets: {m.group(1)}')
                else:
                    self.client_latency_var.set(t)
            else:
                self._footer_label.config(text=text)
        except Exception:
            pass

    def _toggle_host(self):
        if getattr(self, '_host_running', False) is not True:
            self._append_status('Requesting host start...')
            try:
                _ = int(self.port_entry.get())
            except Exception:
                pass
            # GpController start_host has no parameters — call directly
            self._gp.start_host()
            self._host_running = True
            self.host_btn.config(text='Stop Host')
            self.host_state_label.config(text='Host: running', foreground='#228B22')
        else:
            self._append_status('Stopping host...')
            self._gp.stop_host()
            self._host_running = False
            self.host_btn.config(text='Start Host')
            self.host_state_label.config(text='Host: stopped', foreground='#b22222')

    def _toggle_client(self):
        if getattr(self, '_client_running', False) is not True:
            self._append_status('Requesting client start...')
            target = self.ip_entry.get()
            try:
                _ = int(self.port_entry.get())
            except Exception:
                pass
            # GpController start_client has no parameters — call directly
            self._gp.start_client()
            self._client_running = True
            self.client_btn.config(text='Stop Client')
            self.client_state_label.config(text='Client: running', foreground='#228B22')
        else:
            self._append_status('Stopping client...')
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


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
