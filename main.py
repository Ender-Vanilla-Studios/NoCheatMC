import os
import psutil
import subprocess
import tkinter as tk
from tkinter import scrolledtext
import threading
import locale
import json

# === ЯЗЫК ===

def detect_lang():
    try:
        lang = locale.getlocale()[0]
        if lang and lang.lower().startswith("ru"):
            return "ru"
    except:
        pass
    return "en"

LANG = detect_lang()
TRANSLATIONS = {}

def load_translations(lang_code):
    path = os.path.join("lang", f"{lang_code}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

TRANSLATIONS = load_translations(LANG)

def t(key, *args):
    text = TRANSLATIONS.get(key, key)
    return text.format(*args) if args else text

# === ДАННЫЕ ===

def load_cheat_database(file_path="NoCheatMC-BD.json"):
    cheat_mods = []
    cheat_resourcepacks = []

    if not os.path.isfile(file_path):
        print(f"❌ Файл базы читов не найден: {file_path}")
        return cheat_mods, cheat_resourcepacks

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            cheat_mods = [mod.lower() for mod in data.get("cheat_mods", [])]
            cheat_resourcepacks = [rp.lower() for rp in data.get("cheat_resourcepacks", [])]
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
    except Exception as e:
        print(f"❌ Ошибка при загрузке базы читов: {e}")

    return cheat_mods, cheat_resourcepacks

CHEAT_MODS, CHEAT_RESOURCEPACKS = load_cheat_database()

# Добавляем функцию, которую вызывали, но не определили
def load_cheat_resourcepacks():
    # просто возвращаем уже загруженный список
    return CHEAT_RESOURCEPACKS

# === ПРОВЕРКИ ===

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
        for cheat in CHEAT_MODS:
            if cheat in name:
                suspicious.append(mod)
                break
    return suspicious

def check_cheat_processes():
    found = []
    for proc in psutil.process_iter(['name']):
        try:
            pname = proc.info['name'].lower()
            for cheat in CHEAT_MODS:
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
        return t("java_not_found")

# === ГЛАВНАЯ ПРОВЕРКА ===

def perform_check(output_widget, button):
    button.config(state=tk.DISABLED)
    output_widget.delete(1.0, tk.END)

    lines = []

    output_widget.insert(tk.END, t("searching_game"))
    game_dir = find_game_directory()
    if not game_dir:
        output_widget.insert(tk.END, t("not_found"))
        button.config(state=tk.NORMAL)
        return

    mods_path = os.path.join(game_dir, "mods")
    res_path = os.path.join(game_dir, "resourcepacks")

    output_widget.insert(tk.END, t("game_dir", game_dir) + "\n")
    lines.append(f"Game directory: {game_dir}")

    # МОДЫ
    output_widget.insert(tk.END, t("checking_mods"))
    mods = get_mods_list(mods_path)
    suspicious_mods = check_mods(mods)
    output_widget.insert(tk.END, t("mod_count", len(mods)))
    lines.append(f"Mods found ({len(mods)}): {', '.join(mods) if mods else 'None'}")
    if suspicious_mods:
        output_widget.insert(tk.END, t("suspicious_mods", ', '.join(suspicious_mods)))
        lines.append("Suspicious mods: " + ', '.join(suspicious_mods))
    else:
        output_widget.insert(tk.END, t("no_suspicious"))
        lines.append("No suspicious mods")

    # РЕСУРС-ПАКИ
    output_widget.insert(tk.END, t("checking_resourcepacks"))
    cheat_rp = load_cheat_resourcepacks()
    resourcepacks = os.listdir(res_path) if os.path.isdir(res_path) else []
    suspicious_rp = [rp for rp in resourcepacks if any(c in rp.lower() for c in cheat_rp)]
    lines.append(f"Resourcepacks found ({len(resourcepacks)}): {', '.join(resourcepacks) if resourcepacks else 'None'}")
    if suspicious_rp:
        output_widget.insert(tk.END, t("suspicious_resourcepacks", ', '.join(suspicious_rp)))
        lines.append("Suspicious resourcepacks: " + ', '.join(suspicious_rp))
    else:
        output_widget.insert(tk.END, t("no_suspicious_resourcepacks"))
        lines.append("No suspicious resourcepacks")

    # ПРОЦЕССЫ
    cheat_processes = check_cheat_processes()
    if cheat_processes:
        output_widget.insert(tk.END, t("cheat_processes", ', '.join(cheat_processes)))
        lines.append("Cheat processes: " + ', '.join(cheat_processes))
    else:
        output_widget.insert(tk.END, t("no_cheat_processes"))
        lines.append("No cheat processes")

    # JAVA
    java_info = check_java_version()
    output_widget.insert(tk.END, t("java_version", java_info) + "\n")
    lines.append("Java version:\n" + java_info)

    # ОТЧЁТ
    try:
        report_path = os.path.join(os.getcwd(), "nocheat_report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        output_widget.insert(tk.END, t("report_saved", report_path))
    except Exception as e:
        output_widget.insert(tk.END, f"❌ Failed to save report: {e}\n")

    button.config(state=tk.NORMAL)

# === GUI ===

def start_gui():
    root = tk.Tk()
    root.title("NoCheatMC")
    root.geometry("600x600")
    root.resizable(False, False)

    lbl_description = tk.Label(
        root,
        text=t("description"),
        font=("Arial", 10),
        wraplength=560,
        justify="left"
    )
    lbl_description.pack(padx=10, pady=(10, 0), anchor="w")

    btn_check = tk.Button(root, text=t("btn_check"), font=("Arial", 14))
    btn_check.pack(pady=10)

    txt_output = scrolledtext.ScrolledText(root, font=("Consolas", 10), width=70, height=25)
    txt_output.pack(padx=10, pady=10)

    def on_click():
        threading.Thread(target=perform_check, args=(txt_output, btn_check), daemon=True).start()

    btn_check.config(command=on_click)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
