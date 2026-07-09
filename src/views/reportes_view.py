from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.controllers.reporte_controller import ReporteController
from src.services.report_generator import ReportGenerator
from src.ui.modern_widgets import PALETTE, HoverButton, ScrollableFrame, style_treeview


class ReportesView(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg=PALETTE["app_bg"])
        self.current_user = current_user
        self.controller = ReporteController()
        self.exporter = ReportGenerator(str(Path.cwd() / "scratch" / "reports"))
        self.data = {}
        self._refresh_token = 0
        self._build()
        self.refresh()

    def _build(self):
        header = tk.Frame(self, bg=PALETTE["app_bg"])
        header.pack(fill=tk.X, padx=8, pady=(0, 12))
        tk.Label(header, text="Reportes", bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(header, text="Tablas resumen, exportacion en Excel y PDF.", bg=PALETTE["app_bg"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

        actions = tk.Frame(self, bg=PALETTE["app_bg"])
        actions.pack(fill=tk.X, padx=8, pady=(0, 10))
        
        # Búsqueda
        tk.Label(actions, text="Buscar:", bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(actions, textvariable=self.search_var, style="Modern.TEntry", width=25)
        search_entry.pack(side=tk.LEFT, padx=(0, 12))
        search_entry.bind("<KeyRelease>", lambda _e: self._apply_search())
        
        HoverButton(actions, text="Actualizar", command=self.refresh, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
        HoverButton(actions, text="Exportar Excel", command=self.export_excel, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
        HoverButton(actions, text="Exportar PDF", command=self.export_pdf, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT)

        self.summary_frame = tk.Frame(self, bg=PALETTE["app_bg"])
        self.summary_frame.pack(fill=tk.X, padx=8, pady=(0, 10))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.tab_dashboard = tk.Frame(self.notebook, bg=PALETTE["surface"])
        self.tab_sector = tk.Frame(self.notebook, bg=PALETTE["surface"])
        self.tab_top = tk.Frame(self.notebook, bg=PALETTE["surface"])
        self.tab_evolution = tk.Frame(self.notebook, bg=PALETTE["surface"])

        self.notebook.add(self.tab_dashboard, text="Resumen")
        self.notebook.add(self.tab_sector, text="Por sector")
        self.notebook.add(self.tab_top, text="Top deudores")
        self.notebook.add(self.tab_evolution, text="Evolucion")

        self.dashboard_scroll = ScrollableFrame(self.tab_dashboard, bg=PALETTE["surface"])
        self.dashboard_scroll.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.dashboard_content = self.dashboard_scroll.scrollable_frame

        self._build_tree(self.tab_sector, "sector")
        self._build_tree(self.tab_top, "top")
        self._build_tree(self.tab_evolution, "evolution")

    def _build_tree(self, parent, kind):
        frame = tk.Frame(parent, bg=PALETTE["surface"])
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree = ttk.Treeview(frame, show="headings", style="Modern.Treeview")
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview, style="Modern.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview, style="Modern.Horizontal.TScrollbar")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        
        style_treeview(tree, ttk.Style())
        setattr(self, f"{kind}_tree", tree)

    @staticmethod
    def _rows(rows):
        result = []
        for row in rows or []:
            if isinstance(row, dict):
                result.append(row)
            elif hasattr(row, "_mapping"):
                result.append(dict(row._mapping))
            else:
                result.append(dict(row))
        return result

    def refresh(self):
        self._refresh_token += 1
        token = self._refresh_token
        self.data = {"dashboard": {}, "top_deudores": [], "sector": [], "evolucion": []}
        self._render_loading()
        threading.Thread(target=self._load_reports_async, args=(token,), daemon=True).start()

    def _render_loading(self):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        card = tk.Frame(self.summary_frame, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(fill=tk.X)
        tk.Label(card, text="Cargando reportes...", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=14)
        for tree in (self.sector_tree, self.top_tree, self.evolution_tree):
            for item in tree.get_children():
                tree.delete(item)
            tree["columns"] = ["mensaje"]
            tree.heading("mensaje", text="Estado")
            tree.column("mensaje", width=220, anchor="w")
            tree.insert("", "end", values=("Cargando...",))

    def _load_reports_async(self, token):
        try:
            data = self.controller.exportable_dashboard()
            self.after(0, lambda: self._apply_loaded_reports(token, data, None))
        except Exception as exc:
            self.after(0, lambda error=exc: self._apply_loaded_reports(token, {"dashboard": {}, "top_deudores": [], "sector": [], "evolucion": []}, error))

    def _apply_loaded_reports(self, token, data, error):
        if token != self._refresh_token or not self.winfo_exists():
            return
        self.data = data
        if error:
            messagebox.showerror("Reportes", f"No fue posible cargar los reportes.\n\nDetalle: {error}", parent=self)
        self._render_summary()
        self._apply_search()

    def _apply_search(self):
        query = self.search_var.get().lower()
        
        def filter_rows(rows):
            if not query:
                return rows
            filtered = []
            for row in rows:
                if any(query in str(v).lower() for v in row.values()):
                    filtered.append(row)
            return filtered

        self._render_tree(self.sector_tree, filter_rows(self._rows(self.data.get("sector"))), ["codigo_sector", "nombre_sector", "total_deuda", "saldo_pendiente"])
        self._render_tree(self.top_tree, filter_rows(self._rows(self.data.get("top_deudores"))), None)
        self._render_tree(self.evolution_tree, filter_rows(self._rows(self.data.get("evolucion"))), None)

    def _render_summary(self):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        cards = []
        dashboard = self.data.get("dashboard") or {}
        keys = list(dashboard.items())[:4]
        if keys:
            for idx, (key, value) in enumerate(keys):
                card = tk.Frame(self.summary_frame, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
                card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0))
                tk.Label(card, text=str(key).replace("_", " ").title(), bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(12, 4))
                tk.Label(card, text=str(value), bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 20)).pack(anchor="w", padx=14, pady=(0, 12))
                cards.append(card)
        else:
            card = tk.Frame(self.summary_frame, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
            card.pack(fill=tk.X)
            tk.Label(card, text="No hay resumen disponible en las vistas de base de datos.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=14)

        for widget in self.dashboard_content.winfo_children():
            widget.destroy()

        if dashboard:
            row_frame = None
            col_idx = 0
            for i, (key, value) in enumerate(dashboard.items()):
                if i % 3 == 0:
                    row_frame = tk.Frame(self.dashboard_content, bg=PALETTE["surface"])
                    row_frame.pack(fill=tk.X, pady=(0, 10))
                    row_frame.columnconfigure((0, 1, 2), weight=1)
                    col_idx = 0
                
                card = tk.Frame(row_frame, bg=PALETTE["app_bg"], highlightbackground=PALETTE["border"], highlightthickness=1)
                card.grid(row=0, column=col_idx, sticky="nsew", padx=5)
                
                tk.Label(card, text=str(key).replace("_", " ").title(), bg=PALETTE["app_bg"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(12, 4))
                tk.Label(card, text=str(value), bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 16)).pack(anchor="w", padx=14, pady=(0, 12))
                col_idx += 1
        else:
            tk.Label(self.dashboard_content, text="No hay detalles para mostrar.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=14)

    def _render_tree(self, tree, rows, explicit_columns):
        for item in tree.get_children():
            tree.delete(item)

        if not rows:
            cols = explicit_columns or ["mensaje"]
            tree["columns"] = cols
            for col in cols:
                tree.heading(col, text=col.replace("_", " ").title())
                tree.column(col, width=180, anchor="w")
            tree.insert("", "end", values=("Sin datos disponibles",))
            return

        columns = explicit_columns or list(rows[0].keys())
        tree["columns"] = columns
        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=160, anchor="w")

        for row in rows:
            tree.insert("", "end", values=[row.get(col, "") for col in columns])

    def export_excel(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar reporte Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
        )
        if not path:
            return
        sections = {
            "resumen": [self.data.get("dashboard") or {}],
            "sector": self._rows(self.data.get("sector")),
            "top_deudores": self._rows(self.data.get("top_deudores")),
            "evolucion": self._rows(self.data.get("evolucion")),
        }
        saved = self.exporter.export_excel(path, sections)
        messagebox.showinfo("Reportes", f"Reporte exportado correctamente.\n\n{saved}", parent=self)

    def export_pdf(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar reporte PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not path:
            return
        sections = {
            "resumen": [self.data.get("dashboard") or {}],
            "sector": self._rows(self.data.get("sector")),
            "top_deudores": self._rows(self.data.get("top_deudores")),
            "evolucion": self._rows(self.data.get("evolucion")),
        }
        saved = self.exporter.export_pdf(path, "Reporte Neplatic", sections)
        messagebox.showinfo("Reportes", f"Reporte exportado correctamente.\n\n{saved}", parent=self)

    def close(self):
        try:
            self.controller.close()
        except Exception:
            pass
