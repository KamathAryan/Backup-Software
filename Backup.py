import os
import shutil
from datetime import datetime
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk

THREAD_COUNT = 50

def process_file(file_info, backup_directory, dry_run, log_messages, cutoff_year):
    file_path, relative_path = file_info
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))

    if file_mod_time.year < cutoff_year:
        target_folder = os.path.join(backup_directory, relative_path)
        target_path = os.path.join(target_folder, os.path.basename(file_path))

        if dry_run:
            log_messages.append(f"[Dry Run] Would move: {file_path} to {target_path}")
        else:
            os.makedirs(target_folder, exist_ok=True)
            shutil.copy2(file_path, target_path)
            os.chmod(file_path, 0o777)  # Ensure the file can be deleted
            os.remove(file_path)
            log_messages.append(f"Moved: {file_path} to {target_path}")

def backup_old_files(source_directory, backup_directory, dry_run=False, cutoff_year=2022):
    files_to_process = []
    log_messages = []

    for root, _, files in os.walk(source_directory):
        relative_path = os.path.relpath(root, source_directory)
        for filename in files:
            files_to_process.append((os.path.join(root, filename), relative_path))

    total_files = len(files_to_process)
    processed_files = 0

    def update_progress_inner():
        nonlocal processed_files
        processed_files += 1
        update_progress(processed_files, total_files)

    for file_info in files_to_process:
        process_file(file_info, backup_directory, dry_run, log_messages, cutoff_year)
        update_progress_inner()

    if processed_files > 0:
        log_messages.append(f"\nBackup Complete: Moved {processed_files} files.")
    else:
        log_messages.append(f"\nBackup Complete: No files older than the year {cutoff_year} found.")

    update_log_area("\n".join(log_messages))

def select_source_directory():
    source_directory = filedialog.askdirectory(title="Select Source Directory")
    if source_directory:
        source_entry.delete(0, tk.END)
        source_entry.insert(0, source_directory)

def validate_cutoff_year(year):
    try:
        year = int(year)
        if 1900 <= year <= datetime.now().year:
            return year
        else:
            raise ValueError
    except ValueError:
        return None

def start_backup(dry_run=False):
    source_directory = source_entry.get()
    cutoff_year = cutoff_year_entry.get()

    if not source_directory:
        messagebox.showwarning("Input Error", "Please select a source directory.")
        return

    if not cutoff_year or (validate_cutoff_year(cutoff_year) is None):
        messagebox.showwarning("Input Error", "Please enter a valid cutoff year (between 1900 and the current year).")
        return

    cutoff_year = int(cutoff_year)

    current_date = datetime.now().strftime("%Y-%m-%d")
    backup_directory = f"{source_directory}_backup"
    os.makedirs(backup_directory, exist_ok=True)

    log_area.delete(1.0, tk.END)
    log_area.insert(tk.END, "Starting backup...\n")

    backup_thread = Thread(target=backup_old_files, args=(source_directory, backup_directory, dry_run, cutoff_year))
    backup_thread.start()

def update_log_area(message):
    log_area.insert(tk.END, message + "\n")
    log_area.see(tk.END)

def update_progress(processed, total):
    progress['value'] = (processed / total) * 100
    app.update_idletasks()

app = tk.Tk()
app.title("Backup Software")
app.geometry("600x450")

tk.Label(app, text="Select Source Directory:", font=('Arial', 12)).pack(pady=10)

source_entry = tk.Entry(app, font=('Arial', 12), width=50)
source_entry.pack(pady=5)

browse_button = tk.Button(app, text="Browse", font=('Arial', 12), command=select_source_directory)
browse_button.pack(pady=5)

tk.Label(app, text="Enter Cutoff Year:", font=('Arial', 12)).pack(pady=10)

cutoff_year_entry = tk.Entry(app, font=('Arial', 12), width=10)
cutoff_year_entry.pack(pady=5)

dry_run_var = tk.BooleanVar()
dry_run_check = tk.Checkbutton(app, text="Dry Run", variable=dry_run_var, font=('Arial', 12))
dry_run_check.pack(pady=5)

tk.Button(app, text="Start Backup", font=('Arial', 12), command=lambda: start_backup(dry_run=dry_run_var.get())).pack(pady=20)

log_area = scrolledtext.ScrolledText(app, width=60, height=10, wrap=tk.WORD, font=('Arial', 12))
log_area.pack(pady=5)

progress = ttk.Progressbar(app, length=400, mode='determinate', maximum=100)
progress.pack(pady=10)

app.mainloop()
