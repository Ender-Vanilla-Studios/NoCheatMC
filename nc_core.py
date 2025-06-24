import os, urllib.request, urllib.error, psutil, subprocess, locale, json, zipfile, re
import tkinter as tk  # для insert в output
from nc_fun import *  # если там вспомогательные функции, ок

class NoCheatChecker:
    def __init__(self):
        self.LANG = self.detect_lang()
        self.TRANSLATIONS = self.load_translations(self.LANG)
        self.REMOTE_DB_URL = "https://raw.githubusercontent.com/Ender-Vanilla-Studios/NoCheatMC/refs/heads/main/NoCheatMC-BD.json"
        self.CHEAT_MODS, self.CHEAT_RESOURCEPACKS = self.load_cheat_database_smart()

    def detect_lang(self):
        try:
            lang = locale.getlocale()[0]
            if lang:
                lang_lower = lang.lower()
                if lang_lower.startswith("ru"):
                    return "ru"
                elif lang_lower.startswith("uk") or lang_lower.startswith("ua"):
                    return "ua"
        except:
            pass
        return "en"

    def load_translations(self, lang_code):
        path = os.path.join("lang", f"{lang_code}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def t(self, key, *args):
        text = self.TRANSLATIONS.get(key, key)
        return text.format(*args) if args else text

    def load_json_from_file(self, path):
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    def load_json_from_url(self, url):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    return json.loads(data)
        except:
            return None
        return None

    def load_cheat_database_smart(self, local_path="NoCheatMC-BD.json", remote_url=None):
        remote_url = remote_url or self.REMOTE_DB_URL
        remote_data = self.load_json_from_url(remote_url)
        local_data = self.load_json_from_file(local_path)

        if remote_data is None and local_data is None:
            return [], []
        if remote_data and not local_data:
            return [x.lower() for x in remote_data.get("cheat_mods", [])], [x.lower() for x in remote_data.get("cheat_resourcepacks", [])]
        if local_data and not remote_data:
            return [x.lower() for x in local_data.get("cheat_mods", [])], [x.lower() for x in local_data.get("cheat_resourcepacks", [])]

        r_count = len(remote_data.get("cheat_mods", [])) + len(remote_data.get("cheat_resourcepacks", []))
        l_count = len(local_data.get("cheat_mods", [])) + len(local_data.get("cheat_resourcepacks", []))
        data = remote_data if r_count >= l_count else local_data
        return [x.lower() for x in data.get("cheat_mods", [])], [x.lower() for x in data.get("cheat_resourcepacks", [])]

    def find_game_directory(self):
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if "java" in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if "--gameDir" in cmdline:
                        idx = cmdline.index("--gameDir")
                        return cmdline[idx + 1]
            except:
                continue
        return None

    def get_mods_list(self, path):
        return [f for f in os.listdir(path) if f.endswith(".jar")] if os.path.isdir(path) else []

    def get_mod_id_from_jar(self, jar_path):
        mod_ids = set()
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                if 'mcmod.info' in jar.namelist():
                    with jar.open('mcmod.info') as f:
                        data = json.load(f)
                        mods = data if isinstance(data, list) else [data]
                        for mod in mods:
                            mod_ids.add(mod.get("modid") or mod.get("modId", ""))
                if 'fabric.mod.json' in jar.namelist():
                    with jar.open('fabric.mod.json') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            mod_ids.add(data.get("id", ""))
                for name in jar.namelist():
                    if name.startswith("META-INF/") and name.endswith("mods.toml"):
                        with jar.open(name) as f:
                            text = f.read().decode(errors='ignore')
                            mod_ids.update(re.findall(r'id\s*=\s*"(.*?)"', text))
        except:
            pass
        return list(mod_ids)

    def check_mods(self, mods, path):
        result = []
        for mod in mods:
            for cheat in self.CHEAT_MODS:
                if cheat in mod.lower():
                    mod_ids = self.get_mod_id_from_jar(os.path.join(path, mod))
                    result.append((mod, mod_ids))
                    break
        return result

    def check_cheat_processes(self):
        found = []
        for proc in psutil.process_iter(['name']):
            try:
                if any(cheat in proc.info['name'].lower() for cheat in self.CHEAT_MODS):
                    found.append(proc.info['name'])
            except:
                continue
        return found

    def check_java_version(self):
        try:
            res = subprocess.run(["java", "-version"], capture_output=True, text=True)
            return "\n".join(res.stderr.splitlines() + res.stdout.splitlines())
        except FileNotFoundError:
            return self.t("java_not_found")

    def find_non_mod_jars(self, game_dir, log_func=print):
        jar_files = []
        system_dirs_to_skip = {'.fabric', '.gradle', '.minecraft', '.git', '.idea'}  # можно добавить другие

        for root, dirs, files in os.walk(game_dir):
            # Преобразуем путь в части по /
            parts = root.replace("\\", "/").split("/")

            # Пропускаем если в пути есть папка mods или системная папка
            if "mods" in parts or any(d in system_dirs_to_skip for d in parts):
                continue

            for file in files:
                if file.endswith(".jar"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, game_dir)
                    jar_files.append(rel_path)

        if jar_files:
            log_func(self.t("nonmod_jars_found", len(jar_files)) + "\n")
            for path in jar_files:
                log_func("  • " + path + "\n")
        else:
            log_func(self.t("no_nonmod_jars") + "\n")

        return jar_files

        if jar_files:
            log_func(self.t("nonmod_jars_found", len(jar_files)) + "\n")
            for path in jar_files:
                log_func("  • " + path + "\n")
        else:
            log_func(self.t("no_nonmod_jars") + "\n")

        return jar_files

    def perform_check(self, output, button):
        output.delete(1.0, tk.END)
        button.config(state=tk.DISABLED)

        log = []
        output.insert(tk.END, self.t("searching_game"))
        game_dir = self.find_game_directory()
        if not game_dir:
            output.insert(tk.END, self.t("not_found"))
            button.config(state=tk.NORMAL)
            return

        mods_path = os.path.join(game_dir, "mods")
        rps_path = os.path.join(game_dir, "resourcepacks")
        output.insert(tk.END, self.t("game_dir", game_dir) + "\n")
        log.append(f"Game directory: {game_dir}")

        # MODS
        mods = self.get_mods_list(mods_path)
        found = self.check_mods(mods, mods_path)
        output.insert(tk.END, self.t("checking_mods"))
        output.insert(tk.END, self.t("mod_count", len(mods)))
        log.append(f"Mods found: {', '.join(mods)}")
        if found:
            modlist = [f"{m} [IDs: {', '.join(ids) or 'unknown'}]" for m, ids in found]
            output.insert(tk.END, self.t("suspicious_mods", ", ".join(modlist)))
            log.append("Suspicious mods: " + ", ".join(modlist))
        else:
            output.insert(tk.END, self.t("no_suspicious"))
            log.append("No suspicious mods")

        # RESOURCEPACKS
        rps = os.listdir(rps_path) if os.path.isdir(rps_path) else []
        suspicious_rp = [rp for rp in rps if any(c in rp.lower() for c in self.CHEAT_RESOURCEPACKS)]
        output.insert(tk.END, self.t("checking_resourcepacks"))
        log.append(f"Resourcepacks: {', '.join(rps)}")
        if suspicious_rp:
            output.insert(tk.END, self.t("suspicious_resourcepacks", ", ".join(suspicious_rp)))
            log.append("Suspicious resourcepacks: " + ", ".join(suspicious_rp))
        else:
            output.insert(tk.END, self.t("no_suspicious_resourcepacks"))
            log.append("No suspicious resourcepacks")

        # PROCESSES
        cheats = self.check_cheat_processes()
        if cheats:
            output.insert(tk.END, self.t("cheat_processes", ", ".join(cheats)))
            log.append("Cheat processes: " + ", ".join(cheats))
        else:
            output.insert(tk.END, self.t("no_cheat_processes"))
            log.append("No cheat processes")

        # JAVA
        java_info = self.check_java_version()
        output.insert(tk.END, self.t("java_version", java_info) + "\n")
        log.append("Java version:\n" + java_info)

        # NON-MOD JARS
        self.find_non_mod_jars(game_dir, lambda msg: output.insert(tk.END, msg))

        # SAVE REPORT
        try:
            with open("nocheat_report.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(log))
            output.insert(tk.END, self.t("report_saved", "nocheat_report.txt"))
        except Exception as e:
            output.insert(tk.END, f"❌ Failed to save report: {e}")

        button.config(state=tk.NORMAL)
