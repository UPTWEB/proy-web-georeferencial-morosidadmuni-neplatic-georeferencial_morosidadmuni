import tkinter as tk
import threading
from tkinter import messagebox, ttk

from src.controllers.usuario_controller import UsuarioController
from src.ui.modern_widgets import PALETTE, HoverButton


class UsuariosView(ttk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, style="App.TFrame")
        self.current_user = current_user
        self.controller = UsuarioController()
        self.role_options = []
        self.all_users = []
        self._refresh_token = 0
        self._build()
        self.refresh()

    def _build(self):
        header = tk.Frame(self, bg=PALETTE["app_bg"])
        header.pack(fill=tk.X, padx=6, pady=(0, 12))
        tk.Label(header, text="Usuarios", bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(header, text="Administracion de cuentas, roles y estado. Crear, modificar, desactivar y reasignar permisos.", bg=PALETTE["app_bg"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

        controls_row1 = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1, padx=14, pady=14)
        controls_row1.pack(fill=tk.X, padx=6, pady=(0, 8))
        controls_row1.columnconfigure(1, weight=1)

        tk.Label(controls_row1, text="Buscar", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 9)).grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        search = ttk.Entry(controls_row1, textvariable=self.search_var, style="Modern.TEntry")
        search.grid(row=0, column=1, sticky="ew", padx=(10, 12))
        self._search_after_id = None
        search.bind("<KeyRelease>", lambda _e: self._on_search_key())

        HoverButton(controls_row1, text="Recargar", command=self.refresh, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).grid(row=0, column=2, padx=4)
        HoverButton(controls_row1, text="Nuevo usuario", command=self.create_user_dialog, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 9), padx=12, pady=8).grid(row=0, column=3, padx=4)

        table_card = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 12))

        columns = ("id", "username", "nombre", "rol", "email", "activo", "bloqueado")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=14, style="Modern.Treeview")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview, style="Modern.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview, style="Modern.Horizontal.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack elements
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        headings = {
            "id": "ID",
            "username": "Usuario",
            "nombre": "Nombre completo",
            "rol": "Rol",
            "email": "Correo",
            "activo": "Activo",
            "bloqueado": "Bloqueado",
        }
        widths = {"id": 70, "username": 120, "nombre": 220, "rol": 150, "email": 220, "activo": 90, "bloqueado": 100}
        for key in columns:
            self.tree.heading(key, text=headings[key])
            self.tree.column(key, width=widths[key], anchor=tk.CENTER if key in {"id", "activo", "bloqueado"} else tk.W)
        self.tree.bind("<Double-1>", lambda _e: self.edit_selected())

        actions = tk.Frame(self, bg=PALETTE["app_bg"])
        actions.pack(fill=tk.X, padx=6)
        HoverButton(actions, text="Editar", command=self.edit_selected, bg=PALETTE["surface"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
        HoverButton(actions, text="Activar / Desactivar", command=self.toggle_selected, bg=PALETTE["surface"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
        HoverButton(actions, text="Restablecer clave", command=self.reset_password_selected, bg=PALETTE["surface"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
        HoverButton(actions, text="Bloquear", command=self.block_selected, bg=PALETTE["danger"], fg="#ffffff", hover_bg="#b91c1c", border=PALETTE["danger"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
        HoverButton(actions, text="Desbloquear", command=self.unblock_selected, bg=PALETTE["warning"], fg="#ffffff", hover_bg="#d97706", border=PALETTE["warning"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT)

    def _selected_id(self):
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def _selected_username(self):
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.item(selected[0], "values")[1]

    def _on_search_key(self):
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(200, self.load_users)

    def refresh(self):
        self._refresh_token += 1
        token = self._refresh_token
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree.insert("", tk.END, values=("...", "Cargando...", "", "", "", "", ""))
        threading.Thread(target=self._load_users_async, args=(token,), daemon=True).start()

    def _load_users_async(self, token):
        try:
            roles = self.controller.listar_roles()
            users = self.controller.listar_usuarios()
            self.after(0, lambda: self._apply_loaded_users(token, roles, users, None))
        except Exception as exc:
            self.after(0, lambda error=exc: self._apply_loaded_users(token, [], [], error))

    def _apply_loaded_users(self, token, roles, users, error):
        if token != self._refresh_token or not self.winfo_exists():
            return
        self.role_options = roles
        self.all_users = users
        if error:
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.tree.insert("", tk.END, values=("Error", str(error), "", "", "", "", ""))
            messagebox.showerror("Usuarios", f"No fue posible cargar usuarios.\n\nDetalle: {error}", parent=self)
            return
        self.load_users()

    def load_users(self):
        query = (self.search_var.get() or "").lower().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not hasattr(self, "all_users"):
            self.all_users = self.controller.listar_usuarios()
        rows = self.all_users
        count = 0
        for row in rows:
            if count >= 500:
                break
            text = f"{row['username']} {row['nombres']} {row['apellidos']} {row['rol_nombre']} {row.get('email') or ''}".lower()
            if query and query not in text:
                continue
            self.tree.insert(
                "",
                tk.END,
                values=(
                    row["id_usuario"],
                    row["username"],
                    f"{row['nombres']} {row['apellidos']}",
                    row["rol_nombre"],
                    row.get("email") or "No registrado",
                    "Sí" if row.get("activo") else "No",
                    "Sí" if row.get("bloqueado") else "No",
                ),
            )
            count += 1

    def create_user_dialog(self):
        self._user_dialog("Nuevo usuario")

    def edit_selected(self):
        user_id = self._selected_id()
        if not user_id:
            messagebox.showinfo("Usuarios", "Selecciona un usuario primero.", parent=self)
            return
        user = self.controller.obtener_usuario_por_id(user_id)
        if not user:
            messagebox.showerror("Usuarios", "No se pudo cargar el usuario seleccionado.", parent=self)
            return
        self._user_dialog("Editar usuario", user=user)

    def toggle_selected(self):
        user_id = self._selected_id()
        if not user_id:
            messagebox.showinfo("Usuarios", "Selecciona un usuario primero.", parent=self)
            return

        if user_id == self.current_user.id_usuario:
            messagebox.showerror("Operacion no permitida", "No puedes desactivar tu propia cuenta de administrador. Pide a otro administrador que realice esta operacion.", parent=self)
            return

        user = self.controller.obtener_usuario_por_id(user_id)
        if not user:
            messagebox.showerror("Usuarios", "No se pudo cargar el usuario seleccionado.", parent=self)
            return

        nuevo_estado = "ACTIVO" if not user.activo else "INACTIVO"
        if messagebox.askyesno("Confirmar cambio de estado", f"¿Deseas cambiar el estado de '{user.username}' a {nuevo_estado}?", parent=self):
            ok, msg = self.controller.cambiar_estado_usuario(user_id, not user.activo)
            if ok:
                self.refresh()
            messagebox.showinfo("Usuarios", msg, parent=self)

    def reset_password_selected(self):
        user_id = self._selected_id()
        if not user_id:
            messagebox.showinfo("Usuarios", "Selecciona un usuario primero.", parent=self)
            return
        user = self.controller.obtener_usuario_por_id(user_id)
        if not user:
            messagebox.showerror("Usuarios", "No se pudo cargar el usuario seleccionado.", parent=self)
            return
        self._reset_password_dialog(user)

    def unblock_selected(self):
        user_id = self._selected_id()
        if not user_id:
            messagebox.showinfo("Usuarios", "Selecciona un usuario primero.", parent=self)
            return
        user = self.controller.obtener_usuario_por_id(user_id)
        if not user:
            messagebox.showerror("Usuarios", "No se pudo cargar el usuario seleccionado.", parent=self)
            return
        if not user.bloqueado:
            messagebox.showinfo("Usuarios", "El usuario no se encuentra bloqueado.", parent=self)
            return
        if messagebox.askyesno("Confirmar desbloqueo", f"¿Deseas desbloquear la cuenta de '{user.username}'?", parent=self):
            ok, msg = self.controller.desbloquear_usuario(user_id)
            if ok:
                self.refresh()
            messagebox.showinfo("Usuarios", msg, parent=self)

    def block_selected(self):
        user_id = self._selected_id()
        if not user_id:
            messagebox.showinfo("Usuarios", "Selecciona un usuario primero.", parent=self)
            return
        if user_id == self.current_user.id_usuario:
            messagebox.showerror("Operacion no permitida", "No puedes bloquear tu propia cuenta.", parent=self)
            return
        user = self.controller.obtener_usuario_por_id(user_id)
        if not user:
            messagebox.showerror("Usuarios", "No se pudo cargar el usuario seleccionado.", parent=self)
            return
        if user.bloqueado:
            messagebox.showinfo("Usuarios", "El usuario ya se encuentra bloqueado.", parent=self)
            return
        if messagebox.askyesno("Confirmar bloqueo", f"¿Deseas bloquear la cuenta de '{user.username}'?", parent=self):
            ok, msg = self.controller.bloquear_usuario(user_id)
            if ok:
                self.refresh()
            messagebox.showinfo("Usuarios", msg, parent=self)

    def _reset_password_dialog(self, user):
        dialog = tk.Toplevel(self)
        dialog.title("Restablecer contraseña")
        dialog.minsize(400, 300)
        dialog.resizable(True, True)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=PALETTE["app_bg"])

        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)

        canvas = tk.Canvas(dialog, bg=PALETTE["app_bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=PALETTE["app_bg"])

        scrollable.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        frame = tk.Frame(scrollable, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1, padx=18, pady=18)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tk.Label(frame, text="Restablecer contraseña", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(frame, text=f"Usuario: {user.username}", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 14))

        tk.Label(frame, text="Nueva contraseña", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(10, 4))
        pass_entry = ttk.Entry(frame, show="*", style="Modern.TEntry")
        pass_entry.pack(fill=tk.X)

        tk.Label(frame, text="Confirmar contraseña", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(10, 4))
        confirm_entry = ttk.Entry(frame, show="*", style="Modern.TEntry")
        confirm_entry.pack(fill=tk.X)

        tk.Label(
            frame,
            text="La contraseña debe tener al menos 8 caracteres, una mayúscula y un número.",
            bg=PALETTE["surface"],
            fg=PALETTE["text_muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(8, 0))

        def apply():
            pwd = pass_entry.get()
            confirm = confirm_entry.get()
            if not pwd:
                messagebox.showerror("Validacion", "Ingresa la nueva contraseña.", parent=dialog)
                return
            if pwd != confirm:
                messagebox.showerror("Validacion", "Las contraseñas no coinciden.", parent=dialog)
                return
            ok, msg = self.controller.restablecer_contrasena(user.id_usuario, pwd)
            if ok:
                self.refresh()
                dialog.destroy()
            messagebox.showinfo("Usuarios", msg, parent=dialog)

        btn_frame = tk.Frame(frame, bg=PALETTE["surface"])
        btn_frame.pack(fill=tk.X, pady=(18, 0))
        HoverButton(btn_frame, text="Cancelar", command=dialog.destroy, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 10), padx=12, pady=9).pack(side=tk.LEFT)
        HoverButton(btn_frame, text="Aplicar cambio", command=apply, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=12, pady=9).pack(side=tk.RIGHT)

        dialog.update_idletasks()
        width = min(dialog.winfo_reqwidth() + 40, 520)
        height = min(dialog.winfo_reqheight(), 480)
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _user_dialog(self, title, user=None):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.minsize(460, 400)
        dialog.resizable(True, True)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=PALETTE["app_bg"])

        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)

        canvas = tk.Canvas(dialog, bg=PALETTE["app_bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=PALETTE["app_bg"])

        scrollable.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")

        frame = tk.Frame(scrollable, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1, padx=18, pady=18)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        tk.Label(frame, text=title, bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 15)).pack(anchor="w")

        def add_field(label, value=""):
            tk.Label(frame, text=label, bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(10, 4))
            entry = ttk.Entry(frame, style="Modern.TEntry")
            entry.insert(0, value or "")
            entry.pack(fill=tk.X)
            return entry

        username = add_field("Usuario", getattr(user, "username", "") if user else "")
        if user is not None:
            username.configure(state="disabled")
        nombres = add_field("Nombres", getattr(user, "nombres", "") if user else "")
        apellidos = add_field("Apellidos", getattr(user, "apellidos", "") if user else "")
        email = add_field("Correo", getattr(user, "email", "") if user else "")
        telefono = add_field("Teléfono", getattr(user, "telefono", "") if user else "")

        tk.Label(frame, text="Rol", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(10, 4))
        role_map = {r["nombre"]: r["id_rol"] for r in self.role_options}
        role_names = list(role_map.keys()) or ["Administrador", "Supervisor", "Notificador"]
        rol_cb = ttk.Combobox(frame, values=role_names, state="readonly", style="Modern.TCombobox")
        current_role = getattr(user, "id_rol", None)
        if current_role:
            matched = next((r["nombre"] for r in self.role_options if r["id_rol"] == current_role), role_names[0])
            rol_cb.set(matched)
        else:
            rol_cb.current(0)
        rol_cb.pack(fill=tk.X)

        password = None
        if user is None:
            tk.Label(frame, text="Contraseña", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(10, 4))
            password = ttk.Entry(frame, show="*", style="Modern.TEntry")
            password.pack(fill=tk.X)
            tk.Label(
                frame,
                text="Mínimo 8 caracteres, una mayúscula y un número.",
                bg=PALETTE["surface"],
                fg=PALETTE["text_muted"],
                font=("Segoe UI", 8),
            ).pack(anchor="w", pady=(4, 0))

        def save():
            role_id = role_map.get(rol_cb.get())
            if not all([username.get().strip(), nombres.get().strip(), apellidos.get().strip(), role_id]):
                messagebox.showerror("Validación", "Completa los campos obligatorios.", parent=dialog)
                return
            if email.get().strip() and "@" not in email.get().strip():
                messagebox.showerror("Validación", "Correo inválido.", parent=dialog)
                return
            if user is None:
                ok, msg = self.controller.crear_usuario(
                    username.get().strip(),
                    password.get(),
                    nombres.get().strip(),
                    apellidos.get().strip(),
                    role_id,
                    email=email.get().strip(),
                    telefono=telefono.get().strip(),
                )
            else:
                ok, msg = self.controller.actualizar_usuario(
                    user.id_usuario,
                    nombres.get().strip(),
                    apellidos.get().strip(),
                    role_id,
                    email=email.get().strip(),
                    telefono=telefono.get().strip(),
                )
            if ok:
                self.refresh()
                dialog.destroy()
            messagebox.showinfo("Usuarios", msg, parent=dialog)

        btn_frame = tk.Frame(frame, bg=PALETTE["surface"])
        btn_frame.pack(fill=tk.X, pady=(18, 0))
        HoverButton(btn_frame, text="Cancelar", command=dialog.destroy, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 10), padx=12, pady=9).pack(side=tk.LEFT)
        HoverButton(btn_frame, text="Guardar", command=save, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=18, pady=9).pack(side=tk.RIGHT)

        dialog.update_idletasks()
        width = min(dialog.winfo_reqwidth() + 40, 600)
        height = min(dialog.winfo_reqheight(), 640)
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def close(self):
        self.controller.close()
