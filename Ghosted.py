import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from discord.ext import commands
from datetime import datetime
from io import BytesIO

import threading, signal, requests, asyncio, sys, discord, json, os

def get_json_path():
    if getattr(sys, 'frozen', False):
      
        return os.path.join(sys._MEIPASS, 'ghosted.json')
    else:
        
        return 'ghosted.json'


def load_config():
    try:
        json_path = get_json_path()
        with open(json_path, "r") as confjson:
            return json.load(confjson)
    except:
        return {"Token": "", "Prefix": "!"}

def save_config(token):
    config = load_config()
    if token != config["Token"]:
        config["Token"] = token
        with open("ghosted.json", "w") as outfile:
            json.dump(config, outfile, indent=4)


MrReact = commands.Bot(command_prefix="!", self_bot=True, help_command=None, status=discord.Status.do_not_disturb)

async def join_voice(guid, vcid):
    try:
        guild = MrReact.get_guild(guid)
        vc = discord.utils.get(guild.channels, id=vcid)
        await guild.change_voice_state(channel=vc, self_mute=False, self_deaf=False)
        return f"Successfully joined {vc.name} ({vc.id})"
    except Exception as e:
        return str(e)


class ModernButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(relief="flat", borderwidth=0, padx=20, pady=8, font=("Helvetica", 10), cursor="hand2")
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = '#5865f2'

    def on_leave(self, e):
        self['background'] = '#4752c4'

class ModernEntry(tk.Frame):
    def __init__(self, master, width=None, **kwargs):
        super().__init__(master, bg="#4752c4")
        if width:
            self.inner_width = width * 8
        else:
            self.inner_width = 200
        self.inner_frame = tk.Frame(self, bg="#40444b", padx=10, pady=5)
        self.inner_frame.pack(padx=1, pady=1)
        self.entry = tk.Entry(
            self.inner_frame,
            width=width,
            bg="#40444b",
            fg="#dcddde",
            insertbackground="#dcddde",
            font=("Helvetica", 10),
            relief="flat",
            **kwargs
        )
        self.entry.pack(expand=True, fill="both")
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)

    def on_focus_in(self, event):
        self.configure(bg="#5865f2")

    def on_focus_out(self, event):
        self.configure(bg="#4752c4")

    def get(self):
        return self.entry.get()

    def insert(self, index, string):
        self.entry.insert(index, string)

    def delete(self, first, last=None):
        self.entry.delete(first, last)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Ghosted")
        self.root.geometry("300x400")
        self.root.configure(bg="#36393f")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        # Create event loop
        self.loop = asyncio.new_event_loop()
        self.thread = None
        self.is_closing = False

        self.setup_title_bar()
        self.main_container = tk.Frame(root, bg="#36393f")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        self.setup_icon_and_welcome()
        self.setup_tabs()


        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_title_bar(self):

        self.title_bar = tk.Frame(self.root, bg="#202225", height=30)
        self.title_bar.pack(fill="x")
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        self.title_label = tk.Label(self.title_bar, text="Ghosted", font=("Helvetica", 10), fg="#dcddde", bg="#202225")
        self.title_label.pack(side="left", padx=10)
        self.close_button = tk.Label(self.title_bar, text="×", font=("Helvetica", 14), fg="#dcddde", bg="#202225", cursor="hand2", width=3)
        self.close_button.pack(side="right")
        self.close_button.bind("<Button-1>", self.on_closing)
        self.close_button.bind("<Enter>", lambda e: self.close_button.config(bg="#ed4245"))
        self.close_button.bind("<Leave>", lambda e: self.close_button.config(bg="#202225"))

    def signal_handler(self, signum, frame):
        self.on_closing()

    def on_closing(self, event=None):
        if self.is_closing:
            return

        self.is_closing = True


        self.disable_all_widgets()


        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.cleanup(), self.loop)

            self.root.after(1000, self.force_quit)
        else:
            self.force_quit()

    async def cleanup(self):
        try:
            if not MrReact.is_closed():
                await MrReact.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.loop.stop()

    def force_quit(self):

        if self.loop and self.loop.is_running():
            self.loop.stop()


        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)


        self.root.destroy()
        sys.exit(0)

    def disable_all_widgets(self):

        for widget in self.root.winfo_children():
            if isinstance(widget, (tk.Button, tk.Entry)):
                widget.configure(state='disabled')

    def setup_icon_and_welcome(self):
        response = requests.get("https://tlo.sh/imgs/tlo-t.png")
        image_data = Image.open(BytesIO(response.content))
        image_data = image_data.resize((100, 100), Image.LANCZOS)
        self.icon_image = ImageTk.PhotoImage(image_data)
        self.icon_label = tk.Label(self.main_container, image=self.icon_image, bg="#36393f")
        self.icon_label.pack(pady=3)
        self.welcome_label = tk.Label(self.main_container, text="Welcome, ...", font=("Helvetica", 12), bg="#36393f", fg="#dcddde")
        self.welcome_label.pack(pady=6)

    def setup_tabs(self):

        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure("TNotebook", background="#36393f", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#282b30", foreground="#dcddde", padding=[5, 2])
        self.style.map("TNotebook.Tab", background=[["selected", "#36393f"]], foreground=[["selected", "#ffffff"]])

        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill="both", expand=True)

        self.footer_label = tk.Label(self.main_container, text="© 2023-2025 Sanction ™ | All rights reserved.", 
                                   font=("Helvetica", 8), bg="#36393f", fg="#72767d")
        self.footer_label.pack(side="bottom", pady=2)

        self.create_authorize_tab()
        self.create_home_tab()

    def create_authorize_tab(self):
        self.authorize_frame = tk.Frame(self.notebook, bg="#36393f")
        self.notebook.add(self.authorize_frame, text="Authorize")

        tk.Label(self.authorize_frame, text="Enter Token", font=("Helvetica", 12), bg="#36393f", fg="#dcddde").pack(pady=3)
        self.token_entry = ModernEntry(self.authorize_frame, width=30, show="•")
        self.token_entry.pack(pady=3)

        ModernButton(self.authorize_frame, text="Login", bg="#4752c4", fg="white", width=20, command=self.login_bot).pack(pady=3)

    def create_home_tab(self):
        self.home_frame = tk.Frame(self.notebook, bg="#36393f")
        self.notebook.add(self.home_frame, text="Home")

        input_frame = tk.Frame(self.home_frame, bg="#36393f")
        input_frame.pack(pady=3, padx=5, fill="x")

        server_frame = tk.Frame(input_frame, bg="#36393f")
        server_frame.pack(fill="x", pady=5)
        tk.Label(server_frame, text="Server ID:", font=("Helvetica", 12), bg="#36393f", fg="#dcddde", width=10, anchor="w").pack(side="left", padx=5)
        self.server_entry = ModernEntry(server_frame, width=20)
        self.server_entry.pack(side="left", padx=5, fill="x", expand=True)

        channel_frame = tk.Frame(input_frame, bg="#36393f")
        channel_frame.pack(fill="x", pady=5)
        tk.Label(channel_frame, text="Channel ID:", font=("Helvetica", 12), bg="#36393f", fg="#dcddde", width=10, anchor="w").pack(side="left", padx=5)
        self.channel_entry = ModernEntry(channel_frame, width=20)
        self.channel_entry.pack(side="left", padx=5, fill="x", expand=True)

        ModernButton(self.home_frame, text="Join", bg="#4752c4", fg="white", width=20, command=self.join_voice_channel).pack(pady=3)

    def run_bot(self):
        
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        except Exception as e:
            print(f"Bot loop error: {e}")
        finally:
            self.loop.close()

    def login_bot(self):
        token = self.token_entry.get()
        if not token:
            messagebox.showerror("Error", "Please enter a token")
            return

        save_config(token)


        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run_bot, daemon=True)
            self.thread.start()

        async def start_bot():
            try:
                await MrReact.start(token)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                return

        future = asyncio.run_coroutine_threadsafe(start_bot(), self.loop)
        self.root.after(1000, self.update_welcome)

    def update_welcome(self):
        if MrReact.user:
            self.welcome_label.config(text=f"Welcome, {MrReact.user.name}")

    def join_voice_channel(self):
        server_id = self.server_entry.get()
        channel_id = self.channel_entry.get()

        if not server_id or not channel_id:
            messagebox.showerror("Error", "Please enter both Server ID and Channel ID")
            return

        try:
            server_id = int(server_id)
            channel_id = int(channel_id)

            async def do_join():
                result = await join_voice(server_id, channel_id)
                self.root.after(0, lambda: messagebox.showinfo("Success", result))

            asyncio.run_coroutine_threadsafe(do_join(), self.loop)
        except ValueError:
            messagebox.showerror("Error", "Server ID and Channel ID must be numbers")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        x = self.root.winfo_x() - self.x + event.x
        y = self.root.winfo_y() - self.y + event.y
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
