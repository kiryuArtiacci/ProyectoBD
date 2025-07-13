import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import db_manager

# --- CONSTANTES DE ESTILO ---
BG_COLOR = "#0F172A"       # Fondo
FG_COLOR = "#E2E8F0"       # Texto
ENTRY_BG = "#1E293B"       # Inputs
BUTTON_BG = "#334155"      # Algunos botones
ACCENT_COLOR = "#9333EA"   # Morado para selecciones y acentos
ACCENT_ACTIVE = "#A855F7"  # Morado más brillante para hover

FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_MENU_TITLE = ("Segoe UI", 12, "bold")

# --- CLASES DE VENTANAS DE FORMULARIO (TOPLEVEL) ---
class FormularioBase(tk.Toplevel):
    def __init__(self, parent, controller, title):
        super().__init__(parent)
        self.title(title)
        self.config(bg=BG_COLOR, padx=20, pady=20)
        self.transient(parent)
        self.grab_set()
        self.controller = controller
        self.entries = {}
        self.resizable(False, False)

    def crear_campo(self, frame, texto, tipo="entry"):
        row = tk.Frame(frame, bg=BG_COLOR)
        label = tk.Label(row, width=20, text=f"{texto}:", anchor='w', bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL)
        
        widget = None
        if tipo == "entry":
            widget = tk.Entry(row, width=40, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL)
            if "Contraseña" in texto:
                widget.config(show="*")
        elif tipo == "combobox":
            widget = ttk.Combobox(row, width=37, state="readonly", font=FONT_NORMAL)

        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        label.pack(side=tk.LEFT)
        if widget:
            widget.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X, ipady=4)
        self.entries[texto] = widget
        return widget

class CrearUsuarioWindow(FormularioBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Crear Nuevo Usuario")
        self.campos_especificos = {"Postulante": ["Nombres", "Apellidos", "Cédula", "Teléfono"],"Empresa": ["Nombre Empresa", "RIF", "Sector"],"HiringGroup": []}
        
        top_frame = tk.Frame(self, bg=BG_COLOR)
        tk.Label(top_frame, text="Tipo de Usuario:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(side=tk.LEFT, padx=5)
        self.tipo_usuario_combo = ttk.Combobox(top_frame, values=list(self.campos_especificos.keys()), state="readonly")
        self.tipo_usuario_combo.pack(side=tk.LEFT, padx=5, pady=10)
        self.tipo_usuario_combo.bind("<<ComboboxSelected>>", self.actualizar_campos)
        top_frame.pack()
        
        self.form_frame = tk.Frame(self, bg=BG_COLOR)
        self.form_frame.pack(pady=10)
        ttk.Button(self, text="Crear Usuario", command=self.crear, style="Accent.TButton").pack(pady=15)
        self.actualizar_campos(None)

    def actualizar_campos(self, event):
        for widget in self.form_frame.winfo_children(): widget.destroy()
        self.entries = {}
        self.crear_campo(self.form_frame, "Email")
        self.crear_campo(self.form_frame, "Contraseña")
        for field in self.campos_especificos.get(self.tipo_usuario_combo.get(), []): self.crear_campo(self.form_frame, field)

    def crear(self):
        tipo_usuario = self.tipo_usuario_combo.get()
        if not tipo_usuario: messagebox.showerror("Error", "Debes seleccionar un tipo de usuario.", parent=self); return
        datos = {k: v.get() for k, v in self.entries.items()}
        if not all(v for k, v in datos.items() if k != "Contraseña" or (k == "Contraseña" and v)):
             messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self)
             return
        success, message = db_manager.registrar_usuario_db(self.controller.conexion, tipo_usuario, datos)
        if success: messagebox.showinfo("Éxito", message, parent=self); self.destroy()
        else: messagebox.showerror("Error al Crear", message, parent=self)

class CrearVacanteWindow(FormularioBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Crear Nueva Vacante")
        self.profesiones = db_manager.get_profesiones(self.controller.conexion)
        profesiones_nombres = [p['Nombre_Profesion'] for p in self.profesiones] if self.profesiones else []
        if not profesiones_nombres: messagebox.showwarning("Advertencia", "No hay profesiones registradas.", parent=self)

        frame = tk.Frame(self, bg=BG_COLOR)
        self.crear_campo(frame, "Cargo Vacante")
        self.crear_campo(frame, "Descripción")
        self.crear_campo(frame, "Salario Ofrecido")
        profesion_combo = self.crear_campo(frame, "Profesión", tipo="combobox")
        profesion_combo['values'] = profesiones_nombres
        frame.pack(pady=10)
        ttk.Button(self, text="Guardar Vacante", command=self.guardar, style="Accent.TButton").pack(pady=15)

    def guardar(self):
        vals = {k: v.get() for k, v in self.entries.items() if k != "Profesión"}
        selected_prof_name = self.entries["Profesión"].get()
        if not all(vals.values()) or not selected_prof_name: messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self); return
        id_profesion = next((p['ID_Profesion'] for p in self.profesiones if p['Nombre_Profesion'] == selected_prof_name), None)
        success, message = db_manager.crear_vacante_db(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'], vals["Cargo Vacante"], vals["Descripción"], vals["Salario Ofrecido"], id_profesion)
        if success: 
            messagebox.showinfo("Éxito", message, parent=self)
            self.controller.nametowidget('.!app.!mainframe').show_mis_vacantes()
            self.destroy()
        else: 
            messagebox.showerror("Error al Guardar", message, parent=self)

class ActualizarUsuarioWindow(FormularioBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Editar Mi Perfil")
        self.tipo_usuario = self.controller.rol_actual
        self.id_usuario = self.controller.usuario_actual['ID_Usuario']

        form_frame = tk.Frame(self, bg=BG_COLOR)
        if self.tipo_usuario == 'Postulante':
            self.crear_campo(form_frame, "Nombres")
            self.crear_campo(form_frame, "Apellidos")
            self.crear_campo(form_frame, "Teléfono")
        elif self.tipo_usuario == 'Empresa':
            self.crear_campo(form_frame, "Nombre Empresa")
            self.crear_campo(form_frame, "Sector")
        self.crear_campo(form_frame, "Nueva Contraseña (opcional)")
        form_frame.pack(pady=10)
        
        ttk.Button(self, text="Guardar Cambios", command=self.actualizar, style="Accent.TButton").pack(pady=15)

    def actualizar(self):
        datos = {k: v.get() for k, v in self.entries.items()}
        if "Nueva Contraseña (opcional)" in datos:
            datos["Contraseña"] = datos.pop("Nueva Contraseña (opcional)")

        success, message = db_manager.actualizar_usuario_db(self.controller.conexion, self.id_usuario, self.tipo_usuario, datos)
        if success: messagebox.showinfo("Éxito", message, parent=self); self.destroy()
        else: messagebox.showerror("Error al Actualizar", message, parent=self)

class ActualizarVacanteWindow(FormularioBase):
    def __init__(self, parent, controller, datos_vacante):
        super().__init__(parent, controller, "Editar Vacante")
        self.id_vacante = datos_vacante['ID_Vacante']

        frame = tk.Frame(self, bg=BG_COLOR)
        self.crear_campo(frame, "Cargo Vacante")
        self.crear_campo(frame, "Descripción")
        self.crear_campo(frame, "Salario Ofrecido")
        estatus_combo = self.crear_campo(frame, "Estatus", tipo="combobox")
        estatus_combo['values'] = ['Activa', 'Cerrada']
        frame.pack(pady=10)
        
        self.entries["Cargo Vacante"].insert(0, datos_vacante['Cargo_Vacante'])
        self.entries["Descripción"].insert(0, datos_vacante['Descripcion_Perfil'])
        self.entries["Salario Ofrecido"].insert(0, f"{float(datos_vacante['Salario_Ofrecido']):.2f}")
        self.entries["Estatus"].set(datos_vacante['Estatus'])
        
        ttk.Button(self, text="Guardar Cambios", command=self.guardar, style="Accent.TButton").pack(pady=15)

    def guardar(self):
        datos = {k: v.get() for k, v in self.entries.items()}
        if not all(datos.values()): messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self); return
            
        success, message = db_manager.actualizar_vacante_db(self.controller.conexion, self.id_vacante, datos["Cargo Vacante"], datos["Descripción"], datos["Salario Ofrecido"], datos["Estatus"])
        if success: 
            messagebox.showinfo("Éxito", message, parent=self)
            self.controller.nametowidget('.!app.!mainframe').show_mis_vacantes()
            self.destroy()
        else: 
            messagebox.showerror("Error al Guardar", message, parent=self)

# --- CLASES PRINCIPALES DE LA APP ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión Hiring Group"); self.geometry("900x650")
        self.minsize(800, 600)
        self.configure(bg=BG_COLOR)
        self.conexion = None; self.usuario_actual = None; self.rol_actual = None
        
        self.setup_styles()
        
        self.container = tk.Frame(self, bg=BG_COLOR)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1); self.container.grid_columnconfigure(0, weight=1)
        self.show_frame(LoginFrame)

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", background=BUTTON_BG, foreground=FG_COLOR, borderwidth=0, font=FONT_BOLD, padding=10)
        style.map("TButton", background=[("active", ACCENT_ACTIVE)], foreground=[("active", FG_COLOR)])
        style.configure("Accent.TButton", background=ACCENT_COLOR, foreground=FG_COLOR)
        style.map("Accent.TButton", background=[("active", ACCENT_ACTIVE)])
        style.configure("Treeview", background=ENTRY_BG, foreground=FG_COLOR, fieldbackground=ENTRY_BG, rowheight=25, font=FONT_NORMAL)
        style.map("Treeview", background=[("selected", ACCENT_COLOR)], foreground=[("selected", FG_COLOR)])
        style.configure("Treeview.Heading", background=BUTTON_BG, foreground=FG_COLOR, font=FONT_BOLD, relief="flat", padding=5)
        style.map("Treeview.Heading", background=[("active", BUTTON_BG)])
        style.configure("TCombobox", fieldbackground=ENTRY_BG, background=BUTTON_BG, foreground=FG_COLOR, arrowcolor=FG_COLOR, selectbackground=ENTRY_BG, selectforeground=FG_COLOR)
        self.option_add('*TCombobox*Listbox.background', ENTRY_BG)
        self.option_add('*TCombobox*Listbox.foreground', FG_COLOR)
        self.option_add('*TCombobox*Listbox.selectBackground', ACCENT_COLOR)
        self.option_add('*TCombobox*Listbox.font', FONT_NORMAL)

    def show_frame(self, FrameClass):
        for widget in self.container.winfo_children(): widget.destroy()
        frame = FrameClass(parent=self.container, controller=self)
        frame.grid(row=0, column=0, sticky="nsew")

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller
        
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        
        login_container = tk.Frame(self, bg=BG_COLOR)
        login_container.grid(row=0, column=0)
        
        tk.Label(login_container, text="Login del Sistema", font=("Segoe UI", 20, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=20)
        tk.Label(login_container, text="Email", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack()
        self.email_entry = tk.Entry(login_container, width=40, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, justify="center")
        self.email_entry.pack(pady=5, ipady=5)
        tk.Label(login_container, text="Contraseña", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack()
        self.pass_entry = tk.Entry(login_container, width=40, show="*", bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, justify="center")
        self.pass_entry.pack(pady=5, ipady=5)
        ttk.Button(login_container, text="Ingresar", command=self.attempt_login, style="Accent.TButton").pack(pady=20, ipady=5, ipadx=10)

    def attempt_login(self):
        if not self.controller.conexion or not self.controller.conexion.is_connected():
            password_db = simpledialog.askstring("Contraseña DB", "Introduce la contraseña de tu base de datos (MySQL):", show='*')
            if password_db is None: return
            self.controller.conexion = db_manager.conectar_db(password_db)
            if not self.controller.conexion: messagebox.showerror("Error de Conexión", "No se pudo conectar a la base de datos."); return
        
        usuario, rol = db_manager.login_usuario(self.controller.conexion, self.email_entry.get(), self.pass_entry.get())
        if usuario:
            self.controller.usuario_actual, self.controller.rol_actual = usuario, rol
            self.controller.show_frame(MainFrame)
        else:
            messagebox.showerror("Login Fallido", "Email o contraseña incorrectos.")

class MainFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        self.controller = controller
        menu_frame = tk.Frame(self, bg="#0F172A", width=220)
        menu_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10,0), pady=10)
        menu_frame.pack_propagate(False) 
        self.content_frame = tk.Frame(self, bg=BG_COLOR)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        rol = self.controller.rol_actual
        tk.Label(menu_frame, text=f"Menú - {rol}", font=FONT_MENU_TITLE, bg="#0F172A", fg=FG_COLOR).pack(pady=20)
        
        botones = {
            'HiringGroup': [
                ("Crear Usuario", lambda: self.open_form_window(CrearUsuarioWindow)),
                ("Gestionar Usuarios", self.show_gestionar_usuarios),
                ("Gestionar Profesiones", self.show_gestionar_profesiones),
                ("Contratar Postulante", self.show_contratar_form),
                ("Ejecutar Nómina", self.show_nomina_form)
            ],
            'Empresa': [
                ("Crear Vacante", lambda: self.open_form_window(CrearVacanteWindow)),
                ("Ver Mis Vacantes", self.show_mis_vacantes),
                ("Editar Mi Perfil", lambda: self.open_form_window(ActualizarUsuarioWindow))
            ],
            'Postulante': [
                ("Buscar Vacantes", self.show_buscar_vacantes),
                ("Mis Postulaciones", self.show_mis_postulaciones),
                ("Editar Mi Perfil", lambda: self.open_form_window(ActualizarUsuarioWindow))
            ],
            'Contratado': [
                ("Mis Recibos de Pago", self.show_recibos_pago),
                ("Generar Constancia", self.show_constancia),
                ("Editar Mi Perfil", lambda: self.open_form_window(ActualizarUsuarioWindow))
            ]
        }
        for texto, comando in botones.get(rol, []):
            ttk.Button(menu_frame, text=texto, command=comando).pack(fill=tk.X, pady=4, padx=10)
        
        ttk.Button(menu_frame, text="Salir (Logout)", command=self.logout, style="Accent.TButton").pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=10)
        self.show_welcome_message()

    def show_welcome_message(self):
        tk.Label(self.content_frame, text=f"Bienvenido/a, {self.controller.usuario_actual['Email']}", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w", pady=(0, 10))

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()

    def logout(self):
        self.controller.usuario_actual = None
        self.controller.rol_actual = None
        self.controller.show_frame(LoginFrame)

    def open_form_window(self, WindowClass, *args):
        WindowClass(self.controller, self.controller, *args)

    def crear_tabla(self, parent, cols, widths={}):
        tree = ttk.Treeview(parent, columns=cols, show='headings', style="Treeview")
        for col in cols:
            tree.heading(col, text=col); tree.column(col, width=widths.get(col, 120), anchor="w")
        return tree

    def show_gestionar_usuarios(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Gestionar Usuarios", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        
        usuarios = db_manager.get_all_users_for_admin(self.controller.conexion)
        if not usuarios:
            tk.Label(self.content_frame, text="No hay usuarios registrados (aparte de administradores).", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack()
            return
            
        tree = self.crear_tabla(self.content_frame, ('ID', 'Email', 'Tipo de Usuario'), widths={'ID': 50})
        for u in usuarios:
            tree.insert("", "end", values=(u['ID_Usuario'], u['Email'], u['Tipo_Usuario']))
        tree.pack(fill="both", expand=True, pady=5)
        
        def eliminar_usuario():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Selección Requerida", "Por favor, selecciona un usuario para eliminar.", parent=self.controller)
                return
            
            id_usuario = tree.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar al usuario con ID {id_usuario}?\n¡Esta acción es irreversible y podría afectar registros asociados!", parent=self.controller):
                success, msg = db_manager.eliminar_usuario_db(self.controller.conexion, id_usuario)
                messagebox.showinfo("Resultado", msg, parent=self.controller)
                if success: self.show_gestionar_usuarios()
        
        ttk.Button(self.content_frame, text="Eliminar Usuario Seleccionado", command=eliminar_usuario, style="Accent.TButton").pack(pady=10, anchor="e")

    def show_gestionar_profesiones(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Gestionar Profesiones", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        
        add_frame = tk.LabelFrame(self.content_frame, text="Agregar Nueva Profesión", bg=BG_COLOR, fg=FG_COLOR, padx=10, pady=10, font=FONT_BOLD)
        add_frame.pack(fill="x", pady=5)
        tk.Label(add_frame, text="Nombre:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(side=tk.LEFT, padx=5)
        new_profession_entry = tk.Entry(add_frame, width=40, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, insertbackground=FG_COLOR)
        new_profession_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True, ipady=4)
        
        tree_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        tree_frame.pack(fill="both", expand=True, pady=5)
        tree = self.crear_tabla(tree_frame, ('ID', 'Nombre de la Profesión'), widths={'ID': 50, 'Nombre de la Profesión': 600})
        
        def populate_tree():
            for i in tree.get_children(): tree.delete(i)
            profesiones = db_manager.get_profesiones(self.controller.conexion)
            if profesiones:
                for p in profesiones: tree.insert("", "end", values=(p['ID_Profesion'], p['Nombre_Profesion']))

        def add_new_profession():
            new_prof = new_profession_entry.get()
            if not new_prof: messagebox.showwarning("Campo Vacío", "Por favor, introduce un nombre."); return
            success, msg = db_manager.crear_profesion_db(self.controller.conexion, new_prof)
            messagebox.showinfo("Resultado", msg)
            if success: new_profession_entry.delete(0, tk.END); populate_tree()

        ttk.Button(add_frame, text="Agregar", command=add_new_profession).pack(side=tk.LEFT, padx=5)
        tree.pack(fill="both", expand=True)
        populate_tree()

        action_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        action_frame.pack(fill="x", pady=5, anchor="e")

        def editar_profesion():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Por favor, selecciona una profesión para editar.", parent=self.controller); return
            id_profesion, nombre_actual = tree.item(selected[0])['values']
            nuevo_nombre = simpledialog.askstring("Editar Profesión", "Introduce el nuevo nombre:", initialvalue=nombre_actual, parent=self.controller)
            if nuevo_nombre and nuevo_nombre.strip() and nuevo_nombre != nombre_actual:
                success, msg = db_manager.actualizar_profesion_db(self.controller.conexion, id_profesion, nuevo_nombre.strip())
                messagebox.showinfo("Resultado", msg, parent=self.controller)
                if success: populate_tree()

        def eliminar_profesion():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Por favor, selecciona una profesión para eliminar.", parent=self.controller); return
            id_profesion, nombre = tree.item(selected[0])['values']
            if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar la profesión '{nombre}'?\nEsto no funcionará si la profesión está en uso.", parent=self.controller):
                success, msg = db_manager.eliminar_profesion_db(self.controller.conexion, id_profesion)
                messagebox.showinfo("Resultado", msg, parent=self.controller)
                if success: populate_tree()

        ttk.Button(action_frame, text="Eliminar Profesión", command=eliminar_profesion, style="Accent.TButton").pack(side="right", padx=5)
        ttk.Button(action_frame, text="Editar Profesión", command=editar_profesion).pack(side="right")

    def show_contratar_form(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Contratar Postulante", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        postulaciones = db_manager.get_postulaciones_para_contratar(self.controller.conexion)
        if not postulaciones: tk.Label(self.content_frame, text="No hay postulaciones recibidas.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        
        tree = self.crear_tabla(self.content_frame, ('ID', 'Nombre', 'Cargo'));
        for p in postulaciones: tree.insert("", "end", values=(p['ID_Postulacion'], f"{p['Nombres']} {p['Apellidos']}", p['Cargo_Vacante']))
        tree.pack(fill="x", pady=5)
        
        form_frame = tk.Frame(self.content_frame, pady=10, bg=BG_COLOR)
        tk.Label(form_frame, text="Salario Mensual:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        salario_entry = tk.Entry(form_frame, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, insertbackground=FG_COLOR); salario_entry.grid(row=0, column=1, padx=5, pady=5, ipady=4)
        tk.Label(form_frame, text="Tipo Contrato:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=1, column=0, padx=5, pady=5, sticky='w')
        contrato_combo = ttk.Combobox(form_frame, values=['Un mes', 'Seis meses', 'Un año', 'Indefinido'], state="readonly", font=FONT_NORMAL); contrato_combo.grid(row=1, column=1, padx=5, pady=5)
        form_frame.pack(anchor="w")
        
        def contratar():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Por favor, selecciona una postulación."); return
            id_postulacion = tree.item(selected[0])['values'][0]
            salario, tipo = salario_entry.get(), contrato_combo.get()
            if not all([salario, tipo]): messagebox.showerror("Error", "Debes especificar el salario y el tipo de contrato."); return
            success, msg = db_manager.contratar_postulante_db(self.controller.conexion, id_postulacion, salario, tipo)
            messagebox.showinfo("Resultado", msg)
            if success: self.show_contratar_form()
            
        ttk.Button(self.content_frame, text="Contratar y Aceptar", command=contratar, style="Accent.TButton").pack(pady=10, anchor="w")

    def show_nomina_form(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Ejecutar Nómina Mensual", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        empresas = db_manager.get_empresas(self.controller.conexion)
        if not empresas: tk.Label(self.content_frame, text="No hay empresas registradas.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        
        form_frame = tk.Frame(self.content_frame, pady=10, bg=BG_COLOR)
        empresa_nombres = [e['Nombre_Empresa'] for e in empresas]
        tk.Label(form_frame, text="Empresa:", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        empresa_combo = ttk.Combobox(form_frame, values=empresa_nombres, state="readonly", width=30, font=FONT_NORMAL); empresa_combo.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Mes (1-12):", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=1, column=0, padx=5, pady=5, sticky='w')
        mes_entry = tk.Entry(form_frame, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, insertbackground=FG_COLOR); mes_entry.grid(row=1, column=1, padx=5, pady=5, ipady=4)
        tk.Label(form_frame, text="Año (YYYY):", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).grid(row=2, column=0, padx=5, pady=5, sticky='w')
        anio_entry = tk.Entry(form_frame, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, font=FONT_NORMAL, insertbackground=FG_COLOR); anio_entry.grid(row=2, column=1, padx=5, pady=5, ipady=4)
        form_frame.pack(anchor="w")
        
        def generar():
            nombre_empresa, mes, anio = empresa_combo.get(), mes_entry.get(), anio_entry.get()
            if not all([nombre_empresa, mes, anio]): messagebox.showerror("Error", "Todos los campos son obligatorios."); return
            id_empresa = next((e['ID_Empresa'] for e in empresas if e['Nombre_Empresa'] == nombre_empresa), None)
            success, msg = db_manager.ejecutar_nomina_db(self.controller.conexion, id_empresa, mes, anio)
            messagebox.showinfo("Resultado", msg)
        
        ttk.Button(self.content_frame, text="Generar Nómina", command=generar, style="Accent.TButton").pack(pady=10, anchor="w")

    def show_buscar_vacantes(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Vacantes Activas", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        vacantes = db_manager.get_active_vacantes(self.controller.conexion)
        if not vacantes: tk.Label(self.content_frame, text="No hay vacantes disponibles en este momento.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        
        tree = self.crear_tabla(self.content_frame, ('ID', 'Cargo', 'Empresa', 'Salario', 'Descripción'), widths={'ID': 40, 'Salario': 80, 'Descripción': 300})
        for v in vacantes: tree.insert("", "end", values=(v['ID_Vacante'], v['Cargo_Vacante'], v['Nombre_Empresa'], f"{float(v['Salario_Ofrecido']):.2f}", v['Descripcion_Perfil']))
        tree.pack(fill="both", expand=True, pady=5)
        
        def aplicar():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Por favor, selecciona una vacante para aplicar."); return
            id_vacante = tree.item(selected[0])['values'][0]
            success, msg = db_manager.aplicar_a_vacante_db(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'], id_vacante)
            messagebox.showinfo("Resultado de la Postulación", msg)
        
        ttk.Button(self.content_frame, text="Aplicar a Vacante Seleccionada", command=aplicar, style="Accent.TButton").pack(pady=10, anchor="e")

    def show_mis_vacantes(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Mis Vacantes Publicadas", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        vacantes = db_manager.get_vacantes_por_empresa(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if not vacantes: tk.Label(self.content_frame, text="No tienes vacantes publicadas.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return

        tree = self.crear_tabla(self.content_frame, ('ID', 'Cargo', 'Salario', 'Estatus'), widths={'ID': 50, 'Estatus': 80})
        for v in vacantes:
            salario = f"{float(v['Salario_Ofrecido']):.2f}" if v['Salario_Ofrecido'] else "N/A"
            tree.insert("", "end", values=(v['ID_Vacante'], v['Cargo_Vacante'], salario, v['Estatus']))
        tree.pack(fill="both", expand=True, pady=5)

        buttons_frame = tk.Frame(self.content_frame, bg=BG_COLOR)
        buttons_frame.pack(fill="x", pady=5, anchor="e")

        def editar_vacante():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Por favor, selecciona una vacante para editar.", parent=self.controller); return
            id_vacante = tree.item(selected[0])['values'][0]
            datos_vacante = next((v for v in vacantes if v['ID_Vacante'] == id_vacante), None)
            if datos_vacante: self.open_form_window(ActualizarVacanteWindow, datos_vacante)

        def eliminar_vacante():
            selected = tree.selection()
            if not selected: messagebox.showwarning("Selección Requerida", "Por favor, selecciona una vacante para eliminar.", parent=self.controller); return
            id_vacante, cargo = tree.item(selected[0])['values'][:2]
            if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar la vacante '{cargo}'?", parent=self.controller):
                success, msg = db_manager.eliminar_vacante_db(self.controller.conexion, id_vacante)
                messagebox.showinfo("Resultado", msg, parent=self.controller)
                if success: self.show_mis_vacantes()

        ttk.Button(buttons_frame, text="Eliminar Vacante", command=eliminar_vacante, style="Accent.TButton").pack(side="right", padx=5)
        ttk.Button(buttons_frame, text="Editar Vacante", command=editar_vacante).pack(side="right")

    def show_mis_postulaciones(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Mis Postulaciones Realizadas", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        postulaciones = db_manager.get_postulaciones_por_postulante(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if not postulaciones: tk.Label(self.content_frame, text="No has realizado ninguna postulación.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        
        tree = self.crear_tabla(self.content_frame, ('Cargo', 'Empresa', 'Salario', 'Fecha', 'Estatus'))
        for p in postulaciones: 
            salario = f"{float(p['Salario_Ofrecido']):.2f}" if p['Salario_Ofrecido'] else "N/A"
            fecha = p['Fecha_Postulacion'].strftime('%Y-%m-%d') if p['Fecha_Postulacion'] else 'N/A'
            tree.insert("", "end", values=(p['Cargo_Vacante'], p['Nombre_Empresa'], salario, fecha, p['Estatus']))
        tree.pack(fill="both", expand=True, pady=5)
        
    def show_recibos_pago(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Mis Recibos de Pago", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        recibos = db_manager.get_recibos_por_contratado(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if not recibos: tk.Label(self.content_frame, text="No se han generado recibos de pago.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack(); return
        
        tree = self.crear_tabla(self.content_frame, ('Periodo', 'Fecha Pago', 'Salario Base', 'Salario Neto'))
        for r in recibos: 
            base = f"{float(r['Salario_Base']):.2f}" if r['Salario_Base'] else "N/A"
            neto = f"{float(r['Salario_Neto_Pagado']):.2f}" if r['Salario_Neto_Pagado'] else "N/A"
            tree.insert("", "end", values=(f"{r['Mes']}/{r['Anio']}", r['Fecha_Pago'], base, neto))
        tree.pack(fill="both", expand=True, pady=5)
        
    def show_constancia(self):
        self.clear_content_frame()
        self.show_welcome_message()
        tk.Label(self.content_frame, text="Constancia de Trabajo", font=FONT_TITLE, bg=BG_COLOR, fg=FG_COLOR).pack(pady=10, anchor="w")
        texto_constancia = db_manager.get_datos_constancia(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if texto_constancia:
            text_widget = tk.Text(self.content_frame, height=15, width=80, font=("Courier", 11), wrap="word", bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, bd=0, padx=10, pady=10)
            text_widget.insert(tk.END, texto_constancia)
            text_widget.config(state="disabled")
            text_widget.pack(pady=10, fill="x")
        else:
            tk.Label(self.content_frame, text="No se pudo generar la constancia. No se encontró un contrato activo.", bg=BG_COLOR, fg=FG_COLOR, font=FONT_NORMAL).pack()

if __name__ == "__main__":
    app = App()
    # Asignar un nombre al widget raíz para poder encontrarlo después
    app.nametowidget('.')._name = 'app'
    app.mainloop()