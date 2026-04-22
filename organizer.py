import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from datetime import datetime

FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
    "Documents": [".doc", ".docx", ".txt", ".pages"],
    "PDFs": [".pdf"],
    "Spreadsheets": [".xls", ".xlsx", ".csv"],
    "Presentations": [".ppt", ".pptx"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv"],
    "Audio": [".mp3", ".wav", ".aac"],
    "Archives": [".zip", ".tar", ".gz", ".rar"],
    "Code": [".py", ".js", ".html", ".css", ".json"],
}

LAST_FOLDER_FILE = os.path.expanduser("~/file-organizer/last_folder.txt")

def save_last_folder(path):
    with open(LAST_FOLDER_FILE, "w") as f:
        f.write(path)

def load_last_folder():
    if os.path.exists(LAST_FOLDER_FILE):
        with open(LAST_FOLDER_FILE, "r") as f:
            return f.read().strip()
    return ""

def get_files(folder_path):
    files = []
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            files.append(filename)
    return files

def move_file(src, dst_folder, filename, log):
    try:
        os.makedirs(dst_folder, exist_ok=True)
        dst = os.path.join(dst_folder, filename)
        if os.path.exists(dst):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dst):
                dst = os.path.join(dst_folder, f"{name}_{counter}{ext}")
                counter += 1
        shutil.move(src, dst)
        log(f"{filename}  ->  {os.path.basename(dst_folder)}/")
    except Exception as e:
        log(f"Skipped: {filename} ({e})")

def get_type_category(filename):
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    for folder_name, extensions in FILE_TYPES.items():
        if ext in extensions:
            return folder_name
    return "Other"

def get_size_category(filepath):
    size = os.path.getsize(filepath)
    if size < 1_000_000:
        return "Small"
    elif size < 100_000_000:
        return "Medium"
    else:
        return "Large"

def get_alpha_category(filename):
    first_char = filename[0].upper()
    if first_char.isdigit():
        return "0-9"
    elif first_char.isalpha():
        return first_char
    return "Other"

def get_date_category(filepath):
    ts = os.path.getctime(filepath)
    created = datetime.fromtimestamp(ts)
    now = datetime.now()
    if created.year == now.year:
        return "This Year"
    elif created.year == now.year - 1:
        return "Last Year"
    else:
        return "Older"

def get_extension_category(filename):
    _, ext = os.path.splitext(filename)
    if ext:
        return ext.lower().replace(".", "").upper() + " Files"
    return "No Extension"

def build_folder_path(base, categories):
    return os.path.join(base, *categories)

def organize_files(folder_path, modes, log, progress_cb):
    files = get_files(folder_path)
    total = len(files)
    if total == 0:
        log("No files found in this folder.")
        return
    for idx, filename in enumerate(files):
        filepath = os.path.join(folder_path, filename)
        categories = []
        if "type" in modes:
            categories.append(get_type_category(filename))
        if "size" in modes:
            categories.append(get_size_category(filepath))
        if "alpha" in modes:
            categories.append(get_alpha_category(filename))
        if "date" in modes:
            categories.append(get_date_category(filepath))
        if "ext" in modes:
            categories.append(get_extension_category(filename))
        if not categories:
            categories = ["Unsorted"]
        dst_folder = build_folder_path(folder_path, categories)
        move_file(filepath, dst_folder, filename, log)
        progress_cb(int((idx + 1) / total * 100))

def reset_folder(folder_path, log, progress_cb):
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        if root == folder_path:
            continue
        for f in files:
            all_files.append(os.path.join(root, f))
    total = len(all_files)
    for idx, filepath in enumerate(all_files):
        filename = os.path.basename(filepath)
        move_file(filepath, folder_path, filename, log)
        progress_cb(int((idx + 1) / total * 100))
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                log(f"Removed: {item}/")
            except Exception as e:
                log(f"Could not remove {item}: {e}")
    log("Reset complete.")

# colors
BG        = "#f5f5f7"
WHITE     = "#ffffff"
TEXT      = "#1d1d1f"
BORDER    = "#d2d2d7"
BLACK     = "#000000"
RED       = "#ff3b30"
SEPARATOR = "#e5e5ea"
FONT      = "Times New Roman"

class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer")
        self.root.geometry("620x780")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self._build_titlebar()
        self._build_folder_card()
        self._build_filters_card()
        self._build_reset_card()
        self._build_button()
        self._build_log_card()

    def _card(self, pady_top=0):
        f = tk.Frame(self.root, bg=WHITE,
                     highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", padx=24, pady=(pady_top, 0))
        return f

    def _section_label(self, parent, text):
        tk.Label(parent, text=text.upper(),
                 font=(FONT, 11, "bold"),
                 bg=WHITE, fg=TEXT).pack(anchor="w", padx=20, pady=(14, 4))

    def _separator(self, parent):
        tk.Frame(parent, bg=SEPARATOR, height=1).pack(fill="x", padx=20)

    def _row(self, parent):
        f = tk.Frame(parent, bg=WHITE)
        f.pack(fill="x", padx=20, pady=6)
        return f

    def _checkbox(self, parent, variable, command, color=BLACK):
        cb_frame = tk.Frame(parent, bg=WHITE,
                            highlightbackground="#aaaaaa",
                            highlightthickness=1)
        cb_frame.pack(side="left", padx=(0, 8))
        cb = tk.Checkbutton(cb_frame, variable=variable,
                            bg=WHITE, activebackground=WHITE,
                            selectcolor=color,
                            command=command,
                            relief="flat", bd=2,
                            width=1, height=1)
        cb.pack()
        return cb

    def _fake_button(self, parent, text, command,
                     padx=16, pady=6, font_size=12, side="right"):
        frame = tk.Frame(parent, bg=BLACK)
        frame.pack(side=side, padx=(8, 0) if side == "right" else 0)
        lbl = tk.Label(frame, text=text,
                       font=(FONT, font_size, "bold"),
                       bg=BLACK, fg=WHITE,
                       padx=padx, pady=pady,
                       cursor="hand2")
        lbl.pack()
        lbl.bind("<Button-1>", lambda e: command())
        frame.bind("<Button-1>", lambda e: command())
        return lbl

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=24, pady=(28, 16))
        tk.Label(bar, text="File Organizer",
                 font=(FONT, 26, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(bar, text="by Harrison Walters",
                 font=(FONT, 26, "bold"),
                 bg=BG, fg=TEXT).pack(side="left", padx=12, pady=6)

    def _build_folder_card(self):
        card = self._card()
        self._section_label(card, "Folder")
        self._separator(card)
        row = self._row(card)
        self.folder_var = tk.StringVar(value=load_last_folder())
        tk.Entry(row, textvariable=self.folder_var,
                 font=(FONT, 13), bg=BG, fg=TEXT,
                 relief="flat", highlightthickness=0).pack(
                 side="left", fill="x", expand=True, ipady=4)
        self._fake_button(row, "Choose", self.browse_folder,
                          padx=18, pady=6, font_size=12)
        tk.Frame(card, bg=WHITE, height=8).pack()

    def _build_filters_card(self):
        card = self._card(pady_top=12)
        self._section_label(card, "Sort Filters")
        self._separator(card)

        self.check_type  = tk.BooleanVar()
        self.check_size  = tk.BooleanVar()
        self.check_alpha = tk.BooleanVar()
        self.check_date  = tk.BooleanVar()
        self.check_ext   = tk.BooleanVar()

        filters = [
            (self.check_type,  "File Type",      "Images, PDFs, Videos, Documents"),
            (self.check_size,  "File Size",       "Small  |  Medium  |  Large"),
            (self.check_alpha, "Alphabetical",    "A through Z  (0-9 first)"),
            (self.check_date,  "Date Created",    "This Year  |  Last Year  |  Older"),
            (self.check_ext,   "File Extension",  "PDF Files, JPG Files, MP4 Files..."),
        ]

        for i, (var, label, desc) in enumerate(filters):
            if i > 0:
                self._separator(card)
            row = self._row(card)
            self._checkbox(row, var, self._on_filter_change)
            tk.Label(row, text=label,
                     font=(FONT, 13, "bold"),
                     bg=WHITE, fg=TEXT).pack(side="left")
            tk.Label(row, text=desc,
                     font=(FONT, 13),
                     bg=WHITE, fg=TEXT).pack(side="left", padx=10)

        tk.Frame(card, bg=WHITE, height=8).pack()

    def _build_reset_card(self):
        card = self._card(pady_top=12)
        self._section_label(card, "Advanced")
        self._separator(card)
        self.check_reset = tk.BooleanVar()
        reset_row = self._row(card)
        self._checkbox(reset_row, self.check_reset,
                       self._on_reset_change, color=RED)
        tk.Label(reset_row, text="Reset Folder",
                 font=(FONT, 13, "bold"),
                 bg=WHITE, fg=RED).pack(side="left")
        tk.Label(reset_row, text="Move all files back to root",
                 font=(FONT, 13),
                 bg=WHITE, fg=RED).pack(side="left", padx=10)
        tk.Frame(card, bg=WHITE, height=8).pack()

    def _build_button(self):
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(pady=16)

        org_frame = tk.Frame(btn_frame, bg=BLACK)
        org_frame.pack()

        self.run_lbl = tk.Label(org_frame,
                                text="Organize",
                                font=(FONT, 14, "bold"),
                                bg=BLACK, fg=WHITE,
                                padx=60, pady=12,
                                cursor="hand2")
        self.run_lbl.pack()
        self.run_lbl.bind("<Button-1>", lambda e: self.run_organizer())
        org_frame.bind("<Button-1>", lambda e: self.run_organizer())

        self.progress = ttk.Progressbar(btn_frame,
                                        length=400,
                                        mode="determinate")
        self.progress.pack(pady=(10, 0))

    def _build_log_card(self):
        card = self._card()
        self._section_label(card, "Activity")
        self._separator(card)
        log_frame = tk.Frame(card, bg=WHITE)
        log_frame.pack(fill="x", padx=20, pady=10)
        self.log_box = tk.Text(log_frame, height=6,
                               font=(FONT, 12),
                               bg=BG, fg=TEXT,
                               relief="flat", wrap="word", bd=0)
        self.log_box.pack(fill="x")
        tk.Frame(card, bg=WHITE, height=4).pack()

    def _on_filter_change(self):
        self.check_reset.set(False)

    def _on_reset_change(self):
        if self.check_reset.get():
            self.check_type.set(False)
            self.check_size.set(False)
            self.check_alpha.set(False)
            self.check_date.set(False)
            self.check_ext.set(False)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            save_last_folder(folder)

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.root.update()

    def set_progress(self, value):
        self.progress["value"] = value
        self.root.update()

    def set_organizing(self, is_working):
        text = "Working..." if is_working else "Organize"
        self.run_lbl.config(text=text)

    def run_organizer(self):
        folder = self.folder_var.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Please choose a valid folder.")
            return
        save_last_folder(folder)
        self.log_box.delete(1.0, tk.END)
        self.progress["value"] = 0

        modes = []
        if self.check_type.get():  modes.append("type")
        if self.check_size.get():  modes.append("size")
        if self.check_alpha.get(): modes.append("alpha")
        if self.check_date.get():  modes.append("date")
        if self.check_ext.get():   modes.append("ext")

        is_reset = self.check_reset.get()

        if not modes and not is_reset:
            messagebox.showwarning("Nothing Selected",
                                   "Please check at least one filter.")
            return

        self.set_organizing(True)

        def task():
            self.log(f"Folder: {folder}\n")
            if is_reset:
                self.log("Resetting folder...\n")
                reset_folder(folder, self.log, self.set_progress)
            else:
                names = []
                if "type"  in modes: names.append("File Type")
                if "size"  in modes: names.append("File Size")
                if "alpha" in modes: names.append("Alphabetical")
                if "date"  in modes: names.append("Date Created")
                if "ext"   in modes: names.append("File Extension")
                self.log(f"Sorting by: {' + '.join(names)}\n")
                organize_files(folder, modes, self.log, self.set_progress)
            self.log("\nDone.")
            self.set_progress(100)
            self.set_organizing(False)

        threading.Thread(target=task, daemon=True).start()

root = tk.Tk()
app = FileOrganizerApp(root)
root.mainloop()
