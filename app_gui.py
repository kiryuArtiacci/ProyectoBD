import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import db_manager

# --- NUEVA PALETA DE COLORES "NEON GRID" ---
APP_BG_COLOR = "#020617"
FRAME_BG_COLOR = "#0F172A"
ENTRY_BG_COLOR = "#1E293B"
BUTTON_SECONDARY_COLOR = "#334155"
BUTTON_SECONDARY_HOVER = "#475569"
ACCENT_PURPLE = "#A855F7"
ACCENT_PINK = "#EC4899"
TEXT_COLOR = "#E2E8F0"

# --- CONSTANTES DE ESTILO ---
FONT_NORMAL = ("Segoe UI", 12)
FONT_BOLD = ("Segoe UI", 12, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_MENU_TITLE = ("Segoe UI", 16, "bold")


# --- FUNCIÓN DE UTILIDAD (PARA EL TREEVIEW) ---
def crear_tabla(parent, cols, widths={}):
    tree = ttk.Treeview(parent, columns=cols, show="headings", style="Treeview")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=widths.get(col, 120), anchor="w")
    return tree


# --- CLASES DE FORMULARIO (BASE) ---
class FormularioBase(ctk.CTkToplevel):
    def __init__(self, parent, controller, title):
        super().__init__(parent, fg_color=APP_BG_COLOR)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.controller = controller
        self.entries = {}
        self.resizable(False, False)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

    def crear_campo(self, frame, texto_label, tipo="entry", **kwargs):
        row = ctk.CTkFrame(frame, fg_color="transparent")
        label = ctk.CTkLabel(
            row,
            width=150,
            text=f"{texto_label}:",
            anchor="w",
            font=FONT_NORMAL,
            text_color=TEXT_COLOR,  # CORREGIDO
        )
        widget = None
        if tipo == "entry":
            widget = ctk.CTkEntry(
                row,
                width=300,
                font=FONT_NORMAL,
                fg_color=ENTRY_BG_COLOR,
                border_color=BUTTON_SECONDARY_COLOR,
                text_color=TEXT_COLOR,
            )
            if "Contraseña" in texto_label:
                widget.configure(show="*")
        elif tipo == "combobox":
            widget = ctk.CTkComboBox(
                row,
                width=300,
                state="readonly",
                font=FONT_NORMAL,
                values=kwargs.get("values", []),
                fg_color=ENTRY_BG_COLOR,
                border_color=BUTTON_SECONDARY_COLOR,
                button_color=BUTTON_SECONDARY_COLOR,
                button_hover_color=BUTTON_SECONDARY_HOVER,
                text_color=TEXT_COLOR,
            )
        elif tipo == "textbox":
            widget = ctk.CTkTextbox(
                row,
                width=300,
                height=80,
                font=FONT_NORMAL,
                fg_color=ENTRY_BG_COLOR,
                border_color=BUTTON_SECONDARY_COLOR,
                text_color=TEXT_COLOR,
            )
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=8)
        label.pack(side=tk.LEFT)
        if widget:
            widget.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        self.entries[texto_label.replace(":", "")] = widget
        return widget


# --- CLASES DE FORMULARIO (ESPECÍFICAS) ---
class CrearUsuarioWindow(FormularioBase):
    def __init__(
        self,
        parent,
        controller,
        is_first_user=False,
        on_success_callback=None,
        **kwargs,
    ):
        super().__init__(parent, controller, "Crear Nuevo Usuario")
        self.campos_especificos = {
            "Postulante": ["Nombres", "Apellidos", "Cédula", "Teléfono", "Universidad"],
            "Empresa": [
                "Nombre Empresa",
                "RIF",
                "Sector",
                "Persona de Contacto",
                "Teléfono de Contacto",
                "Email de Contacto",
            ],
            "HiringGroup": [],
        }
        self.on_success_callback = on_success_callback
        self.universidades = db_manager.get_catalogo(
            "Universidades", "ID_Universidad", "Nombre_Universidad"
        )
        self.uni_map = {
            u["Nombre_Universidad"]: u["ID_Universidad"]
            for u in self.universidades or []
        }
        top_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        tipo_usuario_combo = self.crear_campo(
            top_frame,
            "Tipo de Usuario",
            "combobox",
            values=list(self.campos_especificos.keys()),
        )
        tipo_usuario_combo.configure(command=self.actualizar_campos)
        top_frame.pack(fill="x")
        if is_first_user:
            self.title("Crear Primer Usuario Administrador")
            tipo_usuario_combo.set("HiringGroup")
            tipo_usuario_combo.configure(state="disabled")
        self.form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.form_frame.pack(pady=10, fill="x")
        ctk.CTkButton(
            self.main_frame,
            text="Crear Usuario",
            command=self.crear,
            corner_radius=10,
            height=40,
            fg_color=ACCENT_PURPLE,
            text_color=TEXT_COLOR,
            hover_color=ACCENT_PINK,
        ).pack(pady=15)
        self.actualizar_campos(None)

    def actualizar_campos(self, event=None):
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        keys_to_remove = [
            k for k in self.entries.keys() if k not in ["Tipo de Usuario"]
        ]
        [self.entries.pop(k, None) for k in keys_to_remove]
        self.crear_campo(self.form_frame, "Email")
        self.crear_campo(self.form_frame, "Contraseña")
        tipo_usuario = self.entries["Tipo de Usuario"].get()
        for field in self.campos_especificos.get(tipo_usuario, []):
            if field == "Universidad":
                self.crear_campo(
                    self.form_frame, field, "combobox", values=list(self.uni_map.keys())
                )
            else:
                self.crear_campo(self.form_frame, field)

    def crear(self):
        tipo_usuario = self.entries["Tipo de Usuario"].get()
        if not tipo_usuario:
            messagebox.showerror(
                "Error", "Debes seleccionar un tipo de usuario.", parent=self
            )
            return
        datos = {
            k: v.get("1.0", "end-1c").strip()
            if isinstance(v, ctk.CTkTextbox)
            else v.get()
            for k, v in self.entries.items()
        }
        datos_db = {
            "Email": datos.get("Email"),
            "Contraseña": datos.get("Contraseña"),
            "Nombres": datos.get("Nombres"),
            "Apellidos": datos.get("Apellidos"),
            "Cédula": datos.get("Cédula"),
            "Teléfono": datos.get("Teléfono"),
            "ID_Universidad": self.uni_map.get(datos.get("Universidad")),
            "Nombre Empresa": datos.get("Nombre Empresa"),
            "RIF": datos.get("RIF"),
            "Sector": datos.get("Sector"),
            "Persona de Contacto": datos.get("Persona de Contacto"),
            "Teléfono de Contacto": datos.get("Teléfono de Contacto"),
            "Email de Contacto": datos.get("Email de Contacto"),
        }
        self.controller.config(cursor="watch")
        self.controller.update_idletasks()
        success, message = db_manager.registrar_usuario_db(tipo_usuario, datos_db)
        self.controller.config(cursor="")
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            if self.on_success_callback:
                self.on_success_callback()
            self.destroy()
        else:
            messagebox.showerror("Error al Crear", message, parent=self)


class ActualizarUsuarioWindow(FormularioBase):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, controller, "Editar Mi Perfil")
        self.tipo_usuario = self.controller.rol_actual
        self.id_usuario = self.controller.usuario_actual["ID_Usuario"]
        form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        if self.tipo_usuario in ["Postulante", "Contratado"]:
            self.universidades = db_manager.get_catalogo(
                "Universidades", "ID_Universidad", "Nombre_Universidad"
            )
            self.uni_map = {
                u["Nombre_Universidad"]: u["ID_Universidad"]
                for u in self.universidades or []
            }
            self.inv_uni_map = {v: k for k, v in self.uni_map.items()}
            self.crear_campo(form_frame, "Nombres")
            self.crear_campo(form_frame, "Apellidos")
            self.crear_campo(form_frame, "Teléfono")
            self.crear_campo(
                form_frame, "Universidad", "combobox", values=list(self.uni_map.keys())
            )
            self.populate_postulante()
        elif self.tipo_usuario == "Empresa":
            self.crear_campo(form_frame, "Nombre Empresa")
            self.crear_campo(form_frame, "Sector")
            self.crear_campo(form_frame, "Persona de Contacto")
            self.crear_campo(form_frame, "Teléfono de Contacto")
            self.crear_campo(form_frame, "Email de Contacto")
            self.populate_empresa()
        self.crear_campo(form_frame, "Nueva Contraseña (opcional)")
        form_frame.pack(pady=10, fill="x")
        ctk.CTkButton(
            self.main_frame,
            text="Guardar Cambios",
            command=self.actualizar,
            corner_radius=10,
            height=40,
            fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_PINK,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=15)

    def populate_postulante(self):
        datos = db_manager.get_single_postulante(self.id_usuario)
        if not datos:
            return
        self.entries["Nombres"].insert(0, datos["Nombres"] or "")
        self.entries["Apellidos"].insert(0, datos["Apellidos"] or "")
        self.entries["Teléfono"].insert(0, datos["Telefono"] or "")
        self.entries["Universidad"].set(
            self.inv_uni_map.get(datos["ID_Universidad"], "")
        )

    def populate_empresa(self):
        datos = db_manager.get_single_empresa(self.id_usuario)
        if not datos:
            return
        self.entries["Nombre Empresa"].insert(0, datos["Nombre_Empresa"] or "")
        self.entries["Sector"].insert(0, datos["Sector_Industrial"] or "")
        self.entries["Persona de Contacto"].insert(0, datos["Persona_Contacto"] or "")
        self.entries["Teléfono de Contacto"].insert(0, datos["Telefono_Contacto"] or "")
        self.entries["Email de Contacto"].insert(0, datos["Email_Contacto"] or "")

    def actualizar(self):
        datos = {
            k: v.get("1.0", "end-1c").strip()
            if isinstance(v, ctk.CTkTextbox)
            else v.get()
            for k, v in self.entries.items()
        }
        datos_db = {k.strip().replace(" (opcional)", ""): v for k, v in datos.items()}
        if self.tipo_usuario in ["Postulante", "Contratado"]:
            datos_db["ID_Universidad"] = self.uni_map.get(datos_db.get("Universidad"))
        if "Nueva Contraseña" in datos_db and datos_db["Nueva Contraseña"]:
            datos_db["Contraseña"] = datos_db.pop("Nueva Contraseña")
        self.controller.config(cursor="watch")
        self.controller.update_idletasks()
        success, message = db_manager.actualizar_usuario_db(
            self.id_usuario, self.tipo_usuario, datos_db
        )
        self.controller.config(cursor="")
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error al Actualizar", message, parent=self)


class GestionarExperienciaWindow(FormularioBase):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, controller, "Gestionar Mi Experiencia Laboral")
        self.id_postulante = self.controller.usuario_actual["ID_Usuario"]
        add_frame = ctk.CTkFrame(self.main_frame, fg_color=FRAME_BG_COLOR)
        add_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(
            add_frame,
            text="Añadir/Editar Experiencia",
            font=FONT_BOLD,
            text_color=TEXT_COLOR,
        ).pack(  # CORREGIDO
            pady=(5, 10)
        )
        self.crear_campo(add_frame, "Empresa")
        self.crear_campo(add_frame, "Cargo")
        self.crear_campo(add_frame, "Fecha Inicio (YYYY-MM-DD)")
        self.crear_campo(add_frame, "Fecha Fin (YYYY-MM-DD, opcional)")
        self.crear_campo(add_frame, "Descripción", "textbox")
        ctk.CTkButton(
            add_frame,
            text="Agregar Experiencia",
            command=self.agregar,
            corner_radius=10,
            fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_PINK,
            text_color=TEXT_COLOR,
        ).pack(pady=10)
        tree_frame = ctk.CTkFrame(self.main_frame, fg_color=FRAME_BG_COLOR)
        tree_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(
            tree_frame, text="Mis Experiencias", font=FONT_BOLD, text_color=TEXT_COLOR
        ).pack(  # CORREGIDO
            pady=(5, 10)
        )
        self.tree = crear_tabla(
            tree_frame, ("ID", "Empresa", "Cargo", "Inicio", "Fin"), widths={"ID": 30}
        )
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkButton(
            tree_frame,
            text="Eliminar Seleccionada",
            command=self.eliminar,
            corner_radius=10,
            fg_color=BUTTON_SECONDARY_COLOR,
            hover_color=BUTTON_SECONDARY_HOVER,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="e", padx=10)
        self.populate_tree()

    def populate_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for exp in db_manager.get_experiencias_db(self.id_postulante) or []:
            self.tree.insert(
                "",
                "end",
                values=(
                    exp["ID_Experiencia"],
                    exp["Empresa"],
                    exp["Cargo_Ocupado"],
                    exp["Fecha_Inicio"],
                    exp["Fecha_Fin"] or "Actual",
                ),
            )

    def agregar(self):
        datos = {
            k: v.get("1.0", "end-1c").strip()
            if isinstance(v, ctk.CTkTextbox)
            else v.get()
            for k, v in self.entries.items()
        }
        if (
            not datos["Empresa"]
            or not datos["Cargo"]
            or not datos["Fecha Inicio (YYYY-MM-DD)"]
        ):
            messagebox.showerror(
                "Error",
                "Empresa, Cargo y Fecha de Inicio son obligatorios.",
                parent=self,
            )
            return
        self.controller.config(cursor="watch")
        self.controller.update_idletasks()
        success, msg = db_manager.crear_experiencia_db(self.id_postulante, datos)
        self.controller.config(cursor="")
        if success:
            self.populate_tree()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def eliminar(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Selección Requerida",
                "Selecciona una experiencia para eliminar.",
                parent=self,
            )
            return
        id_exp = self.tree.item(selected[0])["values"][0]
        if messagebox.askyesno(
            "Confirmar", "¿Seguro que quieres eliminar esta experiencia?", parent=self
        ):
            self.controller.config(cursor="watch")
            self.controller.update_idletasks()
            success, msg = db_manager.eliminar_experiencia_db(id_exp)
            self.controller.config(cursor="")
            if success:
                self.populate_tree()
            else:
                messagebox.showerror("Error", msg, parent=self)


class GestionCatalogoWindow(FormularioBase):
    def __init__(self, parent, controller, title, tabla, id_col, nombre_col, **kwargs):
        super().__init__(parent, controller, title)
        self.tabla, self.id_col, self.nombre_col = tabla, id_col, nombre_col
        add_frame = ctk.CTkFrame(self.main_frame, fg_color=FRAME_BG_COLOR)
        add_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(
            add_frame,
            text=f"Agregar Nuevo/a {title.split(' ')[-1]}",
            font=FONT_BOLD,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=(5, 10))
        entry_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        entry_frame.pack(fill="x", padx=10)
        ctk.CTkLabel(
            entry_frame, text="Nombre:", font=FONT_NORMAL, text_color=TEXT_COLOR
        ).pack(  # CORREGIDO
            side=tk.LEFT, padx=5
        )
        self.new_entry = ctk.CTkEntry(
            entry_frame,
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
            text_color=TEXT_COLOR,
        )
        self.new_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        ctk.CTkButton(
            entry_frame,
            text="Agregar",
            command=self.agregar,
            width=80,
            fg_color=BUTTON_SECONDARY_COLOR,
            hover_color=BUTTON_SECONDARY_HOVER,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side=tk.LEFT, padx=5)
        tree_frame = ctk.CTkFrame(self.main_frame, fg_color=FRAME_BG_COLOR)
        tree_frame.pack(fill="both", expand=True, pady=10)
        self.tree = crear_tabla(
            tree_frame, ("ID", "Nombre"), widths={"ID": 50, "Nombre": 400}
        )
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        action_frame.pack(fill="x", pady=5, padx=10, anchor="e")
        ctk.CTkButton(
            action_frame,
            text="Editar",
            command=self.editar,
            width=80,
            fg_color=BUTTON_SECONDARY_COLOR,
            hover_color=BUTTON_SECONDARY_HOVER,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side="right", padx=5)
        ctk.CTkButton(
            action_frame,
            text="Eliminar",
            command=self.eliminar,
            width=80,
            fg_color=ACCENT_PINK,
            hover_color=ACCENT_PURPLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side="right")
        self.populate_tree()

    def populate_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in db_manager.get_catalogo(self.tabla, self.id_col, self.nombre_col):
            self.tree.insert(
                "", "end", values=(item[self.id_col], item[self.nombre_col])
            )

    def agregar(self):
        new_val = self.new_entry.get()
        if not new_val:
            messagebox.showwarning("Campo Vacío", "Introduce un nombre.", parent=self)
            return
        success, msg = db_manager.crear_item_catalogo(
            self.tabla, self.nombre_col, new_val
        )
        if success:
            self.new_entry.delete(0, tk.END)
            self.populate_tree()
        messagebox.showinfo("Resultado", msg, parent=self)

    def editar(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Selección Requerida",
                "Selecciona un elemento para editar.",
                parent=self,
            )
            return
        item_id, nombre_actual = self.tree.item(selected[0])["values"]
        dialog = ctk.CTkInputDialog(text="Introduce el nuevo nombre:", title="Editar")
        nuevo_nombre = dialog.get_input()
        if nuevo_nombre and nuevo_nombre.strip() and nuevo_nombre != nombre_actual:
            success, msg = db_manager.actualizar_item_catalogo(
                self.tabla, self.id_col, self.nombre_col, item_id, nuevo_nombre
            )
            if success:
                self.populate_tree()
            messagebox.showinfo("Resultado", msg, parent=self)

    def eliminar(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Selección Requerida",
                "Selecciona un elemento para eliminar.",
                parent=self,
            )
            return
        item_id, nombre = self.tree.item(selected[0])["values"]
        if messagebox.askyesno(
            "Confirmar", f"¿Seguro que quieres eliminar '{nombre}'?", parent=self
        ):
            success, msg = db_manager.eliminar_item_catalogo(
                self.tabla, self.id_col, item_id
            )
            if success:
                self.populate_tree()
            messagebox.showinfo("Resultado", msg, parent=self)


class CrearVacanteWindow(FormularioBase):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, controller, "Crear Nueva Vacante")
        self.on_success_callback = kwargs.get("on_success_callback")
        self.profesiones = db_manager.get_catalogo(
            "Profesiones", "ID_Profesion", "Nombre_Profesion"
        )
        self.prof_map = {
            p["Nombre_Profesion"]: p["ID_Profesion"] for p in self.profesiones or []
        }
        if not self.profesiones:
            messagebox.showwarning(
                "Advertencia", "No hay profesiones registradas.", parent=self
            )
            self.destroy()
            return
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.crear_campo(frame, "Cargo Vacante")
        self.crear_campo(frame, "Descripción del Perfil", "textbox")
        self.crear_campo(frame, "Salario Ofrecido")
        self.crear_campo(
            frame,
            "Profesión Requerida",
            tipo="combobox",
            values=list(self.prof_map.keys()),
        )
        frame.pack(pady=10, fill="x")
        ctk.CTkButton(
            self.main_frame,
            text="Guardar Vacante",
            command=self.guardar,
            height=40,
            corner_radius=10,
            fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_PINK,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=15)

    def guardar(self):
        datos = {
            k: v.get("1.0", "end-1c").strip()
            if isinstance(v, ctk.CTkTextbox)
            else v.get()
            for k, v in self.entries.items()
        }
        try:
            salario = float(datos.get("Salario Ofrecido", 0))
            if salario <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror(
                "Entrada no válida",
                "El salario debe ser un número positivo.",
                parent=self,
            )
            return
        id_profesion = self.prof_map.get(datos.get("Profesión Requerida"))
        if not all([datos.get("Cargo Vacante"), id_profesion]):
            messagebox.showerror(
                "Error", "Cargo y Profesión son obligatorios.", parent=self
            )
            return
        success, message = db_manager.crear_vacante_db(
            self.controller.usuario_actual["ID_Usuario"],
            datos["Cargo Vacante"],
            datos["Descripción del Perfil"],
            salario,
            id_profesion,
        )
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            if self.on_success_callback:
                self.on_success_callback()
            self.destroy()
        else:
            messagebox.showerror("Error al Guardar", message, parent=self)


class ActualizarVacanteWindow(FormularioBase):
    def __init__(self, parent, controller, datos_vacante, **kwargs):
        super().__init__(parent, controller, "Editar Vacante")
        self.on_success_callback = kwargs.get("on_success_callback")
        self.id_vacante = datos_vacante["ID_Vacante"]
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.crear_campo(frame, "Cargo Vacante")
        self.crear_campo(frame, "Descripción del Perfil", "textbox")
        self.crear_campo(frame, "Salario Ofrecido")
        self.crear_campo(
            frame, "Estatus", tipo="combobox", values=["Activa", "Inactiva", "Cerrada"]
        )
        frame.pack(pady=10, fill="x")
        self.entries["Cargo Vacante"].insert(0, datos_vacante["Cargo_Vacante"])
        self.entries["Descripción del Perfil"].insert(
            "1.0", datos_vacante["Descripcion_Perfil"]
        )
        self.entries["Salario Ofrecido"].insert(
            0, f"{float(datos_vacante['Salario_Ofrecido']):.2f}"
        )
        self.entries["Estatus"].set(datos_vacante["Estatus"])
        ctk.CTkButton(
            self.main_frame,
            text="Guardar Cambios",
            command=self.guardar,
            height=40,
            corner_radius=10,
            fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_PINK,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=15)

    def guardar(self):
        datos = {
            k: v.get("1.0", "end-1c").strip()
            if isinstance(v, ctk.CTkTextbox)
            else v.get()
            for k, v in self.entries.items()
        }
        try:
            salario = float(datos.get("Salario Ofrecido", 0))
            if salario <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror(
                "Entrada no válida",
                "El salario debe ser un número positivo.",
                parent=self,
            )
            return
        if not all(datos.values()):
            messagebox.showerror(
                "Error", "Todos los campos son obligatorios.", parent=self
            )
            return
        success, message = db_manager.actualizar_vacante_db(
            self.id_vacante,
            datos["Cargo Vacante"],
            datos["Descripción del Perfil"],
            salario,
            datos["Estatus"],
        )
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            if self.on_success_callback:
                self.on_success_callback()
            self.destroy()
        else:
            messagebox.showerror("Error al Guardar", message, parent=self)


class App(ctk.CTk):
    def __init__(self, is_first_run=False):
        super().__init__(fg_color=APP_BG_COLOR)
        self.title("Sistema de Gestión Hiring Group")
        self.geometry("1100x700")
        self.minsize(800, 600)
        self.is_first_run = is_first_run
        self.usuario_actual = None
        self.rol_actual = None
        self.setup_styles()
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.show_frame(LoginFrame)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background=ENTRY_BG_COLOR,
            foreground=TEXT_COLOR,
            fieldbackground=ENTRY_BG_COLOR,
            rowheight=25,
            font=FONT_NORMAL,
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", ACCENT_PURPLE)])
        style.configure(
            "Treeview.Heading",
            background=FRAME_BG_COLOR,
            foreground=TEXT_COLOR,
            font=FONT_BOLD,
            relief="flat",
            padding=5,
        )
        style.map("Treeview.Heading", background=[("active", BUTTON_SECONDARY_HOVER)])

    def show_frame(self, FrameClass):
        for widget in self.container.winfo_children():
            widget.destroy()
        frame = FrameClass(parent=self.container, controller=self)
        frame.grid(row=0, column=0, sticky="nsew")


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        login_container = ctk.CTkFrame(self, fg_color="transparent")
        login_container.grid(row=0, column=0)
        ctk.CTkLabel(
            login_container,
            text="Login del Sistema",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,
        ).pack(pady=20)
        ctk.CTkLabel(
            login_container, text="Email", font=FONT_NORMAL, text_color=TEXT_COLOR
        ).pack(anchor="w", padx=40)
        self.email_entry = ctk.CTkEntry(
            login_container,
            width=300,
            height=35,
            placeholder_text="correo@ejemplo.com",
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text_color=TEXT_COLOR,
        )
        self.email_entry.pack(pady=(0, 10))
        self.email_entry.focus()
        ctk.CTkLabel(
            login_container, text="Contraseña", font=FONT_NORMAL, text_color=TEXT_COLOR
        ).pack(anchor="w", padx=40)
        self.pass_entry = ctk.CTkEntry(
            login_container,
            width=300,
            height=35,
            show="*",
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
            text_color=TEXT_COLOR,
        )
        self.pass_entry.pack()
        self.pass_entry.bind("<Return>", self.attempt_login)
        ctk.CTkButton(
            login_container,
            text="Ingresar",
            command=self.attempt_login,
            height=40,
            corner_radius=10,
            fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_PINK,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=20, ipady=5)
        if self.controller.is_first_run:
            ctk.CTkButton(
                login_container,
                text="Crear Primer Usuario (Admin)",
                command=self.crear_primer_usuario,
                height=35,
                corner_radius=10,
                fg_color=BUTTON_SECONDARY_COLOR,
                hover_color=BUTTON_SECONDARY_HOVER,
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack(pady=10)

    def crear_primer_usuario(self):
        CrearUsuarioWindow(
            self.controller,
            self.controller,
            is_first_user=True,
            on_success_callback=self.refresh_login,
        )

    def refresh_login(self):
        self.controller.is_first_run = False
        self.controller.show_frame(LoginFrame)

    def attempt_login(self, event=None):
        email, password = self.email_entry.get(), self.pass_entry.get()
        if not email or not password:
            messagebox.showwarning(
                "Campos Vacíos", "Por favor, ingrese email y contraseña."
            )
            return
        self.controller.config(cursor="watch")
        self.controller.update_idletasks()
        usuario, rol = db_manager.login_usuario(email, password)
        self.controller.config(cursor="")
        if usuario:
            self.controller.usuario_actual, self.controller.rol_actual = usuario, rol
            self.controller.show_frame(MainFrame)
        else:
            messagebox.showerror(
                "Login Fallido", "Email, contraseña incorrectos o usuario inactivo."
            )


class MainFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        menu_frame = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color=FRAME_BG_COLOR
        )
        menu_frame.grid(row=0, column=0, sticky="nsw")
        self.content_frame = ctk.CTkScrollableFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        rol = self.controller.rol_actual
        ctk.CTkLabel(
            menu_frame,
            text=f"Menú - {rol}",
            font=FONT_MENU_TITLE,
            text_color=TEXT_COLOR,
        ).pack(pady=20)
        botones = {
            "HiringGroup": [
                ("Crear Usuario", lambda: self.open_form_window(CrearUsuarioWindow)),
                ("Gestionar Empresas", self.show_gestionar_empresas),
                ("Gestionar Catálogos", self.show_menu_catalogos),
                ("Contratar Postulante", self.show_contratar_form),
                ("Ejecutar Nómina", self.show_nomina_form),
                ("Reportes de Nómina", self.show_reportes_nomina),
            ],
            "Empresa": [
                (
                    "Crear Vacante",
                    lambda: self.open_form_window(
                        CrearVacanteWindow, on_success_callback=self.show_mis_vacantes
                    ),
                ),
                ("Ver Mis Vacantes", self.show_mis_vacantes),
                (
                    "Editar Mi Perfil",
                    lambda: self.open_form_window(ActualizarUsuarioWindow),
                ),
            ],
            "Postulante": [
                ("Buscar Vacantes", self.show_buscar_vacantes),
                ("Mis Postulaciones", self.show_mis_postulaciones),
                (
                    "Editar Mi Perfil",
                    lambda: self.open_form_window(ActualizarUsuarioWindow),
                ),
                (
                    "Gestionar Experiencia",
                    lambda: self.open_form_window(GestionarExperienciaWindow),
                ),
            ],
            "Contratado": [
                ("Ver Vacantes", lambda: self.show_buscar_vacantes(read_only=True)),
                ("Mis Recibos de Pago", self.show_recibos_pago),
                ("Generar Constancia", self.show_constancia),
                (
                    "Editar Mi Perfil",
                    lambda: self.open_form_window(ActualizarUsuarioWindow),
                ),
            ],
        }
        for texto, comando in botones.get(rol, []):
            ctk.CTkButton(
                menu_frame,
                text=texto,
                command=comando,
                height=35,
                corner_radius=8,
                fg_color=BUTTON_SECONDARY_COLOR,
                hover_color=BUTTON_SECONDARY_HOVER,
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack(pady=4, padx=20, fill="x")
        ctk.CTkButton(
            menu_frame,
            text="Salir (Logout)",
            command=self.logout,
            height=35,
            corner_radius=8,
            fg_color=ACCENT_PINK,
            hover_color=ACCENT_PURPLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side="bottom", pady=20, padx=20, fill="x")
        self.show_welcome_message()

    def open_form_window(self, WindowClass, *args, **kwargs):
        WindowClass(self.controller, self.controller, *args, **kwargs)

    def show_welcome_message(self):
        self.clear_content_frame()
        ctk.CTkLabel(
            self.content_frame,
            text=f"Bienvenido/a, {self.controller.usuario_actual['Email']}",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,
        ).pack(anchor="w", pady=(0, 10))

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def logout(self):
        self.controller.usuario_actual, self.controller.rol_actual = None, None
        self.controller.show_frame(LoginFrame)

    def show_gestionar_empresas(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Gestionar Empresas",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        empresas = db_manager.get_catalogo(
            "Empresas",
            "ID_Empresa",
            [
                "Nombre_Empresa",
                "RIF",
                "Sector_Industrial",
                "Persona_Contacto",
                "Telefono_Contacto",
                "Email_Contacto",
            ],
        )
        if not empresas:
            ctk.CTkLabel(
                self.content_frame,
                text="No hay empresas registradas.",
                text_color=TEXT_COLOR,
            ).pack()  # CORREGIDO
            return
        tree_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=5)
        tree = crear_tabla(
            tree_frame,
            ("ID", "Nombre", "RIF", "Sector", "Contacto", "Teléfono", "Email"),
            widths={"ID": 40, "Nombre": 150, "RIF": 80},
        )
        for e in empresas:
            tree.insert(
                "",
                "end",
                values=(
                    e["ID_Empresa"],
                    e["Nombre_Empresa"],
                    e["RIF"],
                    e["Sector_Industrial"],
                    e["Persona_Contacto"],
                    e["Telefono_Contacto"],
                    e["Email_Contacto"],
                ),
            )
        tree.pack(fill="both", expand=True)

    def show_menu_catalogos(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Gestionar Catálogos",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        catalogos = {
            "Áreas de Conocimiento": (
                "Areas_Conocimiento",
                "ID_Area_Conocimiento",
                "Nombre_Area",
            ),
            "Profesiones": ("Profesiones", "ID_Profesion", "Nombre_Profesion"),
            "Universidades": ("Universidades", "ID_Universidad", "Nombre_Universidad"),
            "Bancos": ("Bancos", "ID_Banco", "Nombre_Banco"),
        }
        for title, args in catalogos.items():
            ctk.CTkButton(
                self.content_frame,
                text=f"Gestionar {title}",
                command=lambda t=title, a=args: self.open_form_window(
                    GestionCatalogoWindow,
                    title=f"Gestionar {t}",
                    tabla=a[0],
                    id_col=a[1],
                    nombre_col=a[2],
                ),
                fg_color=BUTTON_SECONDARY_COLOR,
                hover_color=BUTTON_SECONDARY_HOVER,
                corner_radius=8,
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack(fill="x", padx=20, pady=5)

    def show_contratar_form(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Contratar Postulante",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        postulaciones = db_manager.get_postulaciones_para_contratar()
        bancos = db_manager.get_catalogo("Bancos", "ID_Banco", "Nombre_Banco")
        if not postulaciones:
            ctk.CTkLabel(
                self.content_frame,
                text="No hay postulaciones recibidas.",
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack()
            return
        tree_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tree_frame.pack(fill="x", expand=True, pady=5)
        tree = crear_tabla(tree_frame, ("ID", "Nombre", "Cargo"))
        for p in postulaciones:
            tree.insert(
                "",
                "end",
                values=(
                    p["ID_Postulacion"],
                    f"{p['Nombres']} {p['Apellidos']}",
                    p["Cargo_Vacante"],
                ),
            )
        tree.pack(fill="x")
        form_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        form_frame.pack(anchor="w", fill="x", pady=(10, 0))
        entries = {}
        bancos_map = {b["Nombre_Banco"]: b["ID_Banco"] for b in bancos or []}
        fields = [
            ("Salario", "entry"),
            ("Tipo Contrato", "combo_contrato"),
            ("Tipo de Sangre", "entry"),
            ("Nombre Contacto Emergencia", "entry"),
            ("Teléfono Contacto Emergencia", "entry"),
            ("Número de Cuenta", "entry"),
            ("Banco", "combo_banco"),
        ]
        for i, (label_text, widget_type) in enumerate(fields):
            label = ctk.CTkLabel(
                form_frame,
                text=f"{label_text}:",
                font=FONT_NORMAL,
                text_color=TEXT_COLOR,
            )  # CORREGIDO
            label.grid(row=i, column=0, padx=5, pady=8, sticky="w")
            widget = None
            if widget_type == "entry":
                widget = ctk.CTkEntry(
                    form_frame,
                    width=250,
                    text_color=TEXT_COLOR,
                    fg_color=ENTRY_BG_COLOR,
                    border_color=BUTTON_SECONDARY_COLOR,
                )
            elif (
                widget_type == "combo_contrato" or widget_type == "combo_banco"
            ):  # CORREGIDO (Agrupado)
                widget = ctk.CTkComboBox(
                    form_frame,
                    width=250,
                    values=(
                        ["Un mes", "Seis meses", "Un año", "Indefinido"]
                        if widget_type == "combo_contrato"
                        else list(bancos_map.keys())
                    ),
                    state="readonly",
                    text_color=TEXT_COLOR,
                    fg_color=ENTRY_BG_COLOR,
                    border_color=BUTTON_SECONDARY_COLOR,
                    button_color=BUTTON_SECONDARY_COLOR,
                    button_hover_color=BUTTON_SECONDARY_HOVER,
                )
            if widget:
                widget.grid(row=i, column=1, padx=5, pady=8, sticky="ew")
                entries[label_text] = widget

        def contratar():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Selección Requerida", "Por favor, selecciona una postulación."
                )
                return
            try:
                salario_val = float(entries["Salario"].get())
                if salario_val <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror(
                    "Entrada no válida", "El salario debe ser un número positivo."
                )
                return
            id_postulacion = tree.item(selected[0])["values"][0]
            datos_contrato = {
                "Salario_Acordado": salario_val,
                "Tipo_Contrato": entries["Tipo Contrato"].get(),
                "Tipo_Sangre": entries["Tipo de Sangre"].get(),
                "Contacto_Emergencia_Nombre": entries[
                    "Nombre Contacto Emergencia"
                ].get(),
                "Contacto_Emergencia_Telefono": entries[
                    "Teléfono Contacto Emergencia"
                ].get(),
                "Numero_Cuenta": entries["Número de Cuenta"].get(),
                "ID_Banco": bancos_map.get(entries["Banco"].get()),
            }
            if not all(
                v is not None if k == "ID_Banco" else v
                for k, v in datos_contrato.items()
            ):
                messagebox.showerror("Error", "Todos los campos son obligatorios.")
                return
            success, msg = db_manager.contratar_postulante_db(
                id_postulacion, datos_contrato
            )
            if success:
                messagebox.showinfo("Resultado", msg)
                self.show_contratar_form()
            else:
                messagebox.showerror("Error", msg)

        ctk.CTkButton(
            self.content_frame,
            text="Contratar y Aceptar",
            command=contratar,
            height=40,
            corner_radius=10,
            fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_PINK,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=20, anchor="w")

    def show_buscar_vacantes(self, read_only=False):
        self.show_welcome_message()
        title = "Vacantes Disponibles" if not read_only else "Visualizar Vacantes"
        ctk.CTkLabel(
            self.content_frame, text=title, font=FONT_TITLE, text_color=TEXT_COLOR
        ).pack(  # CORREGIDO
            pady=10, anchor="w"
        )
        filter_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=5)
        areas = db_manager.get_catalogo(
            "Areas_Conocimiento", "ID_Area_Conocimiento", "Nombre_Area"
        )
        area_map = {"Todas": None}
        area_map.update(
            {a["Nombre_Area"]: a["ID_Area_Conocimiento"] for a in areas or []}
        )
        ctk.CTkLabel(
            filter_frame, text="Área:", font=FONT_NORMAL, text_color=TEXT_COLOR
        ).pack(  # CORREGIDO
            side=tk.LEFT, padx=(0, 5)
        )
        area_combo = ctk.CTkComboBox(
            filter_frame,
            values=list(area_map.keys()),
            state="readonly",
            width=180,
            text_color=TEXT_COLOR,  # CORREGIDO
            fg_color=ENTRY_BG_COLOR,  # CORREGIDO
            border_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_hover_color=BUTTON_SECONDARY_HOVER,  # CORREGIDO
        )
        area_combo.pack(side=tk.LEFT, padx=5)
        area_combo.set("Todas")
        ctk.CTkLabel(
            filter_frame, text="Salario:", font=FONT_NORMAL, text_color=TEXT_COLOR
        ).pack(  # CORREGIDO
            side=tk.LEFT, padx=(10, 5)
        )
        salary_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Sin Orden", "Mayor a Menor", "Menor a Mayor"],
            state="readonly",
            width=150,
            text_color=TEXT_COLOR,  # CORREGIDO
            fg_color=ENTRY_BG_COLOR,  # CORREGIDO
            border_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_hover_color=BUTTON_SECONDARY_HOVER,  # CORREGIDO
        )
        salary_combo.pack(side=tk.LEFT, padx=5)
        salary_combo.set("Sin Orden")
        tree_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=10)
        tree = crear_tabla(
            tree_frame,
            ("ID", "Cargo", "Empresa", "Área", "Profesión", "Salario"),
            widths={"ID": 40, "Salario": 80},
        )
        tree.pack(fill="both", expand=True)

        def populate_tree():
            for i in tree.get_children():
                tree.delete(i)
            filtro_area = area_map[area_combo.get()]
            sort_map = {"Mayor a Menor": "DESC", "Menor a Mayor": "ASC"}
            sort_salary = sort_map.get(salary_combo.get())
            vacantes = db_manager.get_active_vacantes(
                filtro_area=filtro_area, sort_salary=sort_salary
            )
            for v in vacantes or []:
                tree.insert(
                    "",
                    "end",
                    values=(
                        v["ID_Vacante"],
                        v["Cargo_Vacante"],
                        v["Nombre_Empresa"],
                        v["Nombre_Area"] or "No Asignada",
                        v["Nombre_Profesion"],
                        f"{float(v['Salario_Ofrecido']):.2f}",
                    ),
                )

        ctk.CTkButton(
            filter_frame,
            text="Filtrar",
            command=populate_tree,
            width=80,
            corner_radius=8,
            fg_color=BUTTON_SECONDARY_COLOR,
            hover_color=BUTTON_SECONDARY_HOVER,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side=tk.LEFT, padx=10)
        if not read_only:
            ctk.CTkButton(
                self.content_frame,
                text="Aplicar a Vacante",
                command=lambda: self.aplicar(tree),
                height=40,
                corner_radius=10,
                fg_color=ACCENT_PURPLE,
                hover_color=ACCENT_PINK,
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack(pady=10, anchor="e")
        populate_tree()

    def aplicar(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                "Selección Requerida", "Selecciona una vacante para aplicar."
            )
            return
        id_vacante = tree.item(selected[0])["values"][0]
        success, msg = db_manager.aplicar_a_vacante_db(
            self.controller.usuario_actual["ID_Usuario"], id_vacante
        )
        messagebox.showinfo("Resultado", msg)

    def show_recibos_pago(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Mis Recibos de Pago",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        filter_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(filter_frame, text="Mes (opc):", text_color=TEXT_COLOR).pack(
            side=tk.LEFT, padx=5
        )  # CORREGIDO
        mes_entry = ctk.CTkEntry(
            filter_frame,
            width=50,
            text_color=TEXT_COLOR,
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
        )
        mes_entry.pack(side=tk.LEFT, padx=5)
        ctk.CTkLabel(filter_frame, text="Año (opc):", text_color=TEXT_COLOR).pack(
            side=tk.LEFT, padx=5
        )  # CORREGIDO
        anio_entry = ctk.CTkEntry(
            filter_frame,
            width=70,
            text_color=TEXT_COLOR,
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
        )
        anio_entry.pack(side=tk.LEFT, padx=5)
        tree_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=10)
        tree = crear_tabla(
            tree_frame, ("Periodo", "Fecha Pago", "Salario Base", "Salario Neto")
        )
        tree.pack(fill="both", expand=True)

        def populate_recibos():
            for i in tree.get_children():
                tree.delete(i)
            recibos = db_manager.get_recibos_por_contratado(
                self.controller.usuario_actual["ID_Usuario"],
                mes_entry.get() or None,
                anio_entry.get() or None,
            )
            for r in recibos or []:
                tree.insert(
                    "",
                    "end",
                    values=(
                        f"{r['Mes']}/{r['Anio']}",
                        r["Fecha_Pago"],
                        f"{r['Salario_Base']:.2f}",
                        f"{r['Salario_Neto_Pagado']:.2f}",
                    ),
                )

        ctk.CTkButton(
            filter_frame,
            text="Filtrar",
            command=populate_recibos,
            width=80,
            corner_radius=8,
            fg_color=BUTTON_SECONDARY_COLOR,
            hover_color=BUTTON_SECONDARY_HOVER,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side=tk.LEFT, padx=10)
        populate_recibos()

    def show_mis_vacantes(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Mis Vacantes Publicadas",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        vacantes = db_manager.get_vacantes_por_empresa(
            self.controller.usuario_actual["ID_Usuario"]
        )
        if not vacantes:
            ctk.CTkLabel(
                self.content_frame,
                text="No tienes vacantes publicadas.",
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack()
            return
        tree_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=10)
        tree = crear_tabla(
            tree_frame,
            ("ID", "Cargo", "Salario", "Estatus"),
            widths={"ID": 50, "Estatus": 80},
        )
        for v in vacantes:
            salario = (
                f"{float(v['Salario_Ofrecido']):.2f}"
                if v["Salario_Ofrecido"]
                else "N/A"
            )
            tree.insert(
                "",
                "end",
                values=(v["ID_Vacante"], v["Cargo_Vacante"], salario, v["Estatus"]),
            )
        tree.pack(fill="both", expand=True)
        buttons_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=5, anchor="e")

        def editar_vacante():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Selección Requerida",
                    "Selecciona una vacante para editar.",
                    parent=self.controller,
                )
                return
            id_vacante = tree.item(selected[0])["values"][0]
            datos_vacante = next(
                (v for v in vacantes if v["ID_Vacante"] == id_vacante), None
            )
            if datos_vacante:
                self.open_form_window(
                    ActualizarVacanteWindow,
                    datos_vacante=datos_vacante,
                    on_success_callback=self.show_mis_vacantes,
                )

        def eliminar_vacante():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning(
                    "Selección Requerida",
                    "Selecciona una vacante para eliminar.",
                    parent=self.controller,
                )
                return
            id_vacante, cargo = tree.item(selected[0])["values"][:2]
            if messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Estás seguro de que quieres eliminar la vacante '{cargo}'?",
                parent=self.controller,
            ):
                success, msg = db_manager.eliminar_vacante_db(id_vacante)
                if success:
                    messagebox.showinfo("Resultado", msg, parent=self.controller)
                    self.show_mis_vacantes()
                else:
                    messagebox.showerror("Error", msg, parent=self.controller)

        ctk.CTkButton(
            buttons_frame,
            text="Editar Vacante",
            command=editar_vacante,
            fg_color=BUTTON_SECONDARY_COLOR,
            hover_color=BUTTON_SECONDARY_HOVER,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side="right", padx=10)
        ctk.CTkButton(
            buttons_frame,
            text="Eliminar Vacante",
            command=eliminar_vacante,
            fg_color=ACCENT_PINK,
            hover_color=ACCENT_PURPLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side="right")

    def show_reportes_nomina(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Reportes de Nómina",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        rep1_frame = ctk.CTkFrame(self.content_frame, fg_color=FRAME_BG_COLOR)
        rep1_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(
            rep1_frame, text="Nómina por Empresa", font=FONT_BOLD, text_color=TEXT_COLOR
        ).pack(  # CORREGIDO
            pady=10
        )
        empresas = db_manager.get_catalogo("Empresas", "ID_Empresa", "Nombre_Empresa")
        empresa_map = {e["Nombre_Empresa"]: e["ID_Empresa"] for e in empresas or []}
        filter_controls = ctk.CTkFrame(rep1_frame, fg_color="transparent")
        filter_controls.pack(fill="x", padx=10)
        ctk.CTkLabel(filter_controls, text="Empresa:", text_color=TEXT_COLOR).pack(
            side=tk.LEFT
        )  # CORREGIDO
        empresa_combo = ctk.CTkComboBox(
            filter_controls,
            values=list(empresa_map.keys()),
            state="readonly",
            width=200,
            text_color=TEXT_COLOR,  # CORREGIDO
            fg_color=ENTRY_BG_COLOR,  # CORREGIDO
            border_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_hover_color=BUTTON_SECONDARY_HOVER,  # CORREGIDO
        )
        empresa_combo.pack(side=tk.LEFT, padx=5)
        ctk.CTkLabel(filter_controls, text="Mes:", text_color=TEXT_COLOR).pack(
            side=tk.LEFT
        )  # CORREGIDO
        mes_entry = ctk.CTkEntry(
            filter_controls,
            width=50,
            text_color=TEXT_COLOR,
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
        )
        mes_entry.pack(side=tk.LEFT, padx=5)
        ctk.CTkLabel(filter_controls, text="Año:", text_color=TEXT_COLOR).pack(
            side=tk.LEFT
        )  # CORREGIDO
        anio_entry = ctk.CTkEntry(
            filter_controls,
            width=70,
            text_color=TEXT_COLOR,
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
        )
        anio_entry.pack(side=tk.LEFT, padx=5)
        tree1_frame = ctk.CTkFrame(rep1_frame, fg_color="transparent")
        tree1_frame.pack(fill="both", expand=True, pady=10, padx=10)
        tree1 = crear_tabla(tree1_frame, ("Empleado", "Cédula", "Salario Base"))
        tree1.pack(fill="both", expand=True)

        def buscar_nomina():
            id_empresa = empresa_map.get(empresa_combo.get())
            try:
                mes, anio = int(mes_entry.get()), int(anio_entry.get())
            except (ValueError, TypeError):
                messagebox.showerror(
                    "Entrada no válida",
                    "Por favor, introduce un mes (1-12) y año válidos.",
                )
                return
            if not id_empresa:
                messagebox.showerror("Error", "Debes seleccionar una empresa")
                return
            for i in tree1.get_children():
                tree1.delete(i)
            reporte = db_manager.get_nomina_reporte_db(id_empresa, mes, anio)
            for row in reporte or []:
                tree1.insert(
                    "",
                    "end",
                    values=(
                        row["Empleado"],
                        row["Cedula_Identidad"],
                        f"{row['Salario_Base']:.2f}",
                    ),
                )

        ctk.CTkButton(
            filter_controls,
            text="Buscar",
            command=buscar_nomina,
            width=80,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(side=tk.LEFT, padx=10)
        rep2_frame = ctk.CTkFrame(self.content_frame, fg_color=FRAME_BG_COLOR)
        rep2_frame.pack(fill="both", pady=10, expand=True)
        ctk.CTkLabel(
            rep2_frame,
            text="Nómina General por Empresa",
            font=FONT_BOLD,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10)
        tree2_frame = ctk.CTkFrame(rep2_frame, fg_color="transparent")
        tree2_frame.pack(fill="both", expand=True, padx=10, pady=10)
        tree2 = crear_tabla(tree2_frame, ("Empresa", "Periodo", "Total Nómina"))
        tree2.pack(fill="both", expand=True)
        reporte_total = db_manager.get_toda_nomina_reporte_db()
        for row in reporte_total or []:
            tree2.insert(
                "",
                "end",
                values=(
                    row["Nombre_Empresa"],
                    f"{row['Mes']}/{row['Anio']}",
                    f"{row['Total_Nomina']:.2f}",
                ),
            )

    def show_nomina_form(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Ejecutar Nómina Mensual",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        form_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        form_container.pack(fill="x", pady=5, anchor="w")
        empresas = db_manager.get_catalogo("Empresas", "ID_Empresa", "Nombre_Empresa")
        if not empresas:
            ctk.CTkLabel(
                self.content_frame,
                text="No hay empresas registradas.",
                text_color=TEXT_COLOR,
            ).pack()  # CORREGIDO
            return
        empresa_map = {e["Nombre_Empresa"]: e["ID_Empresa"] for e in empresas or []}
        ctk.CTkLabel(form_container, text="Empresa:", text_color=TEXT_COLOR).pack(
            anchor="w"
        )  # CORREGIDO
        empresa_combo = ctk.CTkComboBox(
            form_container,
            values=list(empresa_map.keys()),
            state="readonly",
            width=300,
            text_color=TEXT_COLOR,  # CORREGIDO
            fg_color=ENTRY_BG_COLOR,  # CORREGIDO
            border_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_color=BUTTON_SECONDARY_COLOR,  # CORREGIDO
            button_hover_color=BUTTON_SECONDARY_HOVER,  # CORREGIDO
        )
        empresa_combo.pack(fill="x")
        ctk.CTkLabel(form_container, text="Mes (1-12):", text_color=TEXT_COLOR).pack(
            anchor="w", pady=(10, 0)
        )  # CORREGIDO
        mes_entry = ctk.CTkEntry(
            form_container,
            width=300,
            text_color=TEXT_COLOR,
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
        )
        mes_entry.pack(fill="x")
        ctk.CTkLabel(form_container, text="Año (YYYY):", text_color=TEXT_COLOR).pack(
            anchor="w", pady=(10, 0)
        )  # CORREGIDO
        anio_entry = ctk.CTkEntry(
            form_container,
            width=300,
            text_color=TEXT_COLOR,
            fg_color=ENTRY_BG_COLOR,
            border_color=BUTTON_SECONDARY_COLOR,
        )
        anio_entry.pack(fill="x")
        resultado_frame = ctk.CTkFrame(self.content_frame, fg_color=FRAME_BG_COLOR)
        resultado_frame.pack(fill="both", pady=20, expand=True)
        ctk.CTkLabel(
            resultado_frame,
            text="Resultado de la Nómina Generada",
            font=FONT_BOLD,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10)
        tree_resultado = crear_tabla(
            resultado_frame,
            ("Empleado", "Cédula", "Salario Base", "Deducciones", "Salario Neto"),
            widths={
                "Empleado": 200,
                "Cédula": 100,
                "Salario Base": 100,
                "Deducciones": 100,
                "Salario Neto": 100,
            },
        )
        tree_resultado.pack(fill="both", expand=True, padx=10, pady=10)

        def generar():
            for i in tree_resultado.get_children():
                tree_resultado.delete(i)
            nombre_empresa = empresa_combo.get()
            try:
                mes, anio = int(mes_entry.get()), int(anio_entry.get())
            except (ValueError, TypeError):
                messagebox.showerror(
                    "Entrada no válida", "Mes y año deben ser números."
                )
                return
            if not (1 <= mes <= 12 and 2000 <= anio <= 2100):
                messagebox.showerror(
                    "Entrada no válida",
                    "Por favor, introduce un mes (1-12) y año válidos.",
                )
                return
            if not nombre_empresa:
                messagebox.showerror("Error", "Debes seleccionar una empresa")
                return
            id_empresa = empresa_map.get(nombre_empresa)
            success, msg, id_nomina = db_manager.ejecutar_nomina_db(
                id_empresa, mes, anio
            )
            messagebox.showinfo("Resultado", msg)
            if success and id_nomina:
                detalles_nomina = db_manager.get_nomina_generada_detalle_db(id_nomina)
                for detalle in detalles_nomina or []:
                    tree_resultado.insert(
                        "",
                        "end",
                        values=(
                            detalle["Empleado"],
                            detalle["Cedula_Identidad"],
                            f"{detalle['Salario_Base']:.2f}",
                            f"{detalle['Total_Deducciones']:.2f}",
                            f"{detalle['Salario_Neto_Pagado']:.2f}",
                        ),
                    )

        ctk.CTkButton(
            form_container,
            text="Generar Nómina",
            command=generar,
            height=40,
            corner_radius=10,
            fg_color=ACCENT_PURPLE,
            hover_color=ACCENT_PINK,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=20, anchor="w")

    def show_mis_postulaciones(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Mis Postulaciones Realizadas",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        postulaciones = db_manager.get_postulaciones_por_postulante(
            self.controller.usuario_actual["ID_Usuario"]
        )
        if not postulaciones:
            ctk.CTkLabel(
                self.content_frame,
                text="No has realizado ninguna postulación.",
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack()
            return
        tree_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, pady=10)
        tree = crear_tabla(
            tree_frame, ("Cargo", "Empresa", "Salario", "Fecha", "Estatus")
        )
        for p in postulaciones:
            salario = (
                f"{float(p['Salario_Ofrecido']):.2f}"
                if p["Salario_Ofrecido"]
                else "N/A"
            )
            fecha = p["Fecha_Postulacion"] if p["Fecha_Postulacion"] else "N/A"
            tree.insert(
                "",
                "end",
                values=(
                    p["Cargo_Vacante"],
                    p["Nombre_Empresa"],
                    salario,
                    fecha,
                    p["Estatus"],
                ),
            )
        tree.pack(fill="both", expand=True)

    def show_constancia(self):
        self.show_welcome_message()
        ctk.CTkLabel(
            self.content_frame,
            text="Constancia de Trabajo",
            font=FONT_TITLE,
            text_color=TEXT_COLOR,  # CORREGIDO
        ).pack(pady=10, anchor="w")
        texto_constancia = db_manager.get_datos_constancia(
            self.controller.usuario_actual["ID_Usuario"]
        )
        if texto_constancia:
            textbox = ctk.CTkTextbox(
                self.content_frame,
                height=250,
                font=("Courier", 12),
                wrap="word",
                fg_color=ENTRY_BG_COLOR,
                border_color=BUTTON_SECONDARY_COLOR,
                text_color=TEXT_COLOR,
            )
            textbox.pack(pady=10, fill="x", expand=True)
            textbox.insert(tk.END, texto_constancia)
            textbox.configure(state="disabled")
        else:
            ctk.CTkLabel(
                self.content_frame,
                text="No se pudo generar la constancia. No se encontró un contrato activo.",
                text_color=TEXT_COLOR,  # CORREGIDO
            ).pack()


if __name__ == "__main__":
    first_run = not db_manager.hay_usuarios_registrados()
    app = App(is_first_run=first_run)
    app.mainloop()
