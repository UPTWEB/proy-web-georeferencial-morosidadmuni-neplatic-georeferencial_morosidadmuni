#!/usr/bin/env python
import os
import sys
from datetime import datetime

import tkinter as tk
from tkinter import messagebox, ttk

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controllers.auth_controller import AuthController
from src.controllers.reporte_controller import ReporteController
from src.controllers.ruta_controller import RutaController
from src.controllers.usuario_controller import UsuarioController
from src.services.rbac_service import permissions_for_role
from src.ui.modern_widgets import (
    PALETTE,
    HoverButton,
    ScrollableFrame,
    animate_window_in,
    configure_base_theme,
    style_treeview,
)
from src.utils.logger import setup_logger
from src.views.etl_view import EtlView
from src.views.perfil_view import PerfilView
from src.views.reportes_view import ReportesView
from src.views.rutas_view import RutasView
from src.views.usuarios_view import UsuariosView

logger = setup_logger("neplatic-desktop")


ROL_NAMES = {
    1: "Administrador",
    2: "Supervisor",
    3: "Notificador",
    4: "Soporte TI",
}


class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Neplatic | Inicio de sesion")
        master.geometry("720x520")
        master.minsize(640, 480)
        master.configure(bg=PALETTE["app_bg"])
        master.resizable(True, True)

        master.update_idletasks()
        width = master.winfo_width()
        height = master.winfo_height()
        x = (master.winfo_screenwidth() // 2) - (width // 2)
        y = (master.winfo_screenheight() // 2) - (height // 2)
        master.geometry(f"+{x}+{y}")

        self._auth_controller = None
        self.setup_styles()
        self.create_login_ui()
        animate_window_in(self.master)

    @property
    def auth_controller(self):
        if self._auth_controller is None:
            self._auth_controller = AuthController()
        return self._auth_controller

    def setup_styles(self):
        self.style = ttk.Style()
        configure_base_theme(self.style)
        self.style.configure("Login.TFrame", background=PALETTE["app_bg"])
        self.style.configure("Login.TEntry", padding=10)

    def create_login_ui(self):
        shell = ttk.Frame(self.master, style="Login.TFrame", padding=24)
        shell.pack(fill=tk.BOTH, expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)

        card = tk.Frame(
            shell,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
        )
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)

        inner = tk.Frame(card, bg=PALETTE["surface"], padx=28, pady=28)
        inner.pack(fill=tk.BOTH, expand=True)
        inner.columnconfigure(0, weight=1)

        tk.Label(
            inner,
            text="Neplatic",
            bg=PALETTE["surface"],
            fg=PALETTE["text"],
            font=("Segoe UI Semibold", 24),
        ).pack(anchor="center")
        tk.Label(
            inner,
            text="Accede con tu usuario y contrasena",
            bg=PALETTE["surface"],
            fg=PALETTE["text_muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="center", pady=(4, 18))

        form = tk.Frame(inner, bg=PALETTE["surface"])
        form.pack(fill=tk.X)

        def field(label, show=None):
            tk.Label(
                form,
                text=label,
                bg=PALETTE["surface"],
                fg=PALETTE["text"],
                font=("Segoe UI Semibold", 10),
            ).pack(anchor="w", pady=(0, 6))
            shell_field = tk.Frame(
                form,
                bg=PALETTE["surface"],
                highlightbackground=PALETTE["border"],
                highlightthickness=1,
            )
            shell_field.pack(fill=tk.X, pady=(0, 14))
            entry = ttk.Entry(shell_field, font=("Segoe UI", 11), style="Modern.TEntry", show=show)
            entry.pack(fill=tk.X, padx=2, pady=2)
            return entry

        self.username_entry = field("Usuario")
        self.password_entry = field("Contrasena", show="*")

        buttons = tk.Frame(inner, bg=PALETTE["surface"])
        buttons.pack(fill=tk.X, pady=(6, 0))

        btn_ingresar = HoverButton(
            buttons,
            text="Ingresar",
            command=self.login,
            bg=PALETTE["accent"],
            hover_bg=PALETTE["accent_hover"],
            border=PALETTE["accent"],
            font=("Segoe UI Semibold", 11),
            pady=14,
        )
        btn_ingresar.pack(fill=tk.X, ipady=2)

        btn_salir = HoverButton(
            buttons,
            text="Salir",
            command=self.master.destroy,
            bg=PALETTE["danger"],
            fg="#ffffff",
            hover_bg="#b91c1c",
            active_bg="#991b1b",
            border=PALETTE["danger"],
            font=("Segoe UI Semibold", 11),
            pady=14,
        )
        btn_salir.pack(fill=tk.X, pady=(10, 0), ipady=2)

        tk.Label(
            inner,
            text="Neplatic desktop",
            bg=PALETTE["surface"],
            fg=PALETTE["text_muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(18, 0))

        self.master.bind("<Return>", lambda _e: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error de validacion", "Por favor, ingrese usuario y contrasena.")
            return

        user = self.auth_controller.login(username, password)
        if user:
            self.master.withdraw()
            self.open_main_window(user)
        else:
            messagebox.showerror("Error de autenticacion", "Credenciales invalidas o usuario inactivo.")

    def open_main_window(self, user):
        try:
            main_root = tk.Toplevel(self.master)
            MainWindow(main_root, user, self)
        except Exception as exc:
            logger.exception("No se pudo abrir la ventana principal")
            try:
                self.master.deiconify()
            except Exception:
                pass
            messagebox.showerror(
                "Error al iniciar el panel",
                "No fue posible cargar la ventana principal.\n\n"
                f"Detalle tecnico: {exc}",
            )


class MainWindow:
    def __init__(self, master, user, login_window_obj):
        self.master = master
        self.user = user
        self.login_window_obj = login_window_obj
        self.auth_controller = login_window_obj.auth_controller
        self.nav_buttons = {}
        self.role_name = ROL_NAMES.get(self.user.id_rol, "Usuario")
        self.user_permissions = []

        self._view_cache = {}
        self._current_view_name = None
        self._current_view_widget = None
        self._ruta_controller = None
        self._report_controller = None
        self._redis_consumer = None

        self._load_profile_and_permissions()
        self._setup_window()
        self._setup_styles()
        self._create_shell()
        self._start_event_listener()
        self.show_view("dashboard")

        self.master.protocol("WM_DELETE_WINDOW", self.confirmar_salida)
        animate_window_in(self.master)

    def _start_event_listener(self):
        from src.services.redis_consumer import RedisConsumer
        from src.ui.modern_widgets import ToastNotification

        def on_event(payload):
            event_type = payload.get('event_type')
            if event_type in ['visita_registrada', 'notificacion_creada']:
                msg = f"Nueva actualización: {event_type.replace('_', ' ')}"
                # Run on main UI thread
                self.master.after(0, lambda: ToastNotification(self.master, msg))

        self._redis_consumer = RedisConsumer(callback=on_event)
        self._redis_consumer.start()

    @property
    def ruta_controller(self):
        if self._ruta_controller is None:
            self._ruta_controller = RutaController(self.user)
        return self._ruta_controller

    @property
    def report_controller(self):
        if self._report_controller is None:
            self._report_controller = ReporteController()
        return self._report_controller

    def _load_profile_and_permissions(self):
        uc = UsuarioController()
        try:
            perfil = uc.obtener_perfil(self.user.id_usuario)
            if perfil:
                usuario_db, rol_nombre = perfil
                self.role_name = rol_nombre or self.role_name
                self.user.nombres = usuario_db.nombres
                self.user.apellidos = usuario_db.apellidos
                self.user.email = usuario_db.email
                self.user.telefono = usuario_db.telefono
            self.user_permissions = permissions_for_role(
                self.role_name,
                uc.obtener_permisos_usuario(self.user.id_rol),
            )
            logger.info("Permisos cargados para %s: %s", self.user.username, self.user_permissions)
        except Exception as exc:
            logger.error("Error cargando permisos RBAC: %s", exc)
            self.user_permissions = permissions_for_role(self.role_name, None)
        finally:
            try:
                uc.close()
            except Exception:
                pass

    def _setup_window(self):
        self.master.title("Neplatic | Panel administrativo")
        self.master.geometry("1240x760")
        self.master.minsize(1080, 680)
        self.master.configure(bg=PALETTE["app_bg"])

        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f"+{x}+{y}")
        self.master.state('zoomed')

    def _setup_styles(self):
        self.style = ttk.Style()
        configure_base_theme(self.style)
        self.style.configure("App.TFrame", background=PALETTE["app_bg"])
        self.style.configure("Header.TFrame", background=PALETTE["surface"], relief="flat")
        self.style.configure("Body.TFrame", background=PALETTE["app_bg"])
        self.style.configure("Content.TFrame", background=PALETTE["app_bg"])

    def _create_shell(self):
        self.root = ttk.Frame(self.master, style="App.TFrame")
        self.root.pack(fill=tk.BOTH, expand=True)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)

        self._create_header()
        self._create_body()

    def _create_header(self):
        header = tk.Frame(
            self.root,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["border"],
            highlightthickness=1,
            height=76,
        )
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=PALETTE["surface"])
        left.pack(side=tk.LEFT, fill=tk.Y, padx=22)
        tk.Label(left, text="Neplatic", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w", pady=(16, 0))
        tk.Label(left, text="Panel administrativo de escritorio", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w")

        right = tk.Frame(header, bg=PALETTE["surface"])
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=18)

        self.user_chip = HoverButton(
            right,
            text=f"{self.user.nombres} {self.user.apellidos}".strip(),
            command=lambda: self.show_view("perfil"),
            bg=PALETTE["surface_soft"],
            fg=PALETTE["text"],
            hover_bg=PALETTE["surface_alt"],
            active_bg=PALETTE["surface_alt"],
            border=PALETTE["border"],
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=8,
        )
        self.user_chip.pack(side=tk.LEFT, padx=(0, 10), pady=14)

        HoverButton(
            right,
            text="Cerrar sesion",
            command=self.cerrar_sesion,
            bg=PALETTE["danger"],
            hover_bg="#b91c1c",
            border=PALETTE["danger"],
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=8,
        ).pack(side=tk.LEFT, pady=14)

    def _create_body(self):
        body = ttk.Frame(self.root, style="Body.TFrame")
        body.grid(row=1, column=0, columnspan=2, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(body, bg=PALETTE["sidebar"], width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.rowconfigure(2, weight=1)

        self.content = tk.Frame(body, bg=PALETTE["app_bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.content_scroll = ScrollableFrame(self.content, bg=PALETTE["app_bg"])
        self.content_scroll.pack(fill=tk.BOTH, expand=True)
        self.content_host = self.content_scroll.scrollable_frame

        self._build_sidebar()

    def _build_sidebar(self):
        top = tk.Frame(self.sidebar, bg=PALETTE["sidebar"], padx=18, pady=18)
        top.grid(row=0, column=0, sticky="ew")
        tk.Label(top, text="NEPLATIC", bg=PALETTE["sidebar"], fg="#38bdf8", font=("Segoe UI Semibold", 9)).pack(anchor="w")
        tk.Label(top, text="Administracion unificada", bg=PALETTE["sidebar"], fg=PALETTE["text"], font=("Segoe UI Semibold", 17)).pack(anchor="w", pady=(6, 2))
        tk.Label(top, text="Navegacion rapida para el panel.", bg=PALETTE["sidebar"], fg=PALETTE["text_muted"], wraplength=220, justify="left", font=("Segoe UI", 9)).pack(anchor="w")

        nav = tk.Frame(self.sidebar, bg=PALETTE["sidebar"], padx=12, pady=10)
        nav.grid(row=1, column=0, sticky="new")
        nav.columnconfigure(0, weight=1)

        self._add_nav_button(nav, "dashboard", "Inicio", lambda: self.show_view("dashboard"))
        self._add_nav_button(nav, "perfil", "Mi perfil", lambda: self.show_view("perfil"))

        if "rutas:visualizar_propias" in self.user_permissions:
            self._add_nav_button(nav, "rutas", "Mis rutas", lambda: self.show_view("rutas"))
            self._add_nav_button(nav, "deudas", "Deudas", lambda: self.show_view("deudas"))

        if "usuarios:gestionar" in self.user_permissions:
            self._add_nav_button(nav, "usuarios", "Usuarios", lambda: self.show_view("usuarios"))
        if "etl:ejecutar" in self.user_permissions:
            self._add_nav_button(nav, "etl", "Proceso ETL", lambda: self.show_view("etl"))
        if "reportes:descargar" in self.user_permissions:
            self._add_nav_button(nav, "reportes", "Reportes", lambda: self.show_view("reportes"))

        footer = tk.Frame(self.sidebar, bg=PALETTE["sidebar"], padx=18, pady=16)
        footer.grid(row=3, column=0, sticky="sew")
        tk.Label(footer, text="Sesion activa", bg=PALETTE["sidebar"], fg=PALETTE["text_muted"], font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(footer, text="Panel listo para operar", bg=PALETTE["sidebar"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(4, 0))

    def _add_nav_button(self, parent, key, text, command):
        btn = HoverButton(
            parent,
            text=text,
            command=command,
            bg=PALETTE["sidebar"],
            fg="#cbd5e1",
            hover_bg=PALETTE["sidebar_soft"],
            border=PALETTE["sidebar"],
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=11,
            anchor="w",
            justify="left",
        )
        btn.pack(fill=tk.X, pady=4)
        self.nav_buttons[key] = btn
        return btn

    def _set_active_nav(self, key):
        for nav_key, btn in self.nav_buttons.items():
            if nav_key == key:
                btn._bg = PALETTE["accent"]
                btn._hover_bg = PALETTE["accent_hover"]
                btn._border = PALETTE["accent"]
                btn.configure(bg=PALETTE["accent"], fg="#ffffff", highlightbackground=PALETTE["accent"])
            else:
                btn._bg = PALETTE["sidebar"]
                btn._hover_bg = PALETTE["sidebar_soft"]
                btn._border = PALETTE["sidebar"]
                btn.configure(bg=PALETTE["sidebar"], fg=PALETTE["text_muted"], highlightbackground=PALETTE["sidebar"])

    def _hide_current_view(self):
        if self._current_view_widget is not None:
            self._current_view_widget.pack_forget()

    def update_header_user_info(self):
        self.master.title(f"Neplatic | {self.user.nombres} {self.user.apellidos}".strip())
        self.user_chip.config(text=f"{self.user.nombres} {self.user.apellidos}".strip())

    def _require_permission(self, view_name):
        permisos_vistas = {
            "rutas": "rutas:visualizar_propias",
            "deudas": "rutas:visualizar_propias",
            "usuarios": "usuarios:gestionar",
            "etl": "etl:ejecutar",
            "reportes": "reportes:descargar",
        }
        req = permisos_vistas.get(view_name)
        if req and req not in self.user_permissions:
            messagebox.showerror("Acceso denegado", "No tiene permisos para acceder a este modulo.")
            return False
        return True

    def show_view(self, view_name):
        if not self._require_permission(view_name):
            return

        if self._current_view_name == view_name and self._current_view_widget is not None:
            return

        self._set_active_nav(view_name)
        self._hide_current_view()

        cached = self._view_cache.get(view_name)
        if cached is not None:
            cached.pack(fill=tk.BOTH, expand=True)
            self._current_view_widget = cached
            self._current_view_name = view_name
            self.content_scroll.canvas.yview_moveto(0)
            if hasattr(cached, "refresh"):
                self.master.after(10, cached.refresh)
            return

        try:
            loader_map = {
                "dashboard": self._load_dashboard_view,
                "perfil": self._load_profile_view,
                "rutas": self._load_rutas_view,
                "deudas": self._load_deudas_view,
                "usuarios": self._load_usuarios_view,
                "etl": self._load_etl_view,
                "reportes": self._load_reportes_view,
            }
            loader = loader_map.get(view_name)
            if loader is None:
                return

            view = loader()
            self._view_cache[view_name] = view
            self._current_view_widget = view
            self._current_view_name = view_name
            self.content_scroll.canvas.yview_moveto(0)
        except Exception as exc:
            logger.exception("Error abriendo la vista %s", view_name)
            messagebox.showerror("Error de vista", f"No fue posible cargar el modulo '{view_name}'.\n\nDetalle: {exc}", parent=self.master)

    def _section_header(self, parent, title, subtitle=None):
        header = tk.Frame(parent, bg=PALETTE["app_bg"])
        header.pack(fill=tk.X, padx=24, pady=(22, 14))
        tk.Label(header, text=title, bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, bg=PALETTE["app_bg"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))
        return header

    def _surface(self, parent, padding=18):
        frame = tk.Frame(parent, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        inner = tk.Frame(frame, bg=PALETTE["surface"], padx=padding, pady=padding)
        inner.pack(fill=tk.BOTH, expand=True)
        return frame, inner

    def _stat_card(self, parent, title, value, meta, accent):
        card = tk.Frame(parent, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        top = tk.Frame(card, bg=PALETTE["surface"], padx=16, pady=14)
        top.pack(fill=tk.BOTH, expand=True)
        tk.Label(top, text=title, bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w")
        val_lbl = tk.Label(top, text=value, bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 24))
        val_lbl.pack(anchor="w", pady=(8, 2))
        tk.Label(top, text=meta, bg=PALETTE["surface"], fg=accent, font=("Segoe UI Semibold", 9)).pack(anchor="w")
        return card, val_lbl

    def _load_dashboard_view(self):
        container = tk.Frame(self.content_host, bg=PALETTE["app_bg"])
        container.pack(fill=tk.BOTH, expand=True)

        self._section_header(container, "Bienvenido al panel", "Vista general con acceso rapido a las funciones mas usadas.")

        hero_outer = tk.Frame(container, bg=PALETTE["app_bg"])
        hero_outer.pack(fill=tk.X, padx=24, pady=(0, 16))
        hero_outer.columnconfigure(0, weight=2)
        hero_outer.columnconfigure(1, weight=1)

        hero, hero_inner = self._surface(hero_outer, padding=22)
        hero.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        hero_inner.columnconfigure(0, weight=1)

        tk.Label(hero_inner, text=f"Hola, {self.user.nombres}", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 22)).pack(anchor="w")
        tk.Label(hero_inner, text="Neplatic esta listo para organizar rutas, notificaciones y seguimiento operativo.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], wraplength=520, justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 16))

        hero_actions = tk.Frame(hero_inner, bg=PALETTE["surface"])
        hero_actions.pack(fill=tk.X)
        HoverButton(
            hero_actions,
            text="Mi perfil",
            command=lambda: self.show_view("perfil"),
            bg=PALETTE["accent"],
            hover_bg=PALETTE["accent_hover"],
            border=PALETTE["accent"],
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=9,
        ).pack(side=tk.LEFT, padx=(0, 10))
        HoverButton(
            hero_actions,
            text="Sincronizar",
            command=self.ejecutar_sincronizacion_manual,
            bg=PALETTE["surface_soft"],
            fg=PALETTE["text"],
            hover_bg=PALETTE["surface_alt"],
            active_bg=PALETTE["surface_alt"],
            border=PALETTE["border"],
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=9,
        ).pack(side=tk.LEFT)

        side_card, side_inner = self._surface(hero_outer, padding=18)
        side_card.grid(row=0, column=1, sticky="nsew")
        side_inner.columnconfigure(0, weight=1)
        tk.Label(side_inner, text="Estado del usuario", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(side_inner, text=self.role_name, bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 16)).pack(anchor="w", pady=(6, 0))
        tk.Label(side_inner, text="Acceso activo y navegacion habilitada.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 0))
        last_access = self.user.ultimo_acceso.strftime("%d/%m/%Y %H:%M") if getattr(self.user, "ultimo_acceso", None) else datetime.now().strftime("%d/%m/%Y %H:%M")
        tk.Label(side_inner, text=f"Ultimo acceso: {last_access}", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(18, 0))

        tk.Label(side_inner, text="Permisos activos:", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(10, 0))
        for p in self.user_permissions[:6]:  # Limit to avoid overflow
            tk.Label(side_inner, text=f"• {p}", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 8)).pack(anchor="w")
        if len(self.user_permissions) > 6:
            tk.Label(side_inner, text=f"...y {len(self.user_permissions)-6} más.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 8)).pack(anchor="w")

        stats = tk.Frame(container, bg=PALETTE["app_bg"])
        stats.pack(fill=tk.X, padx=24, pady=(0, 12))
        stats.columnconfigure((0, 1, 2, 3), weight=1)

        self._dashboard_stat_labels = []
        placeholders = [
            ("Rutas activas", "Cargando...", "Resumen de rutas asignadas", PALETTE["accent"]),
            ("Efectividad", "Cargando...", "Tasa de efectividad", PALETTE["success"]),
            ("Deuda pendiente", "Cargando...", "Monto total por recaudar", PALETTE["warning"]),
            ("Permisos", str(len(self.user_permissions)), "Privilegios activos del rol", PALETTE["accent_hover"]),
        ]
        for idx, (title, value, meta, accent) in enumerate(placeholders):
            card, val_lbl = self._stat_card(stats, title, value, meta, accent)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))
            self._dashboard_stat_labels.append(val_lbl)

        quick, quick_inner = self._surface(container, padding=18)
        quick.pack(fill=tk.X, padx=24, pady=(0, 16))
        tk.Label(quick_inner, text="Acciones rapidas", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 13)).pack(anchor="w")
        tk.Label(quick_inner, text="Atajos para entrar a los modulos mas usados.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 12))

        row = tk.Frame(quick_inner, bg=PALETTE["surface"])
        row.pack(fill=tk.X)
        HoverButton(row, text="Perfil", command=lambda: self.show_view("perfil"), bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg=PALETTE["surface_alt"], active_bg=PALETTE["surface_alt"], border=PALETTE["border"], font=("Segoe UI Semibold", 9), pady=10).pack(side=tk.LEFT, padx=(0, 10))
        if "rutas:visualizar_propias" in self.user_permissions:
            HoverButton(row, text="Rutas", command=lambda: self.show_view("rutas"), bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg=PALETTE["surface_alt"], active_bg=PALETTE["surface_alt"], border=PALETTE["border"], font=("Segoe UI Semibold", 9), pady=10).pack(side=tk.LEFT, padx=(0, 10))
        if "notificaciones:registrar" in self.user_permissions:
            HoverButton(row, text="Notificar", command=lambda: self.show_view("notificar"), bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg=PALETTE["surface_alt"], active_bg=PALETTE["surface_alt"], border=PALETTE["border"], font=("Segoe UI Semibold", 9), pady=10).pack(side=tk.LEFT, padx=(0, 10))
        if "usuarios:gestionar" in self.user_permissions:
            HoverButton(row, text="Usuarios", command=lambda: self.show_view("usuarios"), bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg=PALETTE["surface_alt"], active_bg=PALETTE["surface_alt"], border=PALETTE["border"], font=("Segoe UI Semibold", 9), pady=10).pack(side=tk.LEFT, padx=(0, 10))
        if "reportes:descargar" in self.user_permissions:
            HoverButton(row, text="Reportes", command=lambda: self.show_view("reportes"), bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg=PALETTE["surface_alt"], active_bg=PALETTE["surface_alt"], border=PALETTE["border"], font=("Segoe UI Semibold", 9), pady=10).pack(side=tk.LEFT, padx=(0, 10))

        self.master.after(30, self._load_dashboard_data)
        container.refresh = lambda: self._load_dashboard_data()
        return container

    def _load_dashboard_data(self):
        import threading
        
        def fetch_data():
            route_count = 0
            avance = "0.0%"
            deuda_total = "S/ 0.00"

            try:
                routes = self.ruta_controller.listar_rutas_usuario()
                route_count = len(routes)
            except Exception as exc:
                logger.error("Error cargando rutas del dashboard: %s", exc)

            try:
                gerencial = self.report_controller.dashboard_gerencial()
                efectividad = gerencial.get("tasa_efectividad_global", 0)
                avance = f"{efectividad}%"
                monto = gerencial.get("deuda_total_pendiente", 0)
                deuda_total = f"S/ {monto:,.2f}"
            except Exception as exc:
                logger.error("Error cargando KPIs del dashboard: %s", exc)
                
            def update_ui():
                if len(self._dashboard_stat_labels) >= 4:
                    self._dashboard_stat_labels[0].config(text=str(route_count))
                    self._dashboard_stat_labels[1].config(text=avance)
                    self._dashboard_stat_labels[2].config(text=deuda_total)
                    self._dashboard_stat_labels[3].config(text=str(len(self.user_permissions)))
            
            self.master.after(0, update_ui)

        threading.Thread(target=fetch_data, daemon=True).start()

    def _load_profile_view(self):
        container = tk.Frame(self.content_host, bg=PALETTE["app_bg"])
        container.pack(fill=tk.BOTH, expand=True)
        profile_shell = tk.Frame(container, bg=PALETTE["app_bg"])
        profile_shell.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        view = PerfilView(profile_shell, self.user, on_update_callback=self.update_header_user_info)
        view.pack(fill=tk.BOTH, expand=True)
        container.refresh = view.load_data
        return container

    def _load_usuarios_view(self):
        container = tk.Frame(self.content_host, bg=PALETTE["app_bg"])
        container.pack(fill=tk.BOTH, expand=True)
        view = UsuariosView(container, self.user)
        view.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        container.refresh = view.refresh
        return container

    def _load_etl_view(self):
        container = tk.Frame(self.content_host, bg=PALETTE["app_bg"])
        container.pack(fill=tk.BOTH, expand=True)
        view = EtlView(container, self.user)
        view.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        return container

    def _load_reportes_view(self):
        container = tk.Frame(self.content_host, bg=PALETTE["app_bg"])
        container.pack(fill=tk.BOTH, expand=True)
        view = ReportesView(container, self.user)
        view.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        container.refresh = view.refresh
        return container

    def _load_rutas_view(self):
        container = tk.Frame(self.content_host, bg=PALETTE["app_bg"])
        container.pack(fill=tk.BOTH, expand=True)
        view = RutasView(container, self.user, mode="rutas")
        view.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        container.refresh = view.refresh
        return container

    def _load_deudas_view(self):
        from src.views.rutas_view import RutasView
        container = tk.Frame(self.content_host, bg=PALETTE["app_bg"])
        container.pack(fill=tk.BOTH, expand=True)
        view = RutasView(container, self.user, mode="deudas")
        view.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        container.refresh = view.refresh
        return container

    def ejecutar_sincronizacion_manual(self):
        from src.services.sync_service import SyncService

        sync_serv = SyncService()
        messagebox.showinfo("Sincronizacion", "Procesando cola local...", parent=self.master)
        res = sync_serv.procesar_cola_pendiente()
        if res["status"] == "success":
            messagebox.showinfo("Sincronizacion", res["message"], parent=self.master)
        elif res["status"] == "empty":
            messagebox.showinfo("Sincronizacion", "No hay datos pendientes en la cola local.", parent=self.master)
        elif res["status"] == "offline":
            messagebox.showerror("Conectividad", "El sistema central sigue inaccesible. Se conservan los datos localmente.", parent=self.master)
        else:
            messagebox.showwarning("Sincronizacion parcial", res["message"], parent=self.master)

    def cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesion", "¿Esta seguro de que desea cerrar la sesion actual?"):
            logger.info("Iniciando proceso de cierre de sesion...")
            try:
                self.auth_controller.logout(self.user.token)
            except Exception as exc:
                logger.error("Error cerrando sesion en la BD: %s", exc)
            try:
                self.ruta_controller.close()
            except Exception:
                pass
            try:
                self.report_controller.close()
            except Exception:
                pass
            self.master.destroy()
            self.login_window_obj.username_entry.delete(0, tk.END)
            self.login_window_obj.password_entry.delete(0, tk.END)
            self.login_window_obj.master.deiconify()

    def confirmar_salida(self):
        if messagebox.askyesno(
            "Salir",
            "¿Esta seguro de que desea cerrar la aplicacion?\nSu sesion activa sera cerrada en el servidor.",
        ):
            try:
                self.auth_controller.logout(self.user.token)
            except Exception as exc:
                logger.error("Error al cerrar sesion al salir: %s", exc)
            try:
                self.ruta_controller.close()
            except Exception:
                pass
            try:
                self.report_controller.close()
            except Exception:
                pass
            if self._redis_consumer:
                self._redis_consumer.stop()
            self.master.destroy()
            self.login_window_obj.master.destroy()


def main():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
