import os
import json
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

try:
    from PIL import Image, ImageTk
except Exception:  # pragma: no cover
    Image = None
    ImageTk = None

from src.controllers.usuario_controller import UsuarioController
from src.ui.modern_widgets import PALETTE, HoverButton


class PerfilView(ttk.Frame):
    def __init__(self, parent, user, on_update_callback=None):
        super().__init__(parent, style="App.TFrame")
        self.user = user
        self.on_update_callback = on_update_callback
        self.controller = UsuarioController()
        self.avatar_cache_file = Path.cwd() / "scratch" / "profile_avatars.json"
        self.avatar_path = (
            getattr(user, "foto_url", None)
            or getattr(user, "avatar_path", None)
            or self._load_cached_avatar_path()
        )

        self._build_view()
        self.load_data()

    def _build_view(self):
        self.columnconfigure(0, weight=1)

        header = tk.Frame(self, bg=PALETTE["app_bg"])
        header.pack(fill=tk.X, padx=6, pady=(0, 14))
        tk.Label(header, text="Mi perfil", bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(header, text="Tu información de cuenta y permisos de acceso.", bg=PALETTE["app_bg"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

        self.summary = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        self.summary.pack(fill=tk.X, padx=6, pady=(0, 14))

        summary_inner = tk.Frame(self.summary, bg=PALETTE["surface"], padx=18, pady=18)
        summary_inner.pack(fill=tk.BOTH, expand=True)
        summary_inner.columnconfigure(1, weight=1)

        avatar_wrap = tk.Frame(summary_inner, bg=PALETTE["surface"])
        avatar_wrap.grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 18))
        self.avatar_label = tk.Label(avatar_wrap, bg="#dbeafe", fg="#1d4ed8", font=("Segoe UI Semibold", 20), width=4, height=2)
        self.avatar_label.pack()
        self.avatar_caption = tk.Label(avatar_wrap, text="Foto opcional", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 8))
        self.avatar_caption.pack(pady=(6, 0))

        self.lbl_fullname = tk.Label(summary_inner, text="", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 20))
        self.lbl_fullname.grid(row=0, column=1, sticky="w")
        self.lbl_role = tk.Label(summary_inner, text="", bg="#dbeafe", fg="#1d4ed8", font=("Segoe UI Semibold", 9), padx=10, pady=4)
        self.lbl_role.grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.lbl_status = tk.Label(summary_inner, text="", bg=PALETTE["surface"], fg=PALETTE["success"], font=("Segoe UI Semibold", 9))
        self.lbl_status.grid(row=2, column=1, sticky="w", pady=(10, 0))

        self.details = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        self.details.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 14))
        details_inner = tk.Frame(self.details, bg=PALETTE["surface"], padx=18, pady=18)
        details_inner.pack(fill=tk.BOTH, expand=True)
        details_inner.columnconfigure(1, weight=1)

        self.detail_labels = {}
        rows = [
            ("Usuario", "username"),
            ("Nombres", "nombres"),
            ("Apellidos", "apellidos"),
            ("Correo", "email"),
            ("Teléfono", "telefono"),
            ("Fecha de registro", "fecha_registro"),
            ("Último acceso", "ultimo_acceso"),
            ("Estado", "estado"),
        ]
        for idx, (label, key) in enumerate(rows):
            tk.Label(details_inner, text=f"{label}:", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI Semibold", 10)).grid(row=idx, column=0, sticky="w", pady=6, padx=(0, 16))
            value = tk.Label(details_inner, text="", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI", 10), anchor="w", justify="left")
            value.grid(row=idx, column=1, sticky="w", pady=6)
            self.detail_labels[key] = value

        permissions_card = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        permissions_card.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 14))
        permissions_inner = tk.Frame(permissions_card, bg=PALETTE["surface"], padx=18, pady=18)
        permissions_inner.pack(fill=tk.BOTH, expand=True)
        tk.Label(permissions_inner, text="Permisos asignados", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.lbl_permisos = tk.Label(permissions_inner, text="", bg=PALETTE["surface"], fg=PALETTE["text_muted"], justify="left", wraplength=700, font=("Segoe UI", 9))
        self.lbl_permisos.pack(anchor="w", pady=(8, 0))

        actions = tk.Frame(self, bg=PALETTE["app_bg"])
        actions.pack(fill=tk.X, padx=6, pady=(0, 4))
        HoverButton(actions, text="Editar perfil", command=self.open_edit_dialog, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=14, pady=10).pack(side=tk.LEFT, padx=(0, 10))
        HoverButton(actions, text="Cambiar contraseña", command=self.open_password_dialog, bg=PALETTE["surface"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 10), padx=14, pady=10).pack(side=tk.LEFT)

    def _initials(self, usuario_db):
        nombres = (usuario_db.nombres or "").strip()
        apellidos = (usuario_db.apellidos or "").strip()
        initials = (nombres[:1] + apellidos[:1]).upper()
        return initials or "N"

    def _load_cached_avatar_path(self):
        try:
            if not self.avatar_cache_file.exists():
                return None
            with self.avatar_cache_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data.get(str(self.user.id_usuario))
        except Exception:
            return None

    def _save_cached_avatar_path(self, path):
        try:
            self.avatar_cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if self.avatar_cache_file.exists():
                try:
                    with self.avatar_cache_file.open("r", encoding="utf-8") as fh:
                        data = json.load(fh)
                except Exception:
                    data = {}
            data[str(self.user.id_usuario)] = path
            with self.avatar_cache_file.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_avatar(self, usuario_db):
        candidate = self.avatar_path
        if not candidate:
            return None
        if not os.path.exists(candidate) or not Image or not ImageTk:
            return None
        try:
            img = Image.open(candidate).convert("RGBA").resize((84, 84))
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def load_data(self):
        resultado = self.controller.obtener_perfil(self.user.id_usuario)
        if not resultado:
            messagebox.showerror("Perfil", "No fue posible cargar tu perfil.")
            return

        usuario_db, rol_nombre = resultado
        fecha_reg = usuario_db.fecha_creacion.strftime("%d/%m/%Y %H:%M") if usuario_db.fecha_creacion else "N/A"
        ultimo_acc = usuario_db.ultimo_acceso.strftime("%d/%m/%Y %H:%M:%S") if usuario_db.ultimo_acceso else "N/A"

        estado_txt = "ACTIVO"
        estado_color = PALETTE["success"]
        if usuario_db.bloqueado:
            estado_txt = "BLOQUEADO"
            estado_color = PALETTE["danger"]
        elif not usuario_db.activo:
            estado_txt = "INACTIVO"
            estado_color = PALETTE["warning"]

        self.lbl_fullname.config(text=f"{usuario_db.nombres} {usuario_db.apellidos}".strip())
        self.lbl_role.config(text=rol_nombre)
        self.lbl_status.config(text=estado_txt, fg=estado_color)

        self.detail_labels["username"].config(text=usuario_db.username)
        self.detail_labels["nombres"].config(text=usuario_db.nombres or "No registrado")
        self.detail_labels["apellidos"].config(text=usuario_db.apellidos or "No registrado")
        self.detail_labels["email"].config(text=usuario_db.email or "No registrado")
        self.detail_labels["telefono"].config(text=usuario_db.telefono or "No registrado")
        self.detail_labels["fecha_registro"].config(text=fecha_reg)
        self.detail_labels["ultimo_acceso"].config(text=ultimo_acc)
        self.detail_labels["estado"].config(text=estado_txt, fg=estado_color)

        avatar_image = self._load_avatar(usuario_db)
        if avatar_image:
            self.avatar_label.config(image=avatar_image, text="")
            self.avatar_label.image = avatar_image
        else:
            self.avatar_label.config(image="", text=self._initials(usuario_db))

        self.lbl_permisos.config(text=self.get_permisos_descripcion(usuario_db.id_rol))

        self.user.nombres = usuario_db.nombres
        self.user.apellidos = usuario_db.apellidos
        self.user.email = usuario_db.email
        self.user.telefono = usuario_db.telefono

        if self.on_update_callback:
            self.on_update_callback()

    def get_permisos_descripcion(self, id_rol):
        permisos = self.controller.obtener_permisos_usuario(id_rol)
        if not permisos:
            return "Sin permisos asignados."

        nombres_permisos = {
            "usuarios:gestionar": "Gestión de usuarios",
            "usuarios:crear": "Crear usuarios",
            "etl:ejecutar": "Ejecutar ETL",
            "rutas:administrar": "Administrar rutas",
            "rutas:visualizar_propias": "Visualizar rutas propias",
            "notificaciones:registrar": "Registrar notificaciones",
            "reportes:descargar": "Descargar reportes",
            "auditoria:visualizar": "Visualizar auditoría",
        }
        desc = [nombres_permisos.get(p, p) for p in permisos]
        return "• " + "\n• ".join(desc)

    def _dialog(self, title, size):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.minsize(420, 320)
        dialog.configure(bg=PALETTE["app_bg"])
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        dialog.update_idletasks()
        w, h = map(int, size.split("x"))
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        return dialog

    def open_edit_dialog(self):
        dialog = self._dialog("Editar perfil", "520x430")
        frame = tk.Frame(dialog, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1, padx=18, pady=18)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tk.Label(frame, text="Editar perfil", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(frame, text="Solo los campos visibles pueden editarse.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 14))

        fields = {}
        for label, key, value in [
            ("Nombres", "nombres", self.user.nombres or ""),
            ("Apellidos", "apellidos", self.user.apellidos or ""),
            ("Correo", "email", self.user.email or ""),
            ("Teléfono", "telefono", self.user.telefono or ""),
        ]:
            tk.Label(frame, text=label, bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(0, 6))
            entry = ttk.Entry(frame, style="Modern.TEntry")
            entry.insert(0, value)
            entry.pack(fill=tk.X, pady=(0, 10))
            fields[key] = entry

        photo_row = tk.Frame(frame, bg=PALETTE["surface"])
        photo_row.pack(fill=tk.X, pady=(2, 10))
        tk.Label(photo_row, text="Foto opcional", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w")
        photo_path = tk.StringVar(value=self.avatar_path or "")
        tk.Entry(photo_row, textvariable=photo_path, state="readonly", relief="flat", bg="#f8fafc").pack(fill=tk.X, pady=(6, 6))

        def choose_photo():
            path = filedialog.askopenfilename(
                parent=dialog,
                title="Seleccionar foto",
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.webp"), ("Todos", "*.*")],
            )
            if path:
                photo_path.set(path)

        HoverButton(photo_row, text="Elegir foto", command=choose_photo, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(anchor="w")

        def save():
            nombres = fields["nombres"].get().strip()
            apellidos = fields["apellidos"].get().strip()
            email = fields["email"].get().strip()
            telefono = fields["telefono"].get().strip()

            if not nombres or not apellidos:
                messagebox.showerror("Validación", "Nombres y apellidos son obligatorios.", parent=dialog)
                return
            if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                messagebox.showerror("Validación", "El correo no tiene un formato válido.", parent=dialog)
                return
            if telefono and not re.match(r"^\+?[\d\s-]{7,15}$", telefono):
                messagebox.showerror("Validación", "El teléfono no tiene un formato válido.", parent=dialog)
                return

            if messagebox.askyesno("Confirmar", "¿Desea guardar los cambios de perfil?", parent=dialog):
                ok = self.controller.actualizar_perfil(self.user.id_usuario, nombres, apellidos, email, telefono)
                if ok:
                    self.avatar_path = photo_path.get() or self.avatar_path
                    if self.avatar_path:
                        self._save_cached_avatar_path(self.avatar_path)
                    self.load_data()
                    dialog.destroy()
                    messagebox.showinfo("Éxito", "Perfil actualizado correctamente.", parent=self)
                else:
                    messagebox.showerror("Error", "No fue posible actualizar el perfil.", parent=dialog)

        HoverButton(frame, text="Guardar cambios", command=save, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=14, pady=10).pack(anchor="e", pady=(8, 0))

    def open_password_dialog(self):
        dialog = self._dialog("Cambiar contraseña", "500x360")
        frame = tk.Frame(dialog, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1, padx=18, pady=18)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        tk.Label(frame, text="Cambiar contraseña", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 15)).pack(anchor="w")
        tk.Label(frame, text="Se solicita la contraseña actual para confirmar identidad.", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 14))

        entry_actual = ttk.Entry(frame, show="*", style="Modern.TEntry")
        entry_nueva = ttk.Entry(frame, show="*", style="Modern.TEntry")
        entry_confirmar = ttk.Entry(frame, show="*", style="Modern.TEntry")

        for label, entry in [
            ("Contraseña actual", entry_actual),
            ("Nueva contraseña", entry_nueva),
            ("Confirmar nueva contraseña", entry_confirmar),
        ]:
            tk.Label(frame, text=label, bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(0, 6))
            entry.pack(fill=tk.X, pady=(0, 10))

        def change():
            actual = entry_actual.get()
            nueva = entry_nueva.get()
            confirmar = entry_confirmar.get()

            if not actual or not nueva or not confirmar:
                messagebox.showerror("Validación", "Todos los campos son obligatorios.", parent=dialog)
                return
            if nueva != confirmar:
                messagebox.showerror("Validación", "La nueva contraseña y su confirmación no coinciden.", parent=dialog)
                return
            if actual == nueva:
                messagebox.showerror("Validación", "La nueva contraseña debe ser diferente a la actual.", parent=dialog)
                return

            ok, msg = self.controller.cambiar_contrasena(self.user.id_usuario, actual, nueva)
            if ok:
                messagebox.showinfo("Éxito", msg, parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Error", msg, parent=dialog)

        HoverButton(frame, text="Actualizar contraseña", command=change, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=14, pady=10).pack(anchor="e", pady=(8, 0))

    def close(self):
        self.controller.close()
