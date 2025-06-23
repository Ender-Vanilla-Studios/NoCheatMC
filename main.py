import os
import urllib.request
import urllib.error

import psutil
import subprocess
import tkinter as tk
from tkinter import scrolledtext
import threading
import locale
import json

# === LANGUAGE ===

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

REMOTE_DB_URL = "https://raw.githubusercontent.com/Ender-Vanilla-Studios/NoCheatMC/refs/heads/main/NoCheatMC-BD.json"

def load_json_from_file(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading local file {path}: {e}")
        return None

def load_json_from_url(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                return json.loads(data)
            else:
                print(f"❌ Error loading from URL {url}: HTTP {response.status}")
    except urllib.error.URLError as e:
        print(f"❌ Error loading from URL {url}: {e}")
    except Exception as e:
        print(f"❌ General error loading from URL {url}: {e}")
    return None

def load_cheat_database_smart(local_path="NoCheatMC-BD.json", remote_url=REMOTE_DB_URL):
    remote_data = load_json_from_url(remote_url)
    local_data = load_json_from_file(local_path)

    # If neither remote nor local database exists — return empty lists
    if remote_data is None and local_data is None:
        print("❌ No remote or local cheat database found.")
        return [], []

    # If only remote exists
    if remote_data is not None and local_data is None:
        print("ℹ️ Using remote cheat database.")
        cheat_mods = [x.lower() for x in remote_data.get("cheat_mods", [])]
        cheat_resourcepacks = [x.lower() for x in remote_data.get("cheat_resourcepacks", [])]
        return cheat_mods, cheat_resourcepacks

    # If only local exists
    if local_data is not None and remote_data is None:
        print("ℹ️ Using local cheat database.")
        cheat_mods = [x.lower() for x in local_data.get("cheat_mods", [])]
        cheat_resourcepacks = [x.lower() for x in local_data.get("cheat_resourcepacks", [])]
        return cheat_mods, cheat_resourcepacks

    # If both exist — choose the more complete (by total number of cheats)
    local_count = len(local_data.get("cheat_mods", [])) + len(local_data.get("cheat_resourcepacks", []))
    remote_count = len(remote_data.get("cheat_mods", [])) + len(remote_data.get("cheat_resourcepacks", []))

    if remote_count >= local_count:
        print(f"ℹ️ Using remote cheat database (size: {remote_count} vs local: {local_count}).")
        cheat_mods = [x.lower() for x in remote_data.get("cheat_mods", [])]
        cheat_resourcepacks = [x.lower() for x in remote_data.get("cheat_resourcepacks", [])]
    else:
        print(f"ℹ️ Using local cheat database (size: {local_count} vs remote: {remote_count}).")
        cheat_mods = [x.lower() for x in local_data.get("cheat_mods", [])]
        cheat_resourcepacks = [x.lower() for x in local_data.get("cheat_resourcepacks", [])]

    return cheat_mods, cheat_resourcepacks

def t(key, *args):
    text = TRANSLATIONS.get(key, key)
    return text.format(*args) if args else text

CHEAT_MODS, CHEAT_RESOURCEPACKS = load_cheat_database_smart()

# Add the function which was called but not defined
def load_cheat_resourcepacks():
    # simply return already loaded list
    return CHEAT_RESOURCEPACKS

# === CHECKS ===

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

# === MAIN CHECK ===

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

    # MODS
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

    # RESOURCE PACKS
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

    # PROCESSES
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

    # REPORT
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
