import os
import psutil
import subprocess
import tkinter as tk
from tkinter import scrolledtext
import threading

# Ключевые слова для подозрительных читов
KNOWN_CHEAT_NAMES = {"wurst", "aristois", "meteor", "sigma", "future", "impact", "novoline", "inertia"}

def find_game_directory():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            name = proc.info['name'].lower()
            if "java" in name:
                cmdline = proc.info['cmdline']
                if "--gameDir" in cmdline:
                    idx = cmdline.index("--gameDir")
                    return cmdline[idx + 1]
        except (psutil.NoSuchProcess, psutil.AccessDenied, IndexError):
            continue
    return None

def get_mods_list(mods_path):
    if not os.path.isdir(mods_path):
        return []
    return [f for f in os.listdir(mods_path) if f.endswith(".jar")]

def check_mods(mods):
    suspicious = []
    for mod in mods:
        name = mod.lower()
        for cheat in KNOWN_CHEAT_NAMES:
            if cheat in name:
                suspicious.append(mod)
                break
    return suspicious

def check_cheat_processes():
    found = []
    for proc in psutil.process_iter(['name']):
        try:
            pname = proc.info['name'].lower()
            for cheat in KNOWN_CHEAT_NAMES:
                if cheat in pname:
                    found.append(pname)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found

def check_java_version():
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        output = result.stderr.splitlines() + result.stdout.splitlines()
        return "\n".join(output)
    except FileNotFoundError:
        return "Java не найдена (java не установлена или не в PATH)"

def perform_check(output_widget, button):
    button.config(state=tk.DISABLED)
    output_widget.delete(1.0, tk.END)
    output_widget.insert(tk.END, "🔍 Поиск папки игры...\n")
    game_dir = find_game_directory()
    if not game_dir:
        output_widget.insert(tk.END, "❌ Не удалось найти запущенный Minecraft с --gameDir.\n")
        button.config(state=tk.NORMAL)
        return

    mods_path = os.path.join(game_dir, "mods")
    output_widget.insert(tk.END, f"📁 Директория игры: {game_dir}\n")
    output_widget.insert(tk.END, "📦 Проверка модов...\n")
    mods = get_mods_list(mods_path)
    suspicious_mods = check_mods(mods)
    cheat_processes = check_cheat_processes()
    java_info = check_java_version()

    output_widget.insert(tk.END, f"✅ Найдено модов: {len(mods)}\n")
    if suspicious_mods:
        output_widget.insert(tk.END, f"⚠️ Подозрительные моды: {', '.join(suspicious_mods)}\n")
    else:
        output_widget.insert(tk.END, "✅ Подозрительных модов нет.\n")

    if cheat_processes:
        output_widget.insert(tk.END, f"🚨 Найдены чит-процессы: {', '.join(cheat_processes)}\n")
    else:
        output_widget.insert(tk.END, "✅ Чит-процессы не найдены.\n")

    output_widget.insert(tk.END, "🔧 Версия Java:\n" + java_info + "\n")

    button.config(state=tk.NORMAL)

def start_gui():
    root = tk.Tk()
    root.title("Проверка Minecraft на читы")

    root.geometry("600x400")
    root.resizable(False, False)

    btn_check = tk.Button(root, text="Проверить Minecraft", font=("Arial", 14))
    btn_check.pack(pady=10)

    txt_output = scrolledtext.ScrolledText(root, font=("Consolas", 10), width=70, height=20)
    txt_output.pack(padx=10, pady=10)

    def on_click():
        threading.Thread(target=perform_check, args=(txt_output, btn_check), daemon=True).start()

    btn_check.config(command=on_click)

    root.mainloop()

if __name__ == "__main__":
    start_gui()
