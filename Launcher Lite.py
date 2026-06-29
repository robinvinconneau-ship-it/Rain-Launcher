import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import sys
import hashlib
import time
from PIL import Image, ImageTk, ImageDraw

DATA_FILE = os.path.join(os.path.expanduser("~"), ".rains_games.json")
ICON_CACHE = os.path.join(os.path.expanduser("~"), ".rains_icons")
os.makedirs(ICON_CACHE, exist_ok=True)

BG = "#07090f"
BG2 = "#0c1018"
BG3 = "#111827"

CARD = "#0f1624"
CARD2 = "#162238"

ACCENT = "#1d3e7c"
ACCENT_HOVER = "#112453"

TEXT = "#e6edf7"
TEXT2 = "#9aa4b2"
TEXT3 = "#6b7280"

DANGER = "#e55353"



def hash_key(s):
    return hashlib.md5(s.encode()).hexdigest()

def load_games():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_games(games):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
def make_placeholder_icon(name):
    size = 128
    key = hash_key(name)
    path = os.path.join(ICON_CACHE, f"ph_{key}.png")
    if os.path.exists(path):
        return path
    img = Image.new("RGBA", (size, size), (18, 22, 35, 255))
    draw = ImageDraw.Draw(img)

    initials = "".join(w[0].upper() for w in name.split()[:2]) or "?"
    draw.text((50, 55), initials, fill=(230, 237, 247, 255))
    img.save(path)
    return path

def load_tk_image(path, size):
    try:
        img = Image.open(path).convert("RGBA")
        img = img.resize((size, size))
        return ImageTk.PhotoImage(img)
    except:
        return None
class GameCard(tk.Frame):
    def __init__(self, parent, game, on_launch, on_delete):
        super().__init__(parent, bg=CARD, highlightthickness=0)

        self.game = game
        self.on_launch = on_launch
        self.on_delete = on_delete

        self.configure(width=180, height=240)
        self.pack_propagate(False)
        self._build()
        self._bind_hover()
    def _build(self):

        icon_path = self.game.get("icon") or make_placeholder_icon(self.game["name"])
        self.game["icon"] = icon_path
        img = load_tk_image(icon_path, 84)
        lbl = tk.Label(self, image=img, bg=CARD, cursor="hand2")
        lbl.image = img
        lbl.pack(pady=(14, 6))
        lbl.bind("<Button-1>", lambda e: self.on_launch(self.game))
        tk.Label(
            self,
            text=self.game["name"],
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 10, "bold"),
            wraplength=150
        ).pack()
        tk.Label(
            self,
            text=os.path.basename(self.game.get("path", "")),
            bg=CARD,
            fg=TEXT3,
            font=("Segoe UI", 7)
        ).pack(pady=(2, 8))
        bar = tk.Frame(self, bg=CARD)
        bar.pack(fill="x", padx=10)
        tk.Button(
            bar,
            text="▶",
            bg=ACCENT,
            fg="black",
            relief="flat",
            cursor="hand2",
            command=lambda: self.on_launch(self.game)
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            bar,
            text="✕",
            bg=DANGER,
            fg="white",
            relief="flat",
            cursor="hand2",
            width=3,
            command=lambda: self.on_delete(self.game)
        ).pack(side="right")
    def _bind_hover(self):
        self.bind("<Enter>", self._hover_on)
        self.bind("<Leave>", self._hover_off)
        for c in self.winfo_children():
            c.bind("<Enter>", self._hover_on)
            c.bind("<Leave>", self._hover_off)
    def _hover_on(self, e):
        self.config(bg=CARD2)
    def _hover_off(self, e):
        self.config(bg=CARD)
class ScrollableGrid(tk.Frame):
    def __init__(self, parent, cols=4):
        super().__init__(parent, bg=BG)
        self.cols = cols
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")
        self.inner.bind("<Configure>", self._update_scroll)
    def _update_scroll(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def rebuild(self, games, on_launch, on_delete):
        for w in self.inner.winfo_children():
            w.destroy()
        if not games:
            tk.Label(self.inner, text="Aucun jeu", bg=BG, fg=TEXT3).pack(pady=50)
            return
        for i, g in enumerate(games):
            card = GameCard(self.inner, g, on_launch, on_delete)
            row = i // self.cols
            col = i % self.cols
            self.inner.after(i * 35, lambda c=card, r=row, co=col:
                c.grid(row=r, column=co, padx=10, pady=10)
            )

class AddGameDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save

        self.title("Ajouter un jeu")
        self.geometry("420x260")
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.grab_set()
        self.name = tk.StringVar()
        self.path = tk.StringVar()

        tk.Label(self, text="Ajouter un jeu", bg=BG2, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        tk.Entry(self, textvariable=self.name).pack(fill="x", padx=20, pady=5)
        tk.Entry(self, textvariable=self.path).pack(fill="x", padx=20, pady=5)
        tk.Button(self, text="Parcourir", command=self._browse).pack(pady=5)
        tk.Button(
            self,
            text="Ajouter",
            bg=ACCENT,
            fg="black",
            relief="flat",
            command=self._save
        ).pack(pady=10)

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("EXE", "*.exe")])
        if path:
            self.path.set(path)
            if not self.name.get():
                self.name.set(os.path.splitext(os.path.basename(path))[0])
    def _save(self):
        if not self.name.get() or not self.path.get():
            return
        self.on_save({
            "name": self.name.get(),
            "path": self.path.get(),
            "icon": make_placeholder_icon(self.name.get())
        })
        self.destroy()

class RainsLauncher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Rain's Launcher Lite")
        self.geometry("1180x760")
        self.minsize(1000, 650)
        self.configure(bg=BG)
        self.attributes("-alpha", 0.0)
        self.after(0, self.fade_in)

        self.games = []
        self.build_ui()
        self.after(100, self.load)
    def fade_in(self):
        a = self.attributes("-alpha")
        if a < 1:
            self.attributes("-alpha", a + 0.05)
            self.after(12, self.fade_in)
    def build_ui(self):
        self.topbar = tk.Frame(self, bg=BG3, height=60)
        self.topbar.pack(side="top", fill="x")
        tk.Label(
            self.topbar,
            text="Rain's Launcher Lite v1",
            bg=BG3,
            fg=TEXT,
            font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=18)
        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(self.container, bg=BG2, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.main = tk.Frame(self.container, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        self.grid_frame = tk.Frame(self.main, bg=BG)
        self.grid_frame.pack(fill="both", expand=True)
        self.grid = ScrollableGrid(self.grid_frame, cols=4)
        self.grid.pack(fill="both", expand=True)

        btn = tk.Button(
            self.sidebar,
            text="＋ Ajouter un jeu",
            bg=ACCENT,
            fg="black",
            relief="flat",
            cursor="hand2",
            command=self.add_game
        )
        btn.pack(pady=20, padx=12, fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=ACCENT))

    def load(self):
        self.games = load_games()
        self.refresh()
    def refresh(self):
        self.grid.rebuild(self.games, self.launch, self.delete)

    def add_game(self):
        AddGameDialog(self, self.save_game)
    def save_game(self, game):
        self.games.append(game)
        save_games(self.games)
        self.refresh()
    def delete(self, game):
        self.games = [g for g in self.games if g != game]
        save_games(self.games)
        self.refresh()
    def launch(self, game):
        path = game.get("path")
        if not path or not os.path.exists(path):
            messagebox.showerror("Erreur", "Fichier introuvable")
            return
        try:
            subprocess.Popen(path, cwd=os.path.dirname(path))
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
if __name__ == "__main__":
    app = RainsLauncher()
    app.mainloop()