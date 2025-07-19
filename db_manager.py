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
    query = "SELECT ID_Usuario, Email, Tipo_Usuario, Estatus FROM Usuarios WHERE Email = %s AND Password = %s"
    cursor.execute(query, (email, password))
    usuario = cursor.fetchone()

    if not usuario or usuario['Estatus'] != 'Activo':
        cursor.close()
        return None, None
    
    if usuario['Tipo_Usuario'] == 'Postulante':
        query_contrato = "SELECT c.ID_Contrato FROM Contratos c JOIN Postulaciones p ON c.ID_Postulacion = p.ID_Postulacion WHERE p.ID_Postulante = %s AND c.Estatus = 'Activo'"
        cursor.execute(query_contrato, (usuario['ID_Usuario'],))
        if cursor.fetchone():
            usuario['Tipo_Usuario'] = 'Contratado'
            
    cursor.close()
    return usuario, usuario['Tipo_Usuario']

# --- FUNCIONES GENÉRICAS DE CRUD PARA CATÁLOGOS ---
def get_catalogo(conexion, tabla, id_col, nombre_col):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(f"SELECT {id_col}, {nombre_col} FROM {tabla} ORDER BY {nombre_col}")
    return cursor.fetchall()

def crear_item_catalogo(conexion, tabla, nombre_col, nombre_valor):
    cursor = conexion.cursor()
    try:
        cursor.execute(f"INSERT INTO {tabla} ({nombre_col}) VALUES (%s)", (nombre_valor,))
        conexion.commit()
        return True, "Elemento agregado con éxito."
    except mysql.connector.IntegrityError: return False, f"Error: Ese valor ya existe en {tabla}."
    except Error as e: return False, f"Error inesperado: {e}"
    finally: cursor.close()

def actualizar_item_catalogo(conexion, tabla, id_col, nombre_col, id_valor, nuevo_nombre):
    cursor = conexion.cursor()
    try:
        cursor.execute(f"UPDATE {tabla} SET {nombre_col} = %s WHERE {id_col} = %s", (nuevo_nombre, id_valor))
        conexion.commit()
        return True, "Elemento actualizado con éxito."
    except Error as e: return False, f"Error al actualizar: {e}"
    finally: cursor.close()

def eliminar_item_catalogo(conexion, tabla, id_col, id_valor):
    cursor = conexion.cursor()
    try:
        cursor.execute(f"DELETE FROM {tabla} WHERE {id_col} = %s", (id_valor,))
        conexion.commit()
        return True, "Elemento eliminado con éxito."
    except mysql.connector.IntegrityError: return False, "Error: El elemento está en uso y no se puede eliminar."
    except Error as e: return False, f"Error inesperado: {e}"
    finally: cursor.close()

# --- FUNCIONES DE CREACIÓN (CRUD - CREATE) ---
def registrar_usuario_db(conexion, tipo_usuario, datos):
    cursor = conexion.cursor()
    try:
        conexion.start_transaction()
        sql_usuario = "INSERT INTO Usuarios (Email, Password, Tipo_Usuario) VALUES (%s, %s, %s)"
        cursor.execute(sql_usuario, (datos["Email"], datos["Contraseña"], tipo_usuario))
        id_usuario = cursor.lastrowid
        
        if tipo_usuario == 'Empresa':
            sql_empresa = "INSERT INTO Empresas (ID_Empresa, Nombre_Empresa, RIF, Sector_Industrial, Persona_Contacto, Telefono_Contacto, Email_Contacto) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            valores = (id_usuario, datos["Nombre Empresa"], datos["RIF"], datos["Sector"], datos["Persona de Contacto"], datos["Teléfono de Contacto"], datos["Email de Contacto"])
            cursor.execute(sql_empresa, valores)
        elif tipo_usuario == 'Postulante':
            sql_postulante = "INSERT INTO Postulantes (ID_Postulante, Nombres, Apellidos, Cedula_Identidad, Telefono, ID_Universidad) VALUES (%s, %s, %s, %s, %s, %s)"
            valores = (id_usuario, datos["Nombres"], datos["Apellidos"], datos["Cédula"], datos["Teléfono"], datos["ID_Universidad"])
            cursor.execute(sql_postulante, valores)
        
        conexion.commit()
        return True, f"Usuario tipo '{tipo_usuario}' creado con éxito."
    except mysql.connector.IntegrityError as e:
        conexion.rollback(); return False, f"Error de integridad: El Email, RIF o Cédula ya existen. ({e})"
    except Error as e:
        conexion.rollback(); return False, f"Error inesperado al crear usuario: {e}"
    finally: cursor.close()

def crear_vacante_db(conexion, id_empresa, cargo, descripcion, salario, id_profesion):
    cursor = conexion.cursor()
    try:
        sql = "INSERT INTO Vacantes (ID_Empresa, Cargo_Vacante, Descripcion_Perfil, Salario_Ofrecido, ID_Profesion) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (id_empresa, cargo, descripcion, salario, id_profesion))
        conexion.commit()
        return True, "Vacante creada con éxito."
    except Error as e: return False, f"Error al crear vacante: {e}"
    finally: cursor.close()

def contratar_postulante_db(conexion, id_postulacion, datos):
    cursor = conexion.cursor(dictionary=True)
    try:
        conexion.start_transaction()
        sql_contrato = """INSERT INTO Contratos (ID_Postulacion, Fecha_Contratacion, Tipo_Contrato, Salario_Acordado, Tipo_Sangre, 
                          Contacto_Emergencia_Nombre, Contacto_Emergencia_Telefono, Numero_Cuenta, ID_Banco) 
                          VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s)"""
        
        valores = (
            id_postulacion, 
            datos['Tipo_Contrato'], 
            datos['Salario_Acordado'], 
            datos['Tipo_Sangre'], 
            datos['Contacto_Emergencia_Nombre'], 
            datos['Contacto_Emergencia_Telefono'], 
            datos['Numero_Cuenta'], 
            datos['ID_Banco']
        )
        cursor.execute(sql_contrato, valores)
        
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
        sql = "INSERT INTO Postulaciones (ID_Postulante, ID_Vacante) VALUES (%s, %s)"
        cursor.execute(sql, (id_postulante, id_vacante))
        conexion.commit()
        return True, "¡Postulación exitosa!"
    except mysql.connector.IntegrityError: return False, "Error: Ya te has postulado a esta vacante."
    except Error as e: return False, f"Error inesperado: {e}"
    finally: cursor.close()

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
            conexion.rollback(); return False, "No hay empleados activos para esta empresa."
        for contrato in contratos:
            salario = contrato['Salario_Acordado']
            ded_inces, ded_ivss = float(salario) * 0.005, float(salario) * 0.01
            comision = float(salario) * 0.02
            neto = float(salario) - ded_inces - ded_ivss
            sql_recibo = "INSERT INTO Recibos (ID_Nomina, ID_Contrato, Salario_Base, Monto_Deduccion_INCES, Monto_Deduccion_IVSS, Comision_Hiring_Group, Salario_Neto_Pagado, Fecha_Pago) VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE())"
            cursor.execute(sql_recibo, (id_nomina, contrato['ID_Contrato'], salario, ded_inces, ded_ivss, comision, neto))
        conexion.commit()
        return True, f"Nómina generada con éxito para {len(contratos)} empleado(s)."
    except mysql.connector.IntegrityError:
        conexion.rollback(); return False, "Ya se generó una nómina para esta empresa en este periodo."
    except Error as e:
        conexion.rollback(); return False, f"Error al generar nómina: {e}"
    finally: cursor.close()

def crear_experiencia_db(conexion, id_postulante, datos):
    cursor = conexion.cursor()
    sql = "INSERT INTO Experiencias_Laborales (ID_Postulante, Empresa, Cargo_Ocupado, Fecha_Inicio, Fecha_Fin, Descripcion) VALUES (%s, %s, %s, %s, %s, %s)"
    try:
        fecha_fin = datos['Fecha Fin'] if datos['Fecha Fin'] else None
        cursor.execute(sql, (id_postulante, datos['Empresa'], datos['Cargo'], datos['Fecha Inicio'], fecha_fin, datos['Descripcion']))
        conexion.commit()
        return True, "Experiencia agregada."
    except Error as e: return False, f"Error al agregar experiencia: {e}"
    finally: cursor.close()

# --- FUNCIONES DE CONSULTA (CRUD - READ) ---
def get_active_vacantes(conexion, filtro_area=None, filtro_prof=None, sort_salary=None):
    cursor = conexion.cursor(dictionary=True)
    query = """
        SELECT v.ID_Vacante, v.Cargo_Vacante, v.Descripcion_Perfil, v.Salario_Ofrecido, 
               e.Nombre_Empresa, p.Nombre_Profesion, ac.Nombre_Area
        FROM Vacantes v 
        JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa 
        JOIN Profesiones p ON v.ID_Profesion = p.ID_Profesion
        LEFT JOIN Areas_Conocimiento ac ON p.ID_Area_Conocimiento = ac.ID_Area_Conocimiento
        WHERE v.Estatus = 'Activa'
    """
    params = []
    if filtro_area: query += " AND ac.ID_Area_Conocimiento = %s"; params.append(filtro_area)
    if filtro_prof: query += " AND p.ID_Profesion = %s"; params.append(filtro_prof)
    if sort_salary: query += f" ORDER BY v.Salario_Ofrecido {sort_salary}"
    cursor.execute(query, params)
    return cursor.fetchall()

def get_postulaciones_para_contratar(conexion):
    cursor = conexion.cursor(dictionary=True)
    query = """SELECT post.ID_Postulacion, p.Nombres, p.Apellidos, v.Cargo_Vacante 
               FROM Postulaciones post 
               JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante 
               JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante 
               WHERE post.Estatus = 'Recibida' OR post.Estatus = 'En Revision'"""
    cursor.execute(query)
    return cursor.fetchall()

def get_vacantes_por_empresa(conexion, id_empresa):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT ID_Vacante, Cargo_Vacante, Descripcion_Perfil, Salario_Ofrecido, Estatus FROM Vacantes WHERE ID_Empresa = %s", (id_empresa,))
    return cursor.fetchall()

def get_postulaciones_por_postulante(conexion, id_postulante):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT v.Cargo_Vacante, v.Salario_Ofrecido, e.Nombre_Empresa, p.Fecha_Postulacion, p.Estatus FROM Postulaciones p JOIN Vacantes v ON p.ID_Vacante = v.ID_Vacante JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa WHERE p.ID_Postulante = %s ORDER BY p.Fecha_Postulacion DESC", (id_postulante,))
    return cursor.fetchall()

def get_recibos_por_contratado(conexion, id_postulante, mes=None, anio=None):
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT r.Fecha_Pago, r.Salario_Base, r.Salario_Neto_Pagado, n.Mes, n.Anio FROM Recibos r JOIN Nominas n ON r.ID_Nomina = n.ID_Nomina JOIN Contratos c ON r.ID_Contrato = c.ID_Contrato JOIN Postulaciones p ON c.ID_Postulacion = p.ID_Postulacion WHERE p.ID_Postulante = %s"
    params = [id_postulante]
    if mes: query += " AND n.Mes = %s"; params.append(mes)
    if anio: query += " AND n.Anio = %s"; params.append(anio)
    query += " ORDER BY n.Anio DESC, n.Mes DESC"
    cursor.execute(query, params)
    return cursor.fetchall()

def get_datos_constancia(conexion, id_postulante):
    cursor = conexion.cursor(dictionary=True)
    query = """
        SELECT p.Nombres, p.Apellidos, c.Fecha_Contratacion, c.Salario_Acordado, 
               v.Cargo_Vacante, e.Nombre_Empresa 
        FROM Contratos c
        JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion
        JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante
        JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante
        JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa
        WHERE p.ID_Postulante = %s AND c.Estatus = 'Activo'
    """
    cursor.execute(query, (id_postulante,))
    datos = cursor.fetchone()
    if not datos: return None
    meses_es = ("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre")
    fecha_contrato = datos['Fecha_Contratacion']; fecha_hoy = datetime.now()
    fecha_inicio_str = f"{fecha_contrato.day} de {meses_es[fecha_contrato.month - 1]} de {fecha_contrato.year}"
    fecha_actual_str = f"{fecha_hoy.day} de {meses_es[fecha_hoy.month - 1]} de {fecha_hoy.year}"
    nombre_completo = f"{datos['Nombres']} {datos['Apellidos']}"; salario_str = f"{float(datos['Salario_Acordado']):.2f}"
    return (f"                 A QUIEN PUEDA INTERESAR\n\n"
            f"Por medio de la presente la empresa HIRING GROUP hace constar que el ciudadano(a)\n"
            f"{nombre_completo}, labora con nosotros desde {fecha_inicio_str}, cumpliendo\n"
            f"funciones en el cargo de {datos['Cargo_Vacante']} en la empresa {datos['Nombre_Empresa']}, devengando un\n"
            f"salario mensual de {salario_str}.\n\n"
            f"Constancia que se pide por la parte interesada en la ciudad de Puerto Ordaz en fecha\n"
            f"{fecha_actual_str}")

def get_nomina_reporte_db(conexion, id_empresa, mes, anio):
    cursor = conexion.cursor(dictionary=True)
    query = """
        SELECT CONCAT(p.Nombres, ' ', p.Apellidos) AS Empleado, p.Cedula_Identidad, rec.Salario_Base
        FROM Recibos rec JOIN Nominas nom ON rec.ID_Nomina = nom.ID_Nomina
        JOIN Contratos c ON rec.ID_Contrato = c.ID_Contrato JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion
        JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante
        WHERE nom.ID_Empresa = %s AND nom.Mes = %s AND nom.Anio = %s
    """
    cursor.execute(query, (id_empresa, mes, anio)); return cursor.fetchall()

def get_toda_nomina_reporte_db(conexion):
    cursor = conexion.cursor(dictionary=True)
    query = """
        SELECT e.Nombre_Empresa, nom.Mes, nom.Anio, SUM(rec.Salario_Base) as Total_Nomina
        FROM Recibos rec JOIN Nominas nom ON rec.ID_Nomina = nom.ID_Nomina
        JOIN Empresas e ON nom.ID_Empresa = e.ID_Empresa
        GROUP BY e.Nombre_Empresa, nom.Mes, nom.Anio ORDER BY e.Nombre_Empresa, nom.Anio DESC, nom.Mes DESC
    """
    cursor.execute(query); return cursor.fetchall()
    
def get_experiencias_db(conexion, id_postulante):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT ID_Experiencia, Empresa, Cargo_Ocupado, Fecha_Inicio, Fecha_Fin, Descripcion FROM Experiencias_Laborales WHERE ID_Postulante = %s ORDER BY Fecha_Inicio DESC", (id_postulante,))
    return cursor.fetchall()

def get_single_postulante(conexion, id_postulante):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Postulantes WHERE ID_Postulante = %s", (id_postulante,))
    return cursor.fetchone()

def get_single_empresa(conexion, id_empresa):
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Empresas WHERE ID_Empresa = %s", (id_empresa,))
    return cursor.fetchone()

# --- FUNCIONES DE ACTUALIZACIÓN (CRUD - UPDATE) ---
def actualizar_usuario_db(conexion, id_usuario, tipo_usuario, datos):
    cursor = conexion.cursor()
    try:
        conexion.start_transaction()
        if "Contraseña" in datos and datos["Contraseña"]:
            cursor.execute("UPDATE Usuarios SET Password = %s WHERE ID_Usuario = %s", (datos["Contraseña"], id_usuario))
        
        if tipo_usuario == 'Empresa':
            sql = "UPDATE Empresas SET Nombre_Empresa = %s, Sector_Industrial = %s, Persona_Contacto = %s, Telefono_Contacto = %s, Email_Contacto = %s WHERE ID_Empresa = %s"
            valores = (datos["Nombre Empresa"], datos["Sector"], datos["Persona de Contacto"], datos["Teléfono de Contacto"], datos["Email de Contacto"], id_usuario)
            cursor.execute(sql, valores)
        elif tipo_usuario in ['Postulante', 'Contratado']:
            sql = "UPDATE Postulantes SET Nombres = %s, Apellidos = %s, Telefono = %s, ID_Universidad = %s WHERE ID_Postulante = %s"
            valores = (datos["Nombres"], datos["Apellidos"], datos["Teléfono"], datos["ID_Universidad"], id_usuario)
            cursor.execute(sql, valores)
        
        conexion.commit()
        return True, "Datos actualizados con éxito."
    except Error as e:
        conexion.rollback(); return False, f"Error al actualizar los datos: {e}"
    finally: cursor.close()

def actualizar_vacante_db(conexion, id_vacante, cargo, descripcion, salario, estatus):
    cursor = conexion.cursor()
    try:
        sql = "UPDATE Vacantes SET Cargo_Vacante = %s, Descripcion_Perfil = %s, Salario_Ofrecido = %s, Estatus = %s WHERE ID_Vacante = %s"
        cursor.execute(sql, (cargo, descripcion, salario, estatus, id_vacante))
        conexion.commit()
        return True, "Vacante actualizada con éxito."
    except Error as e: return False, f"Error al actualizar la vacante: {e}"
    finally: cursor.close()

# --- FUNCIONES DE ELIMINACIÓN (CRUD - DELETE) ---
def eliminar_vacante_db(conexion, id_vacante):
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) as count FROM Postulaciones WHERE ID_Vacante = %s", (id_vacante,))
        if cursor.fetchone()['count'] > 0:
            return False, "No se puede eliminar la vacante porque tiene postulaciones. Considere marcarla como 'Cerrada' o 'Inactiva'."
        cursor.execute("DELETE FROM Vacantes WHERE ID_Vacante = %s", (id_vacante,))
        conexion.commit()
        return True, "Vacante eliminada con éxito."
    except Error as e: return False, f"Error al eliminar la vacante: {e}"
    finally: cursor.close()

def eliminar_usuario_db(conexion, id_usuario):
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM Usuarios WHERE ID_Usuario = %s", (id_usuario,))
        conexion.commit()
        if cursor.rowcount > 0: return True, "Usuario eliminado con éxito."
        else: return False, "No se encontró el usuario para eliminar."
    except mysql.connector.IntegrityError as e: return False, f"Error de integridad: No se puede eliminar. Revise contratos o postulaciones asociadas. ({e})"
    except Error as e: return False, f"Error inesperado al eliminar el usuario: {e}"
    finally: cursor.close()

def eliminar_experiencia_db(conexion, id_experiencia):
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM Experiencias_Laborales WHERE ID_Experiencia = %s", (id_experiencia,))
        conexion.commit()
        return True, "Experiencia eliminada."
    except Error as e: return False, f"Error al eliminar: {e}"
    finally: cursor.close()