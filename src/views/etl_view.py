import os
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

from src.controllers.etl_runner import run_etl
from src.ui.modern_widgets import PALETTE, HoverButton


class EtlView(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg=PALETTE["app_bg"])
        self.current_user = current_user
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=PALETTE["app_bg"])
        header.pack(fill=tk.X, padx=8, pady=(0, 12))
        tk.Label(header, text="Proceso ETL", bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(header, text="Extraccion, transformacion y carga de deudas desde Oracle hacia PostgreSQL.", bg=PALETTE["app_bg"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

        card = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        inner = tk.Frame(card, bg=PALETTE["surface"], padx=18, pady=18)
        inner.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(inner, bg=PALETTE["surface"])
        top.pack(fill=tk.X)
        tk.Label(top, text="Estado de configuracion", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 12)).pack(anchor="w")

        self.status_label = tk.Label(top, text="", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9))
        self.status_label.pack(anchor="w", pady=(4, 12))

        self.status_label.config(text="Listo para ejecutar (Modo Simulado)")

        buttons = tk.Frame(inner, bg=PALETTE["surface"])
        buttons.pack(fill=tk.X, pady=(0, 12))
        HoverButton(
            buttons,
            text="Ejecutar ETL ahora",
            command=self.run_now,
            bg=PALETTE["accent"],
            hover_bg=PALETTE["accent_hover"],
            border=PALETTE["accent"],
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=10,
        ).pack(side=tk.LEFT)

        self.output = ScrolledText(
            inner,
            height=16,
            wrap="word",
            bg=PALETTE["surface_soft"],
            fg=PALETTE["text"],
            insertbackground=PALETTE["text"],
            relief="flat",
            font=("Consolas", 10),
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self._log("ETL listo. Presiona el boton para ejecutar.")

    def _log(self, text):
        self.output.insert("end", f"{text}\n")
        self.output.see("end")

    def run_now(self):
        if not messagebox.askyesno("Confirmar ETL", "¿Desea ejecutar el proceso ETL ahora?", parent=self):
            return
        self._log("Iniciando ETL...")
        self.status_label.config(text="Ejecutando...")
        threading.Thread(target=self._run_etl_async, daemon=True).start()

    def _run_etl_async(self):
        try:
            ok, msg = run_etl()
        except Exception as exc:
            ok, msg = False, str(exc)
        self.after(0, lambda: self._finish_etl(ok, msg))

    def _finish_etl(self, ok, msg):
        if ok:
            self._log("ETL completado correctamente.")
            self.status_label.config(text="Proceso completado correctamente.")
            messagebox.showinfo("ETL", "Proceso completado correctamente.", parent=self)
        else:
            self._log(f"ETL termino con errores. Detalle: {msg}")
            self.status_label.config(text="El proceso termino con errores.")
            messagebox.showerror("ETL", f"No fue posible completar el proceso ETL.\n\nCausa: {msg}", parent=self)
