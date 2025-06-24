from nc_core import NoCheatChecker
import tkinter as tk
from tkinter import scrolledtext
import threading
import os
import subprocess

def start_gui():
    checker = NoCheatChecker()

    root = tk.Tk()
    root.title("NoCheatMC")
    root.geometry("700x600")
    root.minsize(600, 500)

    # Основной контейнер
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Описание
    lbl_description = tk.Label(
        frame,
        text=checker.t("description"),
        font=("Arial", 11),
        wraplength=660,
        justify="center"
    )
    lbl_description.pack(pady=(0, 15))

    # Текстовое поле (консоль)
    txt_output = scrolledtext.ScrolledText(
        frame, font=("Consolas", 10), wrap=tk.WORD
    )
    txt_output.pack(fill="both", expand=True, pady=10)

    # Кнопка проверки
    btn_check = tk.Button(
        frame,
        text=checker.t("btn_check"),
        font=("Arial", 12),
        width=40
    )
    btn_check.pack(pady=(10, 5))

    # Кнопка открыть отчёт
    def open_report():
        report_path = os.path.abspath("nocheat_report.txt")
        if os.path.exists(report_path):
            try:
                os.startfile(report_path)  # Windows
            except AttributeError:
                subprocess.run(["xdg-open", report_path])  # Linux/macOS
        else:
            txt_output.insert(tk.END, checker.t("noreport") + "\n")

    btn_r = tk.Button(
        frame,
        text=checker.t("report-opn"),
        font=("Arial", 10),
        width=40,
        command=open_report
    )
    btn_r.pack(pady=(0, 5))

    # Поток на проверку
    def on_click():
        threading.Thread(target=checker.perform_check, args=(txt_output, btn_check), daemon=True).start()

    btn_check.config(command=on_click)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
