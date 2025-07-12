import mysql.connector
from mysql.connector import Error
from datetime import datetime

# --- FUNCIONES DE CONEXIÓN Y LOGIN ---
def conectar_db(password):
    try:
        conexion = mysql.connector.connect(
            host='localhost', user='root', password=password, database='hiring_group'
        )
        return conexion
    except Error:
        return None

def login_usuario(conexion, email, password):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT ID_Usuario, Email, Tipo_Usuario FROM Usuarios WHERE Email = %s AND Password = %s"
    cursor.execute(query, (email, password))
    usuario = cursor.fetchone()
    if not usuario:
        cursor.close()
        return None, None
    if usuario['Tipo_Usuario'] == 'Postulante':
        query_contrato = "SELECT c.ID_Contrato FROM Contratos c JOIN Postulaciones p ON c.ID_Postulacion = p.ID_Postulacion WHERE p.ID_Postulante = %s AND c.Estatus = 'Activo'"
        cursor.execute(query_contrato, (usuario['ID_Usuario'],))
        if cursor.fetchone():
            usuario['Tipo_Usuario'] = 'Contratado'
    cursor.close()
    return usuario, usuario['Tipo_Usuario']

# --- FUNCIONES DE CREACIÓN (CRUD) ---
def registrar_usuario_db(conexion, tipo_usuario, datos):
    cursor = conexion.cursor()
    email, password = datos.get("Email"), datos.get("Contraseña")
    try:
        conexion.start_transaction()
        sql_usuario = "INSERT INTO Usuarios (Email, Password, Tipo_Usuario) VALUES (%s, %s, %s)"
        cursor.execute(sql_usuario, (email, password, tipo_usuario))
        id_usuario = cursor.lastrowid
        
        if tipo_usuario == 'Empresa':
            sql_especifico = "INSERT INTO Empresas (ID_Empresa, Nombre_Empresa, RIF, Sector_Industrial) VALUES (%s, %s, %s, %s)"
            valores = (id_usuario, datos.get("Nombre Empresa"), datos.get("RIF"), datos.get("Sector"))
            cursor.execute(sql_especifico, valores)
        elif tipo_usuario == 'Postulante':
            sql_especifico = "INSERT INTO Postulantes (ID_Postulante, Nombres, Apellidos, Cedula_Identidad, Telefono) VALUES (%s, %s, %s, %s, %s)"
            valores = (id_usuario, datos.get("Nombres"), datos.get("Apellidos"), datos.get("Cédula"), datos.get("Teléfono"))
            cursor.execute(sql_especifico, valores)
        
        conexion.commit()
        return True, f"Usuario tipo '{tipo_usuario}' creado con éxito."
    except mysql.connector.IntegrityError as e:
        conexion.rollback()
        return False, f"Error de integridad: El Email, RIF o Cédula ya existen. ({e})"
    except Error as e:
        conexion.rollback()
        return False, f"Error inesperado al crear usuario: {e}"
    finally:
        cursor.close()

def crear_vacante_db(conexion, id_empresa, cargo, descripcion, salario, id_profesion):
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO Vacantes (ID_Empresa, Cargo_Vacante, Descripcion_Perfil, Salario_Ofrecido, ID_Profesion) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (id_empresa, cargo, descripcion, salario, id_profesion))
        conexion.commit()
        return True, "Vacante creada con éxito."
    except Error as e:
        return False, f"Error al crear vacante: {e}"
    finally:
        cursor.close()

def crear_profesion_db(conexion, nombre_profesion):
    """Inserta una nueva profesión en la base de datos."""
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO Profesiones (Nombre_Profesion) VALUES (%s)"
        cursor.execute(sql, (nombre_profesion,))
        conexion.commit()
        return True, "Profesión agregada con éxito."
    except mysql.connector.IntegrityError:
        # Esto funcionaría si Nombre_Profesion fuera UNIQUE. Es buena práctica tenerlo.
        return False, "Error: Esa profesión ya podría existir."
    except Error as e:
        return False, f"Error inesperado al agregar la profesión: {e}"
    finally:
        cursor.close()

def contratar_postulante_db(conexion, id_postulacion, salario, tipo_contrato):
    cursor = conexion.cursor(dictionary=True)
    try:
        conexion.start_transaction()
        sql_contrato = "INSERT INTO Contratos (ID_Postulacion, Fecha_Contratacion, Tipo_Contrato, Salario_Acordado) VALUES (%s, CURDATE(), %s, %s)"
        cursor.execute(sql_contrato, (id_postulacion, tipo_contrato, salario))
        cursor.execute("SELECT ID_Vacante FROM Postulaciones WHERE ID_Postulacion = %s", (id_postulacion,))
        id_vacante = cursor.fetchone()['ID_Vacante']
        cursor.execute("UPDATE Vacantes SET Estatus = 'Cerrada' WHERE ID_Vacante = %s", (id_vacante,))
        cursor.execute("UPDATE Postulaciones SET Estatus = 'Aceptada' WHERE ID_Postulacion = %s", (id_postulacion,))
        conexion.commit()
        return True, "Contratación exitosa."
    except Error as e:
        conexion.rollback()
        return False, f"Error al contratar: {e}"
    finally:
        cursor.close()


def aplicar_a_vacante_db(conexion, id_postulante, id_vacante):
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO Postulaciones (ID_Postulante, ID_Vacante, Estatus) VALUES (%s, %s, 'Recibida')"
        cursor.execute(sql, (id_postulante, id_vacante))
        conexion.commit()
        return True, "¡Postulación exitosa!"
    except mysql.connector.IntegrityError:
        return False, "Error: Ya te has postulado a esta vacante."
    except Error as e:
        return False, f"Error inesperado: {e}"
    finally:
        cursor.close()

def ejecutar_nomina_db(conexion, id_empresa, mes, anio):
    cursor = conexion.cursor(dictionary=True)
    try:
        conexion.start_transaction()
        sql_nomina = "INSERT INTO Nominas (ID_Empresa, Mes, Anio) VALUES (%s, %s, %s)"
        cursor.execute(sql_nomina, (id_empresa, mes, anio))
        id_nomina = cursor.lastrowid
        sql_contratos = "SELECT c.ID_Contrato, c.Salario_Acordado FROM Contratos c JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante WHERE v.ID_Empresa = %s AND c.Estatus = 'Activo'"
        cursor.execute(sql_contratos, (id_empresa,))
        contratos = cursor.fetchall()
        if not contratos:
            conexion.rollback()
            return False, "No hay empleados activos para esta empresa."
        for contrato in contratos:
            salario = contrato['Salario_Acordado']
            ded_ivss, ded_inces = float(salario) * 0.01, float(salario) * 0.005
            comision, neto = float(salario) * 0.02, float(salario) - ded_ivss - ded_inces
            sql_recibo = "INSERT INTO Recibos (ID_Nomina, ID_Contrato, Salario_Base, Monto_Deduccion_INCES, Monto_Deduccion_IVSS, Comision_Hiring_Group, Salario_Neto_Pagado, Fecha_Pago) VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE())"
            cursor.execute(sql_recibo, (id_nomina, contrato['ID_Contrato'], salario, ded_inces, ded_ivss, comision, neto))
        conexion.commit()
        return True, f"Nómina generada con éxito para {len(contratos)} empleado(s)."
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return False, "Ya se generó una nómina para esta empresa en este periodo."
    except Error as e:
        conexion.rollback()
        return False, f"Error al generar nómina: {e}"
    finally:
        cursor.close()

# --- FUNCIONES DE CONSULTA (GETTERS) ---
def get_active_vacantes(conexion):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT v.ID_Vacante, v.Cargo_Vacante, v.Descripcion_Perfil, v.Salario_Ofrecido, e.Nombre_Empresa FROM Vacantes v JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa WHERE v.Estatus = 'Activa'"
    cursor.execute(query)
    return cursor.fetchall()

def get_postulaciones_para_contratar(conexion):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT post.ID_Postulacion, p.Nombres, p.Apellidos, v.Cargo_Vacante FROM Postulaciones post JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante WHERE post.Estatus = 'Recibida'"
    cursor.execute(query)
    return cursor.fetchall()

def get_vacantes_por_empresa(conexion, id_empresa):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT ID_Vacante, Cargo_Vacante, Salario_Ofrecido, Estatus FROM Vacantes WHERE ID_Empresa = %s"
    cursor.execute(query, (id_empresa,))
    return cursor.fetchall()

def get_postulaciones_por_postulante(conexion, id_postulante):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT v.Cargo_Vacante, v.Salario_Ofrecido, e.Nombre_Empresa, p.Fecha_Postulacion, p.Estatus FROM Postulaciones p JOIN Vacantes v ON p.ID_Vacante = v.ID_Vacante JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa WHERE p.ID_Postulante = %s ORDER BY p.Fecha_Postulacion DESC"
    cursor.execute(query, (id_postulante,))
    return cursor.fetchall()

def get_recibos_por_contratado(conexion, id_postulante):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT r.Fecha_Pago, r.Salario_Base, r.Salario_Neto_Pagado, n.Mes, n.Anio FROM Recibos r JOIN Nominas n ON r.ID_Nomina = n.ID_Nomina JOIN Contratos c ON r.ID_Contrato = c.ID_Contrato JOIN Postulaciones p ON c.ID_Postulacion = p.ID_Postulacion WHERE p.ID_Postulante = %s ORDER BY n.Anio DESC, n.Mes DESC"
    cursor.execute(query, (id_postulante,))
    return cursor.fetchall()

def get_datos_constancia(conexion, id_postulante):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT p.Nombres, p.Apellidos, c.Fecha_Contratacion, c.Salario_Acordado, v.Cargo_Vacante, e.Nombre_Empresa FROM Contratos c JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa WHERE p.ID_Postulante = %s AND c.Estatus = 'Activo'"
    cursor.execute(query, (id_postulante,))
    datos = cursor.fetchone()
    if not datos: return None
    meses_es = (
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    )
    
    fecha_contrato = datos['Fecha_Contratacion']
    fecha_hoy = datetime.now()

    fecha_inicio_str = f"{fecha_contrato.day} de {meses_es[fecha_contrato.month - 1]} de {fecha_contrato.year}"
    fecha_actual_str = f"{fecha_hoy.day} de {meses_es[fecha_hoy.month - 1]} de {fecha_hoy.year}"
    nombre_completo = f"{datos['Nombres']} {datos['Apellidos']}"
    salario_str = f"{datos['Salario_Acordado']:.2f}"
    
    constancia = f"                 A QUIEN PUEDA INTERESAR\n\nPor medio de la presente la empresa HIRING GROUP hace constar que el ciudadano(a)\n{nombre_completo}, labora con nosotros desde {fecha_inicio_str}, cumpliendo\nfunciones en el cargo de {datos['Cargo_Vacante']} en la empresa {datos['Nombre_Empresa']}, devengando un\nsalario mensual de {salario_str}.\n\nConstancia que se pide por la parte interesada en la ciudad de Puerto Ordaz en fecha\n{fecha_actual_str}"
    return constancia

def get_empresas(conexion):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT ID_Empresa, Nombre_Empresa FROM Empresas ORDER BY Nombre_Empresa")
    return cursor.fetchall()

def get_profesiones(conexion):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT ID_Profesion, Nombre_Profesion FROM Profesiones ORDER BY Nombre_Profesion")
    return cursor.fetchall()
