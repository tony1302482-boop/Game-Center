import json
import sys
import tkinter as tk
import threading
import urllib.request
import urllib.error
import subprocess
import tempfile
import os
import re
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

APP_NAME = "Game Center"
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "Game Center"

CONFIG_FILE = DATA_DIR / "settings.json"
GITHUB_REPO = "tony1302482-boop/Game-Center"
CURRENT_VERSION = "0.7.0"
UPDATE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

DEFAULTS = {
    "language": "Deutsch",
    "theme": "Dunkel",
    "accent": "Blau"
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Game Center")
        self.geometry("1080x700")
        self.minsize(900, 600)
        self.settings = DEFAULTS.copy()
        self.load_settings()
        self.configure(bg="#10141d")
        self._style()
        self._build()
        self.show_page("Übersicht")
        self.after(1800, lambda: self.check_for_updates(manual=False))

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#202938", background="#202938",
                        foreground="#f2f5fa", arrowcolor="#f2f5fa")
        style.map("TCombobox", fieldbackground=[("readonly", "#202938")],
                  foreground=[("readonly", "#f2f5fa")])
        style.configure("TCheckbutton", background="#19212e", foreground="#e8edf5",
                        font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", "#19212e")],
                  foreground=[("active", "#ffffff")])

    def _build(self):
        self.sidebar = tk.Frame(self, bg="#0b0f16", width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg="#0b0f16")
        brand.pack(fill="x", padx=22, pady=(26, 30))
        tk.Label(brand, text="Game Center", font=("Segoe UI", 20, "bold"),
                 fg="#55a6ff", bg="#0b0f16").pack(anchor="w")
        tk.Label(brand, text="Version 0.1.0", font=("Segoe UI", 8),
                 fg="#7e8a9d", bg="#0b0f16").pack(anchor="w", pady=(5, 0))

        self.nav_buttons = {}
        for label, icon in [("Übersicht", "⌂"), ("Einstellungen", "⚙"),
                            ("Über das Programm", "ⓘ")]:
            b = tk.Button(self.sidebar, text=f"   {icon}   {label}", anchor="w",
                          font=("Segoe UI", 10), bd=0, relief="flat",
                          bg="#0b0f16", fg="#aeb9c9", activebackground="#1c2d43",
                          activeforeground="white", padx=14, pady=13,
                          command=lambda x=label: self.show_page(x))
            b.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[label] = b

        tk.Label(self.sidebar, text="GAME CENTER  •  LOCAL", font=("Segoe UI", 8),
                 fg="#596579", bg="#0b0f16").pack(side="bottom", pady=20)

        self.main = tk.Frame(self, bg="#10141d")
        self.main.pack(side="right", fill="both", expand=True)
        self.header = tk.Frame(self.main, bg="#10141d")
        self.header.pack(fill="x", padx=34, pady=(28, 18))
        self.page_title = tk.Label(self.header, text="", font=("Segoe UI", 22, "bold"),
                                   fg="#f4f7fb", bg="#10141d")
        self.page_title.pack(anchor="w")
        self.page_subtitle = tk.Label(self.header, text="", font=("Segoe UI", 10),
                                      fg="#8d9aaf", bg="#10141d")
        self.page_subtitle.pack(anchor="w", pady=(5, 0))
        self.content = tk.Frame(self.main, bg="#10141d")
        self.content.pack(fill="both", expand=True, padx=34, pady=(0, 22))
        self.footer = tk.Frame(self.main, bg="#10141d")
        self.footer.pack(fill="x", padx=34, pady=(0, 22))
        self.status = tk.Label(self.footer, text="Bereit", bg="#10141d",
                               fg="#7f8da2", font=("Segoe UI", 9))
        self.status.pack(side="left")

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()
        for w in self.footer.winfo_children():
            if w is not self.status:
                w.destroy()

    def show_page(self, page):
        self.clear_content()
        for name, btn in self.nav_buttons.items():
            btn.configure(bg="#1b2a3d" if name == page else "#0b0f16",
                          fg="#ffffff" if name == page else "#aeb9c9")
        if page == "Einstellungen":
            self.page_title.configure(text="Einstellungen")
            self.page_subtitle.configure(text="Passe das TB Builder Control Center an deine Arbeitsweise an.")
            self.build_settings()
        elif page == "Übersicht":
            self.page_title.configure(text="Willkommen")
            self.page_subtitle.configure(text="")
            # Bewusst reduzierte Übersicht – zusätzliche Kacheln wurden entfernt.
        else:
            self.page_title.configure(text="Über Game Center")
            self.page_subtitle.configure(text="Informationen zur aktuellen Version und Updates.")
            self.info_card("Game Center", f"Version {CURRENT_VERSION}\\nGaming Launcher für Windows.")
            self.info_card("Updates über GitHub", "Mit dem Update-Button kannst du nach einer neuen Version suchen und sie direkt von GitHub herunterladen.")
            self.update_status = tk.Label(self.content, text="Update-Status: Noch nicht geprüft",
                                          bg="#10141d", fg="#8d9aaf", font=("Segoe UI", 9))
            self.update_status.pack(anchor="w", pady=(4, 10))
            update_button = tk.Button(
                self.content, text="Update", command=lambda: self.check_for_updates(manual=True),
                bg="#1676d2", fg="white", activebackground="#2389ed",
                activeforeground="white", bd=0, padx=24, pady=11,
                font=("Segoe UI", 10, "bold"), cursor="hand2"
            )
            update_button.pack(anchor="w", pady=(0, 14))
            self.info_card("GitHub-Repository", f"https://github.com/{GITHUB_REPO}/releases")
            self.info_card("Datenspeicherung", f"Konfigurationsdatei:\\n{CONFIG_FILE}")

    def info_card(self, title, body):
        card = tk.Frame(self.content, bg="#19212e", padx=22, pady=18)
        card.pack(fill="x", pady=8)
        tk.Label(card, text=title, bg="#19212e", fg="#55a6ff",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(card, text=body, bg="#19212e", fg="#dce4ef",
                 font=("Segoe UI", 10), justify="left", wraplength=700).pack(anchor="w", pady=(8, 0))

    def section(self, title, description=None):
        box = tk.Frame(self.content, bg="#19212e", padx=20, pady=16)
        box.pack(fill="x", pady=(0, 12))
        tk.Label(box, text=title, bg="#19212e", fg="#55a6ff",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        if description:
            tk.Label(box, text=description, bg="#19212e", fg="#8d9aaf",
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 10))
        return box

    def field(self, parent, label, variable, values):
        row = tk.Frame(parent, bg="#19212e")
        row.pack(fill="x", pady=5)
        tk.Label(row, text=label, bg="#19212e", fg="#e8edf5",
                 font=("Segoe UI", 10), width=24, anchor="w").pack(side="left")
        cb = ttk.Combobox(row, textvariable=variable, values=values,
                          state="readonly", width=28)
        cb.pack(side="left")
        return cb

    def check(self, parent, label, variable):
        ttk.Checkbutton(parent, text=label, variable=variable).pack(anchor="w", pady=6)

    def build_settings(self):
        # Scrollable settings area
        canvas = tk.Canvas(self.content, bg="#10141d", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#10141d")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=760)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        old = self.content
        self.content = inner

        self.vars = {}
        for key in ["language", "theme", "accent"]:
            self.vars[key] = tk.StringVar(value=self.settings[key])

        box = self.section("Allgemein", "Sprache und Verhalten der Anwendung.")
        self.field(box, "Sprache", self.vars["language"], ["Deutsch", "English"])

        box = self.section("Darstellung", "Lege das Aussehen der Oberfläche fest.")
        self.field(box, "Farbschema", self.vars["theme"], ["Dunkel", "Hell"])
        self.field(box, "Akzentfarbe", self.vars["accent"], ["Blau", "Grün", "Violett"])

        self.content = old
        actions = tk.Frame(self.footer, bg="#10141d")
        actions.pack(side="right")
        tk.Button(actions, text="Auf Standard zurücksetzen", command=self.reset_settings,
                  bg="#273243", fg="#e8edf5", bd=0, padx=15, pady=10).pack(side="left", padx=6)
        tk.Button(actions, text="Einstellungen speichern", command=self.save_settings,
                  bg="#1676d2", fg="white", activebackground="#2389ed",
                  bd=0, padx=18, pady=10, font=("Segoe UI", 9, "bold")).pack(side="left", padx=6)

    def save_settings(self):
        for key, var in self.vars.items():
            self.settings[key] = var.get()
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps(self.settings, indent=2, ensure_ascii=False), encoding="utf-8")
            self.status.configure(text=f"Einstellungen gespeichert: {CONFIG_FILE}")
            messagebox.showinfo("Gespeichert", "Deine Einstellungen wurden erfolgreich gespeichert.")
        except Exception as exc:
            messagebox.showerror("Fehler", f"Einstellungen konnten nicht gespeichert werden:\n{exc}")

    def reset_settings(self):
        if messagebox.askyesno("Zurücksetzen", "Alle Einstellungen auf Standardwerte zurücksetzen?"):
            self.settings = DEFAULTS.copy()
            self.show_page("Einstellungen")
            self.status.configure(text="Standardwerte geladen – noch nicht gespeichert.")


    def check_for_updates(self, manual=False):
        if hasattr(self, "_update_check_running") and self._update_check_running:
            return
        self._update_check_running = True
        if hasattr(self, "update_status") and self.update_status.winfo_exists():
            self.update_status.configure(text="Update-Status: Suche auf GitHub …")
        def worker():
            try:
                request = urllib.request.Request(
                    UPDATE_API,
                    headers={"Accept": "application/vnd.github+json",
                             "User-Agent": "Game-Center-Updater"}
                )
                with urllib.request.urlopen(request, timeout=12) as response:
                    release = json.loads(response.read().decode("utf-8"))
                tag = str(release.get("tag_name", "")).strip().lstrip("vV")
                if not tag:
                    raise ValueError("Das GitHub-Release hat keinen Versions-Tag.")
                latest = tuple(int(x) for x in re.findall(r"\d+", tag)[:3])
                current = tuple(int(x) for x in re.findall(r"\d+", CURRENT_VERSION)[:3])
                if latest > current:
                    assets = release.get("assets", [])
                    exe_asset = next((a for a in assets if a.get("name", "").lower().endswith(".exe")), None)
                    if not exe_asset:
                        result = ("available_no_asset", tag, release.get("html_url", ""))
                    else:
                        result = ("available", tag, exe_asset.get("browser_download_url", ""))
                else:
                    result = ("current", tag, "")
            except Exception as exc:
                result = ("error", str(exc), "")
            self.after(0, lambda: self._finish_update_check(result, manual))
        threading.Thread(target=worker, daemon=True).start()

    def _finish_update_check(self, result, manual):
        self._update_check_running = False
        status, value, url = result
        has_status_label = hasattr(self, "update_status") and self.update_status.winfo_exists()
        if status == "current":
            if has_status_label:
                self.update_status.configure(text=f"Update-Status: Aktuell (GitHub: {value})")
            if manual:
                messagebox.showinfo("Game Center", "Du verwendest bereits die aktuelle Version.")
        elif status == "available":
            if has_status_label:
                self.update_status.configure(text=f"Update-Status: Neue Version {value} verfügbar")
            if messagebox.askyesno("Update verfügbar",
                                   f"Version {value} ist verfügbar. Jetzt herunterladen und installieren?"):
                self._download_and_install(url, value)
        elif status == "available_no_asset":
            if has_status_label:
                self.update_status.configure(text=f"Update-Status: Version {value} verfügbar, aber keine EXE angehängt")
            if manual and url:
                messagebox.showinfo("Update verfügbar",
                                    f"Version {value} wurde veröffentlicht, enthält aber noch keine EXE-Datei.\\n\\n{url}")
        else:
            if has_status_label:
                self.update_status.configure(text=f"Update-Status: Prüfung fehlgeschlagen – {value}")
            if manual:
                messagebox.showerror("Updateprüfung fehlgeschlagen", str(value))

    def _download_and_install(self, url, version):
        if not getattr(sys, "frozen", False):
            messagebox.showinfo("Testmodus",
                                "Die Updateprüfung funktioniert. Die automatische EXE-Installation ist nur in der installierten EXE-Version aktiv.")
            return
        if not url:
            return
        try:
            self.update_status.configure(text=f"Update-Status: Lade Version {version} herunter …")
            update_dir = Path(tempfile.gettempdir()) / "GameCenterUpdate"
            update_dir.mkdir(parents=True, exist_ok=True)
            new_exe = update_dir / "Game Center.new.exe"
            request = urllib.request.Request(url, headers={"User-Agent": "Game-Center-Updater"})
            with urllib.request.urlopen(request, timeout=60) as response, open(new_exe, "wb") as out:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            current_exe = Path(sys.executable).resolve()
            # A small batch helper waits for this process to exit, swaps the executable, and relaunches it.
            bat = update_dir / "install_update.bat"
            bat.write_text(
                '@echo off\\r\\n'
                'timeout /t 2 /nobreak >nul\\r\\n'
                f'copy /Y "{new_exe}" "{current_exe}" >nul\\r\\n'
                f'start "" "{current_exe}"\\r\\n'
                f'del "%~f0"\\r\\n',
                encoding="utf-8"
            )
            subprocess.Popen(["cmd", "/c", str(bat)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Update fehlgeschlagen", f"Das Update konnte nicht installiert werden:\\n{exc}")

    def load_settings(self):
        try:
            if CONFIG_FILE.exists():
                loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.settings.update({k: v for k, v in loaded.items() if k in DEFAULTS})
        except Exception:
            pass

if __name__ == "__main__":
    App().mainloop()
