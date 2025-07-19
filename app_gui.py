# ==============================================================================
#  app_gui.py - VERSIÓN FINAL COMPLETA Y CORREGIDA
# ==============================================================================
#  - Corrige todos los errores de `KeyError` y `AttributeError`.
#  - Valida entradas numéricas (salario, mes, año).
#  - Muestra un cursor de espera durante operaciones de BD.
#  - Maneja correctamente los valores NULL de la BD al editar perfiles.
#  - Utiliza callbacks para refrescar vistas de forma segura.
#  - Mantiene la lógica de conexión automática para XAMPP.
# ==============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import db_manager
from datetime import datetime

# --- CONSTANTES DE ESTILO ---
BG_COLOR = "#0F172A"; FG_COLOR = "#E2E8F0"; ENTRY_BG = "#1E293B"
BUTTON_BG = "#334155"; ACCENT_COLOR = "#9333EA"; ACCENT_ACTIVE = "#A855F7"
FONT_NORMAL = ("Segoe UI", 10); FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold"); FONT_MENU_TITLE = ("Segoe UI", 12, "bold")

# --- FUNCIÓN DE UTILIDAD ---
def crear_tabla(parent, cols, widths={}):
    tree = ttk.Treeview(parent, columns=cols, show='headings', style="Treeview")
    for col in cols:
        tree.heading(col, text=col); tree.column(col, width=widths.get(col, 120), anchor="w")
    return tree

# --- CLASES DE VENTANAS DE FORMULARIO (TOPLEVEL) ---
class FormularioBase(tk.Toplevel):
    def __init__(self, parent, controller, title):
        super().__init__(parent)
        self.title(title); self.config(bg=BG_COLOR, padx=20, pady=20)
        self.transient(parent); self.grab_set(); self.controller = controller
        self.entries = {}; self.resizable(False, False)

    def crear_campo(self, frame, texto_label, tipo="entry", **kwargs):
        row = tk.Frame(frame, bg=BG_COLOR)
        label = tk.Label(row, width=20, text=f"{texto_label}:", anchor='w', bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL)
        widget = None
        if tipo == "entry":
            widget = tk.Entry(row, width=40, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL)
            if "Contraseña" in texto_label: widget.config(show="*")
        elif tipo == "combobox":
            widget = ttk.Combobox(row, width=37, state="readonly", font=FONT_NORMAL, values=kwargs.get('values', []))
        elif tipo == "scrolledtext":
            widget = scrolledtext.ScrolledText(row, width=40, height=4, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL)
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5); label.pack(side=tk.LEFT)
        if widget: widget.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X, ipady=4)
        self.entries[texto_label.replace(":", "")] = widget
        return widget

class CrearUsuarioWindow(FormularioBase):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, controller, "Crear Nuevo Usuario")
        self.campos_especificos = {"Postulante": ["Nombres", "Apellidos", "Cédula", "Teléfono", "Universidad"], "Empresa": ["Nombre Empresa", "RIF", "Sector", "Persona de Contacto", "Teléfono de Contacto", "Email de Contacto"], "HiringGroup": []}
        self.universidades = db_manager.get_catalogo(self.controller.conexion, 'Universidades', 'ID_Universidad', 'Nombre_Universidad')
        self.uni_map = {u['Nombre_Universidad']: u['ID_Universidad'] for u in self.universidades}
        top_frame = tk.Frame(self, bg=BG_COLOR)
        self.crear_campo(top_frame, "Tipo de Usuario", "combobox", values=list(self.campos_especificos.keys()))
        self.entries["Tipo de Usuario"].bind("<<ComboboxSelected>>", self.actualizar_campos)
        top_frame.pack(); self.form_frame = tk.Frame(self, bg=BG_COLOR); self.form_frame.pack(pady=10)
        ttk.Button(self, text="Crear Usuario", command=self.crear, style="Accent.TButton").pack(pady=15); self.actualizar_campos(None)

    def actualizar_campos(self, event):
        for widget in self.form_frame.winfo_children(): widget.destroy()
        keys_to_remove = [k for k in self.entries.keys() if k not in ["Tipo de Usuario"]]; [self.entries.pop(k, None) for k in keys_to_remove]
        self.crear_campo(self.form_frame, "Email"); self.crear_campo(self.form_frame, "Contraseña")
        tipo_usuario = self.entries["Tipo de Usuario"].get()
        for field in self.campos_especificos.get(tipo_usuario, []):
            if field == "Universidad": self.crear_campo(self.form_frame, field, "combobox", values=list(self.uni_map.keys()))
            else: self.crear_campo(self.form_frame, field)

    def crear(self):
        tipo_usuario = self.entries["Tipo de Usuario"].get()
        if not tipo_usuario: messagebox.showerror("Error", "Debes seleccionar un tipo de usuario.", parent=self); return
        datos = {k: v.get() for k, v in self.entries.items()}
        datos_db = {"Email": datos.get("Email"), "Contraseña": datos.get("Contraseña"), "Nombres": datos.get("Nombres"), "Apellidos": datos.get("Apellidos"), "Cédula": datos.get("Cédula"), "Teléfono": datos.get("Teléfono"), "ID_Universidad": self.uni_map.get(datos.get("Universidad")), "Nombre Empresa": datos.get("Nombre Empresa"), "RIF": datos.get("RIF"), "Sector": datos.get("Sector"), "Persona de Contacto": datos.get("Persona de Contacto"), "Teléfono de Contacto": datos.get("Teléfono de Contacto"), "Email de Contacto": datos.get("Email de Contacto")}
        
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        success, message = db_manager.registrar_usuario_db(self.controller.conexion, tipo_usuario, datos_db)
        self.controller.config(cursor="")
        
        if success: messagebox.showinfo("Éxito", message, parent=self); self.destroy()
        else: messagebox.showerror("Error al Crear", message, parent=self)

class ActualizarUsuarioWindow(FormularioBase):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, controller, "Editar Mi Perfil")
        self.tipo_usuario = self.controller.rol_actual; self.id_usuario = self.controller.usuario_actual['ID_Usuario']
        form_frame = tk.Frame(self, bg=BG_COLOR)
        if self.tipo_usuario in ['Postulante', 'Contratado']:
            self.universidades = db_manager.get_catalogo(self.controller.conexion, 'Universidades', 'ID_Universidad', 'Nombre_Universidad')
            self.uni_map = {u['Nombre_Universidad']: u['ID_Universidad'] for u in self.universidades}; self.inv_uni_map = {v: k for k, v in self.uni_map.items()}
            self.crear_campo(form_frame, "Nombres"); self.crear_campo(form_frame, "Apellidos"); self.crear_campo(form_frame, "Teléfono")
            self.crear_campo(form_frame, "Universidad", "combobox", values=list(self.uni_map.keys())); self.populate_postulante()
        elif self.tipo_usuario == 'Empresa':
            self.crear_campo(form_frame, "Nombre Empresa"); self.crear_campo(form_frame, "Sector"); self.crear_campo(form_frame, "Persona de Contacto")
            self.crear_campo(form_frame, "Teléfono de Contacto"); self.crear_campo(form_frame, "Email de Contacto"); self.populate_empresa()
        self.crear_campo(form_frame, "Nueva Contraseña (opcional)"); form_frame.pack(pady=10)
        ttk.Button(self, text="Guardar Cambios", command=self.actualizar, style="Accent.TButton").pack(pady=15)

    def populate_postulante(self):
        datos = db_manager.get_single_postulante(self.controller.conexion, self.id_usuario)
        if not datos: return
        self.entries["Nombres"].insert(0, datos['Nombres'] or ""); self.entries["Apellidos"].insert(0, datos['Apellidos'] or "")
        self.entries["Teléfono"].insert(0, datos['Telefono'] or ""); self.entries["Universidad"].set(self.inv_uni_map.get(datos['ID_Universidad'], ""))

    def populate_empresa(self):
        datos = db_manager.get_single_empresa(self.controller.conexion, self.id_usuario)
        if not datos: return
        self.entries["Nombre Empresa"].insert(0, datos['Nombre_Empresa'] or ""); self.entries["Sector"].insert(0, datos['Sector_Industrial'] or "")
        self.entries["Persona de Contacto"].insert(0, datos['Persona_Contacto'] or ""); self.entries["Teléfono de Contacto"].insert(0, datos['Telefono_Contacto'] or "")
        self.entries["Email de Contacto"].insert(0, datos['Email_Contacto'] or "")

    def actualizar(self):
        datos = {k: (v.get("1.0", "end-1c") if isinstance(v, scrolledtext.ScrolledText) else v.get()) for k, v in self.entries.items()}
        datos_db = {k.strip().replace(" (opcional)", ""): v for k, v in datos.items()}
        if self.tipo_usuario in ['Postulante', 'Contratado']: datos_db["ID_Universidad"] = self.uni_map.get(datos_db.get("Universidad"))
        if "Nueva Contraseña" in datos_db: datos_db["Contraseña"] = datos_db.pop("Nueva Contraseña")
        
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        success, message = db_manager.actualizar_usuario_db(self.controller.conexion, self.id_usuario, self.tipo_usuario, datos_db)
        self.controller.config(cursor="")

        if success: messagebox.showinfo("Éxito", message, parent=self); self.destroy()
        else: messagebox.showerror("Error al Actualizar", message, parent=self)

class GestionarExperienciaWindow(FormularioBase):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, controller, "Gestionar Mi Experiencia Laboral")
        self.id_postulante = self.controller.usuario_actual['ID_Usuario']
        add_frame = tk.LabelFrame(self, text="Añadir/Editar Experiencia", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10, font=FONT_BOLD)
        add_frame.pack(fill="x", pady=10)
        self.crear_campo(add_frame, "Empresa"); self.crear_campo(add_frame, "Cargo"); self.crear_campo(add_frame, "Fecha Inicio (YYYY-MM-DD)"); self.crear_campo(add_frame, "Fecha Fin (YYYY-MM-DD, opcional)")
        self.crear_campo(add_frame, "Descripción", "scrolledtext")
        ttk.Button(add_frame, text="Agregar Experiencia", command=self.agregar, style="Accent.TButton").pack(pady=10)
        tree_frame = tk.LabelFrame(self, text="Mis Experiencias", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10, font=FONT_BOLD)
        tree_frame.pack(fill="both", expand=True, pady=10)
        self.tree = crear_tabla(tree_frame, ('ID', 'Empresa', 'Cargo', 'Inicio', 'Fin'), widths={'ID': 30})
        self.tree.pack(fill="both", expand=True)
        ttk.Button(tree_frame, text="Eliminar Seleccionada", command=self.eliminar).pack(pady=10, anchor='e')
        self.populate_tree()

    def populate_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for exp in db_manager.get_experiencias_db(self.controller.conexion, self.id_postulante):
            self.tree.insert("", "end", values=(exp['ID_Experiencia'], exp['Empresa'], exp['Cargo_Ocupado'], exp['Fecha_Inicio'], exp['Fecha_Fin'] or 'Actual'))

    def agregar(self):
        datos = {k: (v.get("1.0", "end-1c") if isinstance(v, scrolledtext.ScrolledText) else v.get()) for k, v in self.entries.items()}
        if not datos['Empresa'] or not datos['Cargo'] or not datos['Fecha Inicio (YYYY-MM-DD)']:
            messagebox.showerror("Error", "Empresa, Cargo y Fecha de Inicio son obligatorios.", parent=self); return
        datos_db = {'Empresa': datos['Empresa'], 'Cargo': datos['Cargo'], 'Fecha Inicio': datos['Fecha Inicio (YYYY-MM-DD)'], 'Fecha Fin': datos['Fecha Fin (YYYY-MM-DD, opcional)'], 'Descripcion': datos['Descripción']}
        
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        success, msg = db_manager.crear_experiencia_db(self.controller.conexion, self.id_postulante, datos_db)
        self.controller.config(cursor="")

        if success: self.populate_tree()
        else: messagebox.showerror("Error", msg, parent=self)

    def eliminar(self):
        selected = self.tree.selection()
        if not selected: messagebox.showwarning("Selección Requerida", "Selecciona una experiencia para eliminar.", parent=self); return
        id_exp = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta experiencia?", parent=self):
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            success, msg = db_manager.eliminar_experiencia_db(self.controller.conexion, id_exp)
            self.controller.config(cursor="")
            if success: self.populate_tree()
            else: messagebox.showerror("Error", msg, parent=self)

class GestionCatalogoWindow(FormularioBase):
    def __init__(self, parent, controller, title, tabla, id_col, nombre_col, **kwargs):
        super().__init__(parent, controller, title)
        self.tabla, self.id_col, self.nombre_col = tabla, id_col, nombre_col
        add_frame = tk.LabelFrame(self, text=f"Agregar Nuevo/a {title.split(' ')[-1]}", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10, font=FONT_BOLD)
        add_frame.pack(fill="x", pady=5)
        tk.Label(add_frame, text="Nombre:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(side=tk.LEFT, padx=5)
        self.new_entry = tk.Entry(add_frame, width=40, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, insertbackground=FG_COLOR)
        self.new_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True, ipady=4)
        ttk.Button(add_frame, text="Agregar", command=self.agregar).pack(side=tk.LEFT, padx=5)
        tree_frame = tk.Frame(self, bg=BG_COLOR); tree_frame.pack(fill="both", expand=True, pady=5)
        self.tree = crear_tabla(tree_frame, ('ID', 'Nombre'), widths={'ID': 50, 'Nombre': 600})
        self.tree.pack(fill="both", expand=True)
        action_frame = tk.Frame(self, bg=BG_COLOR); action_frame.pack(fill="x", pady=5, anchor="e")
        ttk.Button(action_frame, text="Eliminar", command=self.eliminar, style="Accent.TButton").pack(side="right", padx=5)
        ttk.Button(action_frame, text="Editar", command=self.editar).pack(side="right")
        self.populate_tree()

    def populate_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for item in db_manager.get_catalogo(self.controller.conexion, self.tabla, self.id_col, self.nombre_col):
            self.tree.insert("", "end", values=(item[self.id_col], item[self.nombre_col]))

    def agregar(self):
        new_val = self.new_entry.get()
        if not new_val: messagebox.showwarning("Campo Vacío", "Introduce un nombre.", parent=self); return
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        success, msg = db_manager.crear_item_catalogo(self.controller.conexion, self.tabla, self.nombre_col, new_val)
        self.controller.config(cursor="")
        if success: self.new_entry.delete(0, tk.END); self.populate_tree()
        messagebox.showinfo("Resultado", msg, parent=self)

    def editar(self):
        selected = self.tree.selection()
        if not selected: messagebox.showwarning("Selección Requerida", "Selecciona un elemento para editar.", parent=self); return
        item_id, nombre_actual = self.tree.item(selected[0])['values']
        nuevo_nombre = simpledialog.askstring("Editar", "Introduce el nuevo nombre:", initialvalue=nombre_actual, parent=self)
        if nuevo_nombre and nuevo_nombre.strip() and nuevo_nombre != nombre_actual:
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            success, msg = db_manager.actualizar_item_catalogo(self.controller.conexion, self.tabla, self.id_col, self.nombre_col, item_id, nuevo_nombre)
            self.controller.config(cursor="")
            if success: self.populate_tree()
            messagebox.showinfo("Resultado", msg, parent=self)

    def eliminar(self):
        selected = self.tree.selection()
        if not selected: messagebox.showwarning("Selección Requerida", "Selecciona un elemento para eliminar.", parent=self); return
        item_id, nombre = self.tree.item(selected[0])['values']
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar '{nombre}'?", parent=self):
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            success, msg = db_manager.eliminar_item_catalogo(self.controller.conexion, self.tabla, self.id_col, item_id)
            self.controller.config(cursor="")
            if success: self.populate_tree()
            messagebox.showinfo("Resultado", msg, parent=self)

class CrearVacanteWindow(FormularioBase):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, controller, "Crear Nueva Vacante")
        self.on_success_callback = kwargs.get('on_success_callback')
        self.profesiones = db_manager.get_catalogo(self.controller.conexion, 'Profesiones', 'ID_Profesion', 'Nombre_Profesion')
        self.prof_map = {p['Nombre_Profesion']: p['ID_Profesion'] for p in self.profesiones}
        if not self.profesiones: messagebox.showwarning("Advertencia", "No hay profesiones registradas. No se puede crear una vacante.", parent=self); self.destroy(); return
        frame = tk.Frame(self, bg=BG_COLOR); self.crear_campo(frame, "Cargo Vacante"); self.crear_campo(frame, "Descripción del Perfil", tipo="scrolledtext")
        self.crear_campo(frame, "Salario Ofrecido"); self.crear_campo(frame, "Profesión Requerida", tipo="combobox", values=list(self.prof_map.keys()))
        frame.pack(pady=10); ttk.Button(self, text="Guardar Vacante", command=self.guardar, style="Accent.TButton").pack(pady=15)

    def guardar(self):
        datos = {k: (v.get("1.0", "end-1c") if isinstance(v, scrolledtext.ScrolledText) else v.get()) for k, v in self.entries.items()}
        try:
            salario = float(datos.get("Salario Ofrecido", 0))
            if salario <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Entrada no válida", "El salario debe ser un número positivo.", parent=self); return
        
        id_profesion = self.prof_map.get(datos.get("Profesión Requerida"))
        if not all([datos.get("Cargo Vacante"), id_profesion]):
            messagebox.showerror("Error", "Cargo y Profesión son obligatorios.", parent=self); return

        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        success, message = db_manager.crear_vacante_db(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'], datos["Cargo Vacante"], datos["Descripción del Perfil"], salario, id_profesion)
        self.controller.config(cursor="")
        
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            if self.on_success_callback: self.on_success_callback()
            self.destroy()
        else:
            messagebox.showerror("Error al Guardar", message, parent=self)

class ActualizarVacanteWindow(FormularioBase):
    def __init__(self, parent, controller, datos_vacante, **kwargs):
        super().__init__(parent, controller, "Editar Vacante")
        self.on_success_callback = kwargs.get('on_success_callback')
        self.id_vacante = datos_vacante['ID_Vacante']; frame = tk.Frame(self, bg=BG_COLOR)
        self.crear_campo(frame, "Cargo Vacante"); self.crear_campo(frame, "Descripción del Perfil", tipo="scrolledtext")
        self.crear_campo(frame, "Salario Ofrecido"); self.crear_campo(frame, "Estatus", tipo="combobox", values=['Activa', 'Inactiva', 'Cerrada']); frame.pack(pady=10)
        self.entries["Cargo Vacante"].insert(0, datos_vacante['Cargo_Vacante']); self.entries["Descripción del Perfil"].insert("1.0", datos_vacante['Descripcion_Perfil'])
        self.entries["Salario Ofrecido"].insert(0, f"{float(datos_vacante['Salario_Ofrecido']):.2f}"); self.entries["Estatus"].set(datos_vacante['Estatus'])
        ttk.Button(self, text="Guardar Cambios", command=self.guardar, style="Accent.TButton").pack(pady=15)

    def guardar(self):
        datos = {k: (v.get("1.0", "end-1c") if isinstance(v, scrolledtext.ScrolledText) else v.get()) for k, v in self.entries.items()}
        try:
            salario = float(datos.get("Salario Ofrecido", 0))
            if salario <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Entrada no válida", "El salario debe ser un número positivo.", parent=self); return
        if not all(datos.values()): messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self); return

        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        success, message = db_manager.actualizar_vacante_db(self.controller.conexion, self.id_vacante, datos["Cargo Vacante"], datos["Descripción del Perfil"], salario, datos["Estatus"])
        self.controller.config(cursor="")

        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            if self.on_success_callback: self.on_success_callback()
            self.destroy()
        else:
            messagebox.showerror("Error al Guardar", message, parent=self)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Sistema de Gestión Hiring Group"); self.geometry("950x700"); self.minsize(800, 600)
        self.configure(bg=BG_COLOR); self.conexion = None; self.usuario_actual = None; self.rol_actual = None
        self.setup_styles(); self.container = tk.Frame(self, bg=BG_COLOR); self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1); self.container.grid_columnconfigure(0, weight=1); self.show_frame(LoginFrame)

    def setup_styles(self):
        style = ttk.Style(self); style.theme_use("clam")
        style.configure("TButton", background=BUTTON_BG, foreground=FG_COLOR, borderwidth=0, font=FONT_BOLD, padding=10)
        style.map("TButton", background=[("active", ACCENT_ACTIVE)], foreground=[("active", FG_COLOR)])
        style.configure("Accent.TButton", background=ACCENT_COLOR, foreground=FG_COLOR); style.map("Accent.TButton", background=[("active", ACCENT_ACTIVE)])
        style.configure("Treeview", background=ENTRY_BG, foreground=FG_COLOR, fieldbackground=ENTRY_BG, rowheight=25, font=FONT_NORMAL)
        style.map("Treeview", background=[("selected", ACCENT_COLOR)], foreground=[("selected", FG_COLOR)])
        style.configure("Treeview.Heading", background=BUTTON_BG, foreground=FG_COLOR, font=FONT_BOLD, relief="flat", padding=5)
        style.map("Treeview.Heading", background=[("active", BUTTON_BG)])
        style.configure("TCombobox", fieldbackground=ENTRY_BG, background=BUTTON_BG, foreground=FG_COLOR, arrowcolor=FG_COLOR, selectbackground=ENTRY_BG, selectforeground=FG_COLOR)
        self.option_add('*TCombobox*Listbox.background', ENTRY_BG); self.option_add('*TCombobox*Listbox.foreground', FG_COLOR)
        self.option_add('*TCombobox*Listbox.selectBackground', ACCENT_COLOR); self.option_add('*TCombobox*Listbox.font', FONT_NORMAL)

    def show_frame(self, FrameClass):
        for widget in self.container.winfo_children(): widget.destroy()
        frame = FrameClass(parent=self.container, controller=self); frame.grid(row=0, column=0, sticky="nsew")

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR); self.controller = controller
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        login_container = tk.Frame(self, bg=BG_COLOR); login_container.grid(row=0, column=0)
        tk.Label(login_container, text="Login del Sistema", font=("Segoe UI", 20, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=20)
        tk.Label(login_container, text="Email", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack()
        self.email_entry = tk.Entry(login_container, width=40, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, justify="center")
        self.email_entry.pack(pady=5, ipady=5); self.email_entry.focus()
        tk.Label(login_container, text="Contraseña", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack()
        self.pass_entry = tk.Entry(login_container, width=40, show="*", bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, justify="center")
        self.pass_entry.pack(pady=5, ipady=5); self.pass_entry.bind("<Return>", self.attempt_login)
        ttk.Button(login_container, text="Ingresar", command=self.attempt_login, style="Accent.TButton").pack(pady=20, ipady=5, ipadx=10)

    def attempt_login(self, event=None):
        if not self.controller.conexion or not self.controller.conexion.is_connected():
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            self.controller.conexion = db_manager.conectar_db(password='')
            self.controller.config(cursor="")
            if not self.controller.conexion:
                password_db = simpledialog.askstring("Contraseña DB", "La conexión automática falló. Introduce la contraseña de tu BD (MySQL):", show='*')
                if password_db is None: return
                self.controller.config(cursor="watch"); self.controller.update_idletasks()
                self.controller.conexion = db_manager.conectar_db(password=password_db)
                self.controller.config(cursor="")
                if not self.controller.conexion:
                    messagebox.showerror("Error de Conexión", "No se pudo conectar. Verifica que el servidor (XAMPP) esté activo y la contraseña sea correcta.")
                    return
        
        email = self.email_entry.get(); password = self.pass_entry.get()
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        usuario, rol = db_manager.login_usuario(self.controller.conexion, email, password)
        self.controller.config(cursor="")
        
        if usuario:
            self.controller.usuario_actual, self.controller.rol_actual = usuario, rol
            self.controller.show_frame(MainFrame)
        else:
            messagebox.showerror("Login Fallido", "Email, contraseña incorrectos o usuario inactivo.")

class MainFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR); self.controller = controller
        menu_frame = tk.Frame(self, bg="#0F172A", width=220); menu_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10,0), pady=10)
        menu_frame.pack_propagate(False); self.content_frame = tk.Frame(self, bg=BG_COLOR)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        rol = self.controller.rol_actual
        tk.Label(menu_frame, text=f"Menú - {rol}", font=FONT_MENU_TITLE, bg="#0F172A", fg=FG_COLOR).pack(pady=20)
        botones = {'HiringGroup': [("Crear Usuario", lambda: self.open_form_window(CrearUsuarioWindow)), ("Gestionar Empresas", self.show_gestionar_empresas), ("Gestionar Catálogos", self.show_menu_catalogos), ("Contratar Postulante", self.show_contratar_form), ("Ejecutar Nómina", self.show_nomina_form), ("Reportes de Nómina", self.show_reportes_nomina)],
                   'Empresa': [("Crear Vacante", lambda: self.open_form_window(CrearVacanteWindow, on_success_callback=self.show_mis_vacantes)), ("Ver Mis Vacantes", self.show_mis_vacantes), ("Editar Mi Perfil", lambda: self.open_form_window(ActualizarUsuarioWindow))],
                   'Postulante': [("Buscar Vacantes", self.show_buscar_vacantes), ("Mis Postulaciones", self.show_mis_postulaciones), ("Editar Mi Perfil", lambda: self.open_form_window(ActualizarUsuarioWindow)), ("Gestionar Experiencia", lambda: self.open_form_window(GestionarExperienciaWindow))],
                   'Contratado': [("Ver Vacantes", lambda: self.show_buscar_vacantes(read_only=True)), ("Mis Recibos de Pago", self.show_recibos_pago), ("Generar Constancia", self.show_constancia), ("Editar Mi Perfil", lambda: self.open_form_window(ActualizarUsuarioWindow))]}
        for texto, comando in botones.get(rol, []):
            ttk.Button(menu_frame, text=texto, command=comando).pack(fill=tk.X, pady=4, padx=10)
        ttk.Button(menu_frame, text="Salir (Logout)", command=self.logout, style="Accent.TButton").pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=10)
        self.show_welcome_message()

    def show_welcome_message(self):
        self.clear_content_frame(); tk.Label(self.content_frame, text=f"Bienvenido/a, {self.controller.usuario_actual['Email']}", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w", pady=(0, 10))
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()
    def logout(self):
        self.controller.usuario_actual, self.controller.rol_actual = None, None; self.controller.show_frame(LoginFrame)
    def open_form_window(self, WindowClass, *args, **kwargs):
        WindowClass(self.controller, self.controller, *args, **kwargs)
    
    def show_gestionar_empresas(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Gestionar Empresas", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        empresas = db_manager.get_catalogo(self.controller.conexion, 'Empresas', 'ID_Empresa', 'Nombre_Empresa, RIF, Sector_Industrial, Persona_Contacto, Telefono_Contacto, Email_Contacto')
        self.controller.config(cursor="")
        if not empresas: tk.Label(self.content_frame, text="No hay empresas registradas.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        tree = crear_tabla(self.content_frame, ('ID', 'Nombre', 'RIF', 'Sector', 'Contacto', 'Teléfono', 'Email'), widths={'ID': 40, 'Nombre': 150, 'RIF': 80})
        for e in empresas: tree.insert("", "end", values=(e['ID_Empresa'], e['Nombre_Empresa'], e['RIF'], e['Sector_Industrial'], e['Persona_Contacto'], e['Telefono_Contacto'], e['Email_Contacto']))
        tree.pack(fill="both", expand=True, pady=5)

    def show_menu_catalogos(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Gestionar Catálogos", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        catalogos = {"Áreas de Conocimiento": ('Areas_Conocimiento', 'ID_Area_Conocimiento', 'Nombre_Area'), "Profesiones": ('Profesiones', 'ID_Profesion', 'Nombre_Profesion'), "Universidades": ('Universidades', 'ID_Universidad', 'Nombre_Universidad'), "Bancos": ('Bancos', 'ID_Banco', 'Nombre_Banco')}
        for title, args in catalogos.items(): ttk.Button(self.content_frame, text=f"Gestionar {title}", command=lambda t=title, a=args: self.open_form_window(GestionCatalogoWindow, title=f"Gestionar {t}", tabla=a[0], id_col=a[1], nombre_col=a[2])).pack(fill='x', padx=20, pady=5)

    def show_contratar_form(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Contratar Postulante", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        postulaciones = db_manager.get_postulaciones_para_contratar(self.controller.conexion)
        bancos = db_manager.get_catalogo(self.controller.conexion, 'Bancos', 'ID_Banco', 'Nombre_Banco')
        self.controller.config(cursor="")
        if not postulaciones: tk.Label(self.content_frame, text="No hay postulaciones recibidas.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        tree = crear_tabla(self.content_frame, ('ID', 'Nombre', 'Cargo'));
        for p in postulaciones: tree.insert("", "end", values=(p['ID_Postulacion'], f"{p['Nombres']} {p['Apellidos']}", p['Cargo_Vacante']))
        tree.pack(fill="x", pady=5)
        form_frame = tk.Frame(self.content_frame, pady=10, bg=BG_COLOR); entries = {}; bancos_map = {b['Nombre_Banco']: b['ID_Banco'] for b in bancos}
        fields = [("Salario", "entry"), ("Tipo Contrato", "combo_contrato"), ("Tipo de Sangre", "entry"), ("Nombre Contacto Emergencia", "entry"), ("Teléfono Contacto Emergencia", "entry"), ("Número de Cuenta", "entry"), ("Banco", "combo_banco")]
        for i, (label_text, widget_type) in enumerate(fields):
            tk.Label(form_frame, text=f"{label_text}:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=i, column=0, padx=5, pady=5, sticky='w')
            widget = None
            if widget_type == "entry": widget = tk.Entry(form_frame, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR)
            elif widget_type == "combo_contrato": widget = ttk.Combobox(form_frame, values=['Un mes', 'Seis meses', 'Un año', 'Indefinido'], state="readonly")
            elif widget_type == "combo_banco": widget = ttk.Combobox(form_frame, values=list(bancos_map.keys()), state="readonly")
            if widget: widget.grid(row=i, column=1, padx=5, pady=5, sticky='we', ipady=4); entries[label_text] = widget
        form_frame.pack(anchor="w")
        def contratar():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Por favor, selecciona una postulación."); return
            try:
                salario_val = float(entries["Salario"].get())
                if salario_val <= 0: raise ValueError
            except (ValueError, TypeError): messagebox.showerror("Entrada no válida", "El salario debe ser un número positivo."); return
            id_postulacion = tree.item(selected[0])['values'][0]
            
            datos_contrato = {
                'Salario_Acordado': salario_val,
                'Tipo_Contrato': entries['Tipo Contrato'].get(),
                'Tipo_Sangre': entries['Tipo de Sangre'].get(),
                'Contacto_Emergencia_Nombre': entries['Nombre Contacto Emergencia'].get(),
                'Contacto_Emergencia_Telefono': entries['Teléfono Contacto Emergencia'].get(),
                'Numero_Cuenta': entries['Número de Cuenta'].get(),
                'ID_Banco': bancos_map.get(entries['Banco'].get())
            }
            
            if not all(v is not None if k == 'ID_Banco' else v for k,v in datos_contrato.items()): messagebox.showerror("Error", "Todos los campos son obligatorios."); return
            
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            success, msg = db_manager.contratar_postulante_db(self.controller.conexion, id_postulacion, datos_contrato)
            self.controller.config(cursor="")
            if success: messagebox.showinfo("Resultado", msg); self.show_contratar_form()
            else: messagebox.showerror("Error", msg)
        ttk.Button(self.content_frame, text="Contratar y Aceptar", command=contratar, style="Accent.TButton").pack(pady=10, anchor="w")
    
    def show_buscar_vacantes(self, read_only=False):
        self.show_welcome_message()
        title = "Vacantes Disponibles" if not read_only else "Visualizar Vacantes"
        tk.Label(self.content_frame, text=title, font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        filter_frame = tk.Frame(self.content_frame, bg=BG_COLOR); filter_frame.pack(fill='x', pady=5)
        areas = db_manager.get_catalogo(self.controller.conexion, 'Areas_Conocimiento', 'ID_Area_Conocimiento', 'Nombre_Area')
        area_map = {"Todas": None}; area_map.update({a['Nombre_Area']: a['ID_Area_Conocimiento'] for a in areas})
        tk.Label(filter_frame, text="Área:", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)
        area_combo = ttk.Combobox(filter_frame, values=list(area_map.keys()), state="readonly", width=20); area_combo.pack(side=tk.LEFT, padx=5); area_combo.set("Todas")
        tk.Label(filter_frame, text="Salario:", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)
        salary_combo = ttk.Combobox(filter_frame, values=["Sin Orden", "Mayor a Menor", "Menor a Mayor"], state="readonly", width=15); salary_combo.pack(side=tk.LEFT, padx=5); salary_combo.set("Sin Orden")
        tree = crear_tabla(self.content_frame, ('ID', 'Cargo', 'Empresa', 'Área', 'Profesión', 'Salario'), widths={'ID': 40, 'Salario': 80})
        tree.pack(fill="both", expand=True, pady=5)
        def populate_tree():
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            for i in tree.get_children(): tree.delete(i)
            filtro_area = area_map[area_combo.get()]
            sort_map = {"Mayor a Menor": "DESC", "Menor a Mayor": "ASC"}; sort_salary = sort_map.get(salary_combo.get())
            vacantes = db_manager.get_active_vacantes(self.controller.conexion, filtro_area=filtro_area, sort_salary=sort_salary)
            self.controller.config(cursor="")
            for v in vacantes:
                area_nombre = v['Nombre_Area'] or 'No Asignada'
                tree.insert("", "end", values=(v['ID_Vacante'], v['Cargo_Vacante'], v['Nombre_Empresa'], area_nombre, v['Nombre_Profesion'], f"{float(v['Salario_Ofrecido']):.2f}"))
        ttk.Button(filter_frame, text="Filtrar", command=populate_tree).pack(side=tk.LEFT, padx=10)
        if not read_only: ttk.Button(self.content_frame, text="Aplicar a Vacante", command=lambda: self.aplicar(tree), style="Accent.TButton").pack(pady=10, anchor="e")
        populate_tree()

    def aplicar(self, tree):
        selected = tree.selection()
        if not selected: messagebox.showwarning("Selección Requerida", "Selecciona una vacante para aplicar."); return
        id_vacante = tree.item(selected[0])['values'][0]
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        success, msg = db_manager.aplicar_a_vacante_db(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'], id_vacante)
        self.controller.config(cursor="")
        messagebox.showinfo("Resultado", msg)

    def show_recibos_pago(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Mis Recibos de Pago", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        filter_frame = tk.Frame(self.content_frame, bg=BG_COLOR); filter_frame.pack(fill='x', pady=5)
        tk.Label(filter_frame, text="Mes (opc):", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)
        mes_entry = tk.Entry(filter_frame, width=5, bg=ENTRY_BG, fg=FG_COLOR); mes_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(filter_frame, text="Año (opc):", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)
        anio_entry = tk.Entry(filter_frame, width=7, bg=ENTRY_BG, fg=FG_COLOR); anio_entry.pack(side=tk.LEFT, padx=5)
        tree = crear_tabla(self.content_frame, ('Periodo', 'Fecha Pago', 'Salario Base', 'Salario Neto'))
        tree.pack(fill="both", expand=True, pady=5)
        def populate_recibos():
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            for i in tree.get_children(): tree.delete(i)
            recibos = db_manager.get_recibos_por_contratado(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'], mes_entry.get() or None, anio_entry.get() or None)
            self.controller.config(cursor="")
            for r in recibos: tree.insert("", "end", values=(f"{r['Mes']}/{r['Anio']}", r['Fecha_Pago'], f"{r['Salario_Base']:.2f}", f"{r['Salario_Neto_Pagado']:.2f}"))
        ttk.Button(filter_frame, text="Filtrar", command=populate_recibos).pack(side=tk.LEFT, padx=10)
        populate_recibos()
    
    def show_mis_vacantes(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Mis Vacantes Publicadas", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        vacantes = db_manager.get_vacantes_por_empresa(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        self.controller.config(cursor="")
        if not vacantes: tk.Label(self.content_frame, text="No tienes vacantes publicadas.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        tree = crear_tabla(self.content_frame, ('ID', 'Cargo', 'Salario', 'Estatus'), widths={'ID': 50, 'Estatus': 80})
        for v in vacantes:
            salario = f"{float(v['Salario_Ofrecido']):.2f}" if v['Salario_Ofrecido'] else "N/A"
            tree.insert("", "end", values=(v['ID_Vacante'], v['Cargo_Vacante'], salario, v['Estatus']))
        tree.pack(fill="both", expand=True, pady=5)
        buttons_frame = tk.Frame(self.content_frame, bg=BG_COLOR); buttons_frame.pack(fill="x", pady=5, anchor="e")
        def editar_vacante():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Selecciona una vacante para editar.", parent=self.controller); return
            id_vacante = tree.item(selected[0])['values'][0]
            datos_vacante = next((v for v in vacantes if v['ID_Vacante'] == id_vacante), None)
            if datos_vacante: self.open_form_window(ActualizarVacanteWindow, datos_vacante=datos_vacante, on_success_callback=self.show_mis_vacantes)
        def eliminar_vacante():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Selecciona una vacante para eliminar.", parent=self.controller); return
            id_vacante, cargo = tree.item(selected[0])['values'][:2]
            if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar la vacante '{cargo}'?", parent=self.controller):
                self.controller.config(cursor="watch"); self.controller.update_idletasks()
                success, msg = db_manager.eliminar_vacante_db(self.controller.conexion, id_vacante)
                self.controller.config(cursor="")
                if success: messagebox.showinfo("Resultado", msg, parent=self.controller); self.show_mis_vacantes()
        ttk.Button(buttons_frame, text="Eliminar Vacante", command=eliminar_vacante, style="Accent.TButton").pack(side="right", padx=5)
        ttk.Button(buttons_frame, text="Editar Vacante", command=editar_vacante).pack(side="right")
        
    def show_reportes_nomina(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Reportes de Nómina", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        rep1_frame = tk.LabelFrame(self.content_frame, text="Nómina por Empresa", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10, font=FONT_BOLD); rep1_frame.pack(fill="x", pady=5)
        empresas = db_manager.get_catalogo(self.controller.conexion, 'Empresas', 'ID_Empresa', 'Nombre_Empresa'); empresa_map = {e['Nombre_Empresa']: e['ID_Empresa'] for e in empresas}
        tk.Label(rep1_frame, text="Empresa:", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, padx=5)
        empresa_combo = ttk.Combobox(rep1_frame, values=list(empresa_map.keys()), state="readonly"); empresa_combo.grid(row=0, column=1, padx=5)
        tk.Label(rep1_frame, text="Mes:", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=2, padx=5)
        mes_entry = tk.Entry(rep1_frame, width=5, bg=ENTRY_BG, fg=FG_COLOR); mes_entry.grid(row=0, column=3, padx=5)
        tk.Label(rep1_frame, text="Año:", bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=4, padx=5)
        anio_entry = tk.Entry(rep1_frame, width=7, bg=ENTRY_BG, fg=FG_COLOR); anio_entry.grid(row=0, column=5, padx=5)
        tree1 = crear_tabla(rep1_frame, ('Empleado', 'Cédula', 'Salario Base')); tree1.grid(row=1, column=0, columnspan=7, sticky='we', pady=10)
        def buscar_nomina():
            id_empresa = empresa_map.get(empresa_combo.get())
            try:
                mes = int(mes_entry.get()); anio = int(anio_entry.get())
                if not (1 <= mes <= 12 and 2000 <= anio <= 2100): raise ValueError
            except (ValueError, TypeError): messagebox.showerror("Entrada no válida", "Por favor, introduce un mes (1-12) y año válidos."); return
            if not id_empresa: messagebox.showerror("Error", "Debes seleccionar una empresa"); return
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            for i in tree1.get_children(): tree1.delete(i)
            reporte = db_manager.get_nomina_reporte_db(self.controller.conexion, id_empresa, mes, anio)
            self.controller.config(cursor="")
            for row in reporte: tree1.insert("", "end", values=(row['Empleado'], row['Cedula_Identidad'], f"{row['Salario_Base']:.2f}"))
        ttk.Button(rep1_frame, text="Buscar", command=buscar_nomina).grid(row=0, column=6, padx=10)
        rep2_frame = tk.LabelFrame(self.content_frame, text="Nómina General por Empresa", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10, font=FONT_BOLD); rep2_frame.pack(fill="x", pady=5, expand=True)
        tree2 = crear_tabla(rep2_frame, ('Empresa', 'Periodo', 'Total Nómina')); tree2.pack(fill='both', expand=True, pady=5)
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        reporte_total = db_manager.get_toda_nomina_reporte_db(self.controller.conexion)
        self.controller.config(cursor="")
        for row in reporte_total: tree2.insert("", "end", values=(row['Nombre_Empresa'], f"{row['Mes']}/{row['Anio']}", f"{row['Total_Nomina']:.2f}"))

    def show_nomina_form(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Ejecutar Nómina Mensual", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        empresas = db_manager.get_catalogo(self.controller.conexion, 'Empresas', 'ID_Empresa', 'Nombre_Empresa')
        if not empresas: tk.Label(self.content_frame, text="No hay empresas registradas.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        form_frame = tk.Frame(self.content_frame, pady=10, bg=BG_COLOR); empresa_map = {e['Nombre_Empresa']: e['ID_Empresa'] for e in empresas}
        tk.Label(form_frame, text="Empresa:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        empresa_combo = ttk.Combobox(form_frame, values=list(empresa_map.keys()), state="readonly", width=30, font=FONT_NORMAL); empresa_combo.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Mes (1-12):", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=1, column=0, padx=5, pady=5, sticky='w')
        mes_entry = tk.Entry(form_frame, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, insertbackground=FG_COLOR); mes_entry.grid(row=1, column=1, padx=5, pady=5, ipady=4)
        tk.Label(form_frame, text="Año (YYYY):", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=2, column=0, padx=5, pady=5, sticky='w')
        anio_entry = tk.Entry(form_frame, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, insertbackground=FG_COLOR); anio_entry.grid(row=2, column=1, padx=5, pady=5, ipady=4)
        form_frame.pack(anchor="w")
        def generar():
            nombre_empresa = empresa_combo.get()
            try:
                mes = int(mes_entry.get()); anio = int(anio_entry.get())
                if not (1 <= mes <= 12 and 2000 <= anio <= 2100): raise ValueError
            except (ValueError, TypeError): messagebox.showerror("Entrada no válida", "Por favor, introduce un mes (1-12) y año válidos."); return
            if not nombre_empresa: messagebox.showerror("Error", "Debes seleccionar una empresa"); return
            id_empresa = empresa_map.get(nombre_empresa)
            self.controller.config(cursor="watch"); self.controller.update_idletasks()
            success, msg = db_manager.ejecutar_nomina_db(self.controller.conexion, id_empresa, mes, anio)
            self.controller.config(cursor="")
            messagebox.showinfo("Resultado", msg)
        ttk.Button(self.content_frame, text="Generar Nómina", command=generar, style="Accent.TButton").pack(pady=10, anchor="w")

    def show_mis_postulaciones(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Mis Postulaciones Realizadas", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        postulaciones = db_manager.get_postulaciones_por_postulante(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        self.controller.config(cursor="")
        if not postulaciones: tk.Label(self.content_frame, text="No has realizado ninguna postulación.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        tree = crear_tabla(self.content_frame, ('Cargo', 'Empresa', 'Salario', 'Fecha', 'Estatus'))
        for p in postulaciones:
            salario = f"{float(p['Salario_Ofrecido']):.2f}" if p['Salario_Ofrecido'] else "N/A"
            fecha = p['Fecha_Postulacion'].strftime('%Y-%m-%d %H:%M') if p['Fecha_Postulacion'] else 'N/A'
            tree.insert("", "end", values=(p['Cargo_Vacante'], p['Nombre_Empresa'], salario, fecha, p['Estatus']))
        tree.pack(fill="both", expand=True, pady=5)
        
    def show_constancia(self):
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Constancia de Trabajo", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        self.controller.config(cursor="watch"); self.controller.update_idletasks()
        texto_constancia = db_manager.get_datos_constancia(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        self.controller.config(cursor="")
        if texto_constancia:
            text_widget = tk.Text(self.content_frame, height=15, width=80, font=("Courier", 11), wrap="word", bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, bd=0, padx=10, pady=10)
            text_widget.insert(tk.END, texto_constancia); text_widget.config(state="disabled"); text_widget.pack(pady=10, fill="x")
        else:
            tk.Label(self.content_frame, text="No se pudo generar la constancia. No se encontró un contrato activo.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack()

if __name__ == "__main__":
    app = App()
    app.mainloop()