import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import db_manager

# --- CLASES DE VENTANAS DE FORMULARIO (TOPLEVEL) ---
class FormularioBase(tk.Toplevel):
    def __init__(self, parent, controller, title):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.controller = controller
        self.entries = {}

    def crear_campo(self, frame, texto):
        row = tk.Frame(frame)
        label = tk.Label(row, width=15, text=f"{texto}:", anchor='w')
        entry = tk.Entry(row, width=40)
        if "Contraseña" in texto:
            entry.config(show="*")
        row.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)
        label.pack(side=tk.LEFT)
        entry.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        self.entries[texto] = entry

class CrearUsuarioWindow(FormularioBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Crear Nuevo Usuario")
        self.campos_especificos = {
            "Postulante": ["Nombres", "Apellidos", "Cédula", "Teléfono"],
            "Empresa": ["Nombre Empresa", "RIF", "Sector"],
            "HiringGroup": []
        }
        
        top_frame = tk.Frame(self)
        tk.Label(top_frame, text="Tipo de Usuario:").pack(side=tk.LEFT, padx=5)
        self.tipo_usuario_combo = ttk.Combobox(top_frame, values=list(self.campos_especificos.keys()), state="readonly")
        self.tipo_usuario_combo.pack(side=tk.LEFT, padx=5, pady=10)
        self.tipo_usuario_combo.bind("<<ComboboxSelected>>", self.actualizar_campos)
        top_frame.pack()
        
        self.form_frame = tk.Frame(self)
        self.form_frame.pack(pady=10)
        tk.Button(self, text="Crear Usuario", command=self.crear).pack(pady=15)
        self.actualizar_campos(None)

    def actualizar_campos(self, event):
        for widget in self.form_frame.winfo_children(): widget.destroy()
        self.entries = {}
        for field in ["Email", "Contraseña"]: self.crear_campo(self.form_frame, field)
        for field in self.campos_especificos.get(self.tipo_usuario_combo.get(), []): self.crear_campo(self.form_frame, field)

    def crear(self):
        tipo_usuario = self.tipo_usuario_combo.get()
        if not tipo_usuario:
            messagebox.showerror("Error", "Debes seleccionar un tipo de usuario.", parent=self)
            return
        datos = {k: v.get() for k, v in self.entries.items()}
        if not all(datos.values()):
            messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self)
            return
        success, message = db_manager.registrar_usuario_db(self.controller.conexion, tipo_usuario, datos)
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error al Crear", message, parent=self)

class CrearVacanteWindow(FormularioBase):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Crear Nueva Vacante")
        self.profesiones = db_manager.get_profesiones(self.controller.conexion)
        profesiones_nombres = [p['Nombre_Profesion'] for p in self.profesiones] if self.profesiones else []
        if not profesiones_nombres:
            messagebox.showwarning("Advertencia", "No hay profesiones registradas en el sistema. Por favor, pida a un usuario de Hiring Group que las agregue.", parent=self)

        frame = tk.Frame(self)
        for field in ["Cargo Vacante", "Descripción", "Salario Ofrecido"]: self.crear_campo(frame, field)
        
        row = tk.Frame(frame)
        tk.Label(row, width=15, text="Profesión:", anchor='w').pack(side=tk.LEFT)
        self.profesion_combo = ttk.Combobox(row, values=profesiones_nombres, state="readonly", width=37)
        self.profesion_combo.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        row.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)
        frame.pack(pady=10)
        tk.Button(self, text="Guardar Vacante", command=self.guardar).pack(pady=15)

    def guardar(self):
        vals = {k: v.get() for k, v in self.entries.items()}
        selected_profesion_name = self.profesion_combo.get()
        if not all(vals.values()) or not selected_profesion_name:
            messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self)
            return
        
        id_profesion = next((p['ID_Profesion'] for p in self.profesiones if p['Nombre_Profesion'] == selected_profesion_name), None)
        id_empresa = self.controller.usuario_actual['ID_Usuario']
        success, message = db_manager.crear_vacante_db(self.controller.conexion, id_empresa, vals["Cargo Vacante"], vals["Descripción"], vals["Salario Ofrecido"], id_profesion)
        if success:
            messagebox.showinfo("Éxito", message, parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error al Guardar", message, parent=self)


# --- CLASES PRINCIPALES DE LA APP ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión Hiring Group")
        self.geometry("850x600")
        self.conexion = None
        self.usuario_actual = None
        self.rol_actual = None
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.show_frame(LoginFrame)

    def show_frame(self, FrameClass):
        for widget in self.container.winfo_children(): widget.destroy()
        frame = FrameClass(parent=self.container, controller=self)
        frame.grid(row=0, column=0, sticky="nsew")

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Login del Sistema", font=("Helvetica", 16)).pack(pady=20)
        tk.Label(self, text="Email").pack()
        self.email_entry = tk.Entry(self, width=30)
        self.email_entry.pack(pady=5)
        tk.Label(self, text="Contraseña").pack()
        self.pass_entry = tk.Entry(self, width=30, show="*")
        self.pass_entry.pack(pady=5)
        tk.Button(self, text="Ingresar", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        if not self.controller.conexion or not self.controller.conexion.is_connected():
            password_db = simpledialog.askstring("Contraseña DB", "Introduce la contraseña de tu base de datos (MySQL):", show='*')
            self.controller.conexion = db_manager.conectar_db(password_db if password_db is not None else "")
            
            if not self.controller.conexion:
                messagebox.showerror("Error de Conexión", "No se pudo conectar a la base de datos.")
                return
        
        usuario, rol = db_manager.login_usuario(self.controller.conexion, self.email_entry.get(), self.pass_entry.get())
        
        if usuario:
            self.controller.usuario_actual, self.controller.rol_actual = usuario, rol
            self.controller.show_frame(MainFrame)
        else:
            messagebox.showerror("Login Fallido", "Email o contraseña incorrectos.")

class MainFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        menu_frame = tk.Frame(self, relief=tk.RAISED, bd=2, width=200)
        menu_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        menu_frame.pack_propagate(False) 
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        rol = self.controller.rol_actual
        tk.Label(menu_frame, text=f"Menú - {rol}", font=("Helvetica", 12, "bold")).pack(pady=10)
        
        botones = {
            'HiringGroup': [
                ("Crear Usuario", lambda: self.open_form_window(CrearUsuarioWindow)), 
                ("Gestionar Profesiones", self.show_gestionar_profesiones), # <-- NUEVO BOTÓN
                ("Contratar Postulante", self.show_contratar_form), 
                ("Ejecutar Nómina", self.show_nomina_form)
            ],
            'Empresa': [
                ("Crear Vacante", lambda: self.open_form_window(CrearVacanteWindow)), 
                ("Ver Mis Vacantes", self.show_mis_vacantes)
            ],
            'Postulante': [
                ("Buscar Vacantes", self.show_buscar_vacantes), 
                ("Mis Postulaciones", self.show_mis_postulaciones)
            ],
            'Contratado': [
                ("Mis Recibos de Pago", self.show_recibos_pago), 
                ("Generar Constancia", self.show_constancia)
            ]
        }
        for texto, comando in botones.get(rol, []):
            tk.Button(menu_frame, text=texto, command=comando).pack(fill=tk.X, pady=5, padx=5)
        
        tk.Button(menu_frame, text="Salir (Logout)", command=self.logout).pack(side=tk.BOTTOM, fill=tk.X, pady=20, padx=5)
        tk.Label(self.content_frame, text=f"Bienvenido/a, {self.controller.usuario_actual['Email']}", font=("Helvetica", 14)).pack(anchor="w")

    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()

    def logout(self):
        try:
            if self.controller.conexion and self.controller.conexion.is_connected(): 
                self.controller.conexion.close()
        except:
            pass
        self.controller.conexion = None
        self.controller.show_frame(LoginFrame)

    def open_form_window(self, WindowClass): WindowClass(self, self.controller)

    # --- NUEVA VISTA PARA GESTIONAR PROFESIONES ---
    def show_gestionar_profesiones(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Gestionar Profesiones", font=("Helvetica", 14)).pack(pady=10, anchor="w")

        # --- Frame para agregar nueva profesión ---
        add_frame = tk.LabelFrame(self.content_frame, text="Agregar Nueva Profesión", padx=10, pady=10)
        add_frame.pack(fill="x", pady=10)
        
        tk.Label(add_frame, text="Nombre:").pack(side=tk.LEFT, padx=5)
        new_profession_entry = tk.Entry(add_frame, width=40)
        new_profession_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

        # --- Frame para la lista de profesiones existentes ---
        list_frame = tk.Frame(self.content_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        tk.Label(list_frame, text="Profesiones Existentes:").pack(anchor="w")
        tree = self.crear_tabla(list_frame, ('ID', 'Nombre de la Profesión'), widths={'ID': 50})
        
        def populate_tree():
            for i in tree.get_children():
                tree.delete(i)
            profesiones = db_manager.get_profesiones(self.controller.conexion)
            if profesiones:
                for p in profesiones:
                    tree.insert("", "end", values=(p['ID_Profesion'], p['Nombre_Profesion']))
        
        def add_new_profession():
            new_prof = new_profession_entry.get()
            if not new_prof:
                messagebox.showwarning("Campo Vacío", "Por favor, introduce un nombre para la profesión.")
                return
            success, msg = db_manager.crear_profesion_db(self.controller.conexion, new_prof)
            messagebox.showinfo("Resultado", msg)
            if success:
                new_profession_entry.delete(0, tk.END)
                populate_tree()

        tk.Button(add_frame, text="Agregar", command=add_new_profession).pack(side=tk.LEFT, padx=5)
        tree.pack(fill="both", expand=True)
        populate_tree()

    # --- EL RESTO DE LAS FUNCIONES DE LA CLASE MainFrame ---
    def show_contratar_form(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Contratar Postulante (Postulaciones Recibidas)", font=("Helvetica", 14)).pack(pady=10, anchor="w")
        postulaciones = db_manager.get_postulaciones_para_contratar(self.controller.conexion)
        if not postulaciones:
            tk.Label(self.content_frame, text="No hay postulaciones recibidas pendientes de contratación.").pack()
            return
        
        tree = self.crear_tabla(self.content_frame, ('ID', 'Nombre', 'Cargo'))
        for p in postulaciones: tree.insert("", "end", values=(p['ID_Postulacion'], f"{p['Nombres']} {p['Apellidos']}", p['Cargo_Vacante']))
        tree.pack(fill="x", pady=5)
        
        form_frame = tk.Frame(self.content_frame, pady=10)
        tk.Label(form_frame, text="Salario Mensual:").grid(row=0, column=0, padx=5, pady=5)
        salario_entry = tk.Entry(form_frame)
        salario_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Tipo Contrato:").grid(row=1, column=0, padx=5, pady=5)
        contrato_combo = ttk.Combobox(form_frame, values=['Un mes', 'Seis meses', 'Un año', 'Indefinido'], state="readonly")
        contrato_combo.grid(row=1, column=1, padx=5, pady=5)
        form_frame.pack(anchor="w")

        def contratar():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Selección Requerida", "Por favor, selecciona una postulación de la lista.")
                return
            id_postulacion, salario, tipo = tree.item(selected[0])['values'][0], salario_entry.get(), contrato_combo.get()
            if not all([salario, tipo]):
                messagebox.showerror("Error", "Debes especificar el salario y el tipo de contrato.")
                return
            success, msg = db_manager.contratar_postulante_db(self.controller.conexion, id_postulacion, salario, tipo)
            messagebox.showinfo("Resultado", msg)
            if success: self.show_contratar_form()

        tk.Button(self.content_frame, text="Contratar y Aceptar Postulación", command=contratar).pack(pady=10, anchor="w")

    def show_nomina_form(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Ejecutar Nómina Mensual", font=("Helvetica", 14)).pack(pady=10, anchor="w")
        empresas = db_manager.get_empresas(self.controller.conexion)
        if not empresas:
            tk.Label(self.content_frame, text="No hay empresas registradas.").pack()
            return
        
        form_frame = tk.Frame(self.content_frame, pady=10)
        empresa_nombres = [e['Nombre_Empresa'] for e in empresas]
        tk.Label(form_frame, text="Empresa:").grid(row=0, column=0, padx=5, pady=5)
        empresa_combo = ttk.Combobox(form_frame, values=empresa_nombres, state="readonly", width=30)
        empresa_combo.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Mes (1-12):").grid(row=1, column=0, padx=5, pady=5)
        mes_entry = tk.Entry(form_frame)
        mes_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(form_frame, text="Año (YYYY):").grid(row=2, column=0, padx=5, pady=5)
        anio_entry = tk.Entry(form_frame)
        anio_entry.grid(row=2, column=1, padx=5, pady=5)
        form_frame.pack(anchor="w")

        def generar():
            nombre_empresa, mes, anio = empresa_combo.get(), mes_entry.get(), anio_entry.get()
            if not all([nombre_empresa, mes, anio]):
                messagebox.showerror("Error", "Todos los campos son obligatorios.")
                return
            id_empresa = next((e['ID_Empresa'] for e in empresas if e['Nombre_Empresa'] == nombre_empresa), None)
            success, msg = db_manager.ejecutar_nomina_db(self.controller.conexion, id_empresa, mes, anio)
            messagebox.showinfo("Resultado", msg)

        tk.Button(self.content_frame, text="Generar Nómina", command=generar).pack(pady=10, anchor="w")

    def show_buscar_vacantes(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Vacantes Activas", font=("Helvetica", 14)).pack(pady=10, anchor="w")
        vacantes = db_manager.get_active_vacantes(self.controller.conexion)
        if not vacantes:
            tk.Label(self.content_frame, text="No hay vacantes disponibles en este momento.").pack()
            return
        
        tree = self.crear_tabla(self.content_frame, ('ID', 'Cargo', 'Empresa', 'Salario', 'Descripción'), widths={'ID': 40, 'Salario': 80})
        for v in vacantes: tree.insert("", "end", values=(v['ID_Vacante'], v['Cargo_Vacante'], v['Nombre_Empresa'], f"{v['Salario_Ofrecido']:.2f}", v['Descripcion_Perfil']))
        tree.pack(fill="both", expand=True, pady=5)

        def aplicar():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Selección Requerida", "Por favor, selecciona una vacante de la lista para aplicar.")
                return
            id_vacante, id_postulante = tree.item(selected[0])['values'][0], self.controller.usuario_actual['ID_Usuario']
            success, msg = db_manager.aplicar_a_vacante_db(self.controller.conexion, id_postulante, id_vacante)
            messagebox.showinfo("Resultado de la Postulación", msg)

        tk.Button(self.content_frame, text="Aplicar a Vacante Seleccionada", command=aplicar).pack(pady=10, anchor="e")
    
    def show_mis_vacantes(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Mis Vacantes Publicadas", font=("Helvetica", 14)).pack(pady=10, anchor="w")
        vacantes = db_manager.get_vacantes_por_empresa(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if not vacantes:
            tk.Label(self.content_frame, text="No tienes vacantes publicadas.").pack()
            return
        tree = self.crear_tabla(self.content_frame, ('ID', 'Cargo', 'Salario', 'Estatus'))
        for vacante in vacantes: tree.insert("", "end", values=(vacante['ID_Vacante'], vacante['Cargo_Vacante'], f"{vacante['Salario_Ofrecido']:.2f}", vacante['Estatus']))
        tree.pack(fill="both", expand=True, pady=5)
    
    def show_mis_postulaciones(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Mis Postulaciones Realizadas", font=("Helvetica", 14)).pack(pady=10, anchor="w")
        postulaciones = db_manager.get_postulaciones_por_postulante(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if not postulaciones:
            tk.Label(self.content_frame, text="No has realizado ninguna postulación.").pack()
            return
        tree = self.crear_tabla(self.content_frame, ('Cargo', 'Empresa', 'Salario', 'Fecha', 'Estatus'))
        for p in postulaciones: tree.insert("", "end", values=(p['Cargo_Vacante'], p['Nombre_Empresa'], f"{p['Salario_Ofrecido']:.2f}", p['Fecha_Postulacion'].strftime('%Y-%m-%d'), p['Estatus']))
        tree.pack(fill="both", expand=True, pady=5)
        
    def show_recibos_pago(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Mis Recibos de Pago", font=("Helvetica", 14)).pack(pady=10, anchor="w")
        recibos = db_manager.get_recibos_por_contratado(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if not recibos:
            tk.Label(self.content_frame, text="No se han generado recibos de pago.").pack()
            return
        tree = self.crear_tabla(self.content_frame, ('Periodo', 'Fecha Pago', 'Salario Base', 'Salario Neto'))
        for r in recibos: tree.insert("", "end", values=(f"{r['Mes']}/{r['Anio']}", r['Fecha_Pago'], f"{r['Salario_Base']:.2f}", f"{r['Salario_Neto_Pagado']:.2f}"))
        tree.pack(fill="both", expand=True, pady=5)
        
    def show_constancia(self):
        self.clear_content_frame()
        tk.Label(self.content_frame, text="Constancia de Trabajo", font=("Helvetica", 14)).pack(pady=10, anchor="w")
        texto_constancia = db_manager.get_datos_constancia(self.controller.conexion, self.controller.usuario_actual['ID_Usuario'])
        if texto_constancia:
            text_widget = tk.Text(self.content_frame, height=15, width=80, font=("Courier", 10), wrap="word")
            text_widget.insert(tk.END, texto_constancia)
            text_widget.config(state="disabled")
            text_widget.pack(pady=10, fill="x")
        else:
            tk.Label(self.content_frame, text="No se pudo generar la constancia. No se encontró un contrato activo.").pack()
    
    def crear_tabla(self, parent, cols, widths={}):
        tree = ttk.Treeview(parent, columns=cols, show='headings')
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 100))
        return tree

if __name__ == "__main__":
    app = App()
    app.mainloop()