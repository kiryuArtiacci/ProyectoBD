import sqlite3
from datetime import datetime
from contextlib import contextmanager


# --- CONTEXT MANAGER PARA LA CONEXIÓN ---
@contextmanager
def get_db_connection():
    """
    Un context manager que maneja la apertura y cierre de la conexión a la BD.
    Garantiza que la conexión siempre se cierre, incluso si hay errores.
    """
    conn = None
    try:
        conn = sqlite3.connect("hiring_group.db", timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    except sqlite3.Error as e:
        print(f"Error de conexión a la base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()


# --- FUNCIONES DE LA BASE DE DATOS (REFACTORIZADAS) ---
# Ninguna función recibe 'conexion' como argumento.


def login_usuario(email, password):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT ID_Usuario, Email, Tipo_Usuario, Estatus FROM Usuarios WHERE Email = ? AND Password = ?"
        cursor.execute(query, (email, password))
        usuario_data = cursor.fetchone()

        if not usuario_data:
            return None, None

        usuario = dict(usuario_data)
        if usuario["Estatus"] != "Activo":
            return None, None

        if usuario["Tipo_Usuario"] == "Postulante":
            query_contrato = "SELECT c.ID_Contrato FROM Contratos c JOIN Postulaciones p ON c.ID_Postulacion = p.ID_Postulacion WHERE p.ID_Postulante = ? AND c.Estatus = 'Activo'"
            cursor.execute(query_contrato, (usuario["ID_Usuario"],))
            if cursor.fetchone():
                usuario["Tipo_Usuario"] = "Contratado"

        return usuario, usuario["Tipo_Usuario"]


def hay_usuarios_registrados():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Usuarios LIMIT 1")
            return cursor.fetchone() is not None
    except sqlite3.Error:
        return False


def get_catalogo(tabla, id_col, nombre_col):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if isinstance(nombre_col, list):
            nombre_col_str = ", ".join(nombre_col)
            order_col = nombre_col[0]
        else:
            nombre_col_str = nombre_col
            order_col = nombre_col

        cursor.execute(
            f"SELECT {id_col}, {nombre_col_str} FROM {tabla} ORDER BY {order_col}"
        )
        return cursor.fetchall()


def crear_item_catalogo(tabla, nombre_col, nombre_valor):
    try:
        with get_db_connection() as conn:
            conn.execute(
                f"INSERT INTO {tabla} ({nombre_col}) VALUES (?)", (nombre_valor,)
            )
            conn.commit()
            return True, "Elemento agregado con éxito."
    except sqlite3.IntegrityError:
        return False, f"Error: Ese valor ya existe en {tabla}."
    except sqlite3.Error as e:
        return False, f"Error inesperado: {e}"


def actualizar_item_catalogo(tabla, id_col, nombre_col, id_valor, nuevo_nombre):
    try:
        with get_db_connection() as conn:
            conn.execute(
                f"UPDATE {tabla} SET {nombre_col} = ? WHERE {id_col} = ?",
                (nuevo_nombre, id_valor),
            )
            conn.commit()
            return True, "Elemento actualizado con éxito."
    except sqlite3.Error as e:
        return False, f"Error al actualizar: {e}"


def eliminar_item_catalogo(tabla, id_col, id_valor):
    try:
        with get_db_connection() as conn:
            conn.execute(f"DELETE FROM {tabla} WHERE {id_col} = ?", (id_valor,))
            conn.commit()
            return True, "Elemento eliminado con éxito."
    except sqlite3.IntegrityError:
        return False, "Error: El elemento está en uso y no se puede eliminar."
    except sqlite3.Error as e:
        return False, f"Error inesperado: {e}"


def registrar_usuario_db(tipo_usuario, datos):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            sql_usuario = (
                "INSERT INTO Usuarios (Email, Password, Tipo_Usuario) VALUES (?, ?, ?)"
            )
            cursor.execute(
                sql_usuario, (datos["Email"], datos["Contraseña"], tipo_usuario)
            )
            id_usuario = cursor.lastrowid

            if tipo_usuario == "Empresa":
                sql_empresa = "INSERT INTO Empresas (ID_Empresa, Nombre_Empresa, RIF, Sector_Industrial, Persona_Contacto, Telefono_Contacto, Email_Contacto) VALUES (?, ?, ?, ?, ?, ?, ?)"
                valores = (
                    id_usuario,
                    datos["Nombre Empresa"],
                    datos["RIF"],
                    datos["Sector"],
                    datos["Persona de Contacto"],
                    datos["Teléfono de Contacto"],
                    datos["Email de Contacto"],
                )
                cursor.execute(sql_empresa, valores)
            elif tipo_usuario == "Postulante":
                sql_postulante = "INSERT INTO Postulantes (ID_Postulante, Nombres, Apellidos, Cedula_Identidad, Telefono, ID_Universidad) VALUES (?, ?, ?, ?, ?, ?)"
                valores = (
                    id_usuario,
                    datos["Nombres"],
                    datos["Apellidos"],
                    datos["Cédula"],
                    datos["Teléfono"],
                    datos["ID_Universidad"],
                )
                cursor.execute(sql_postulante, valores)

            conn.commit()
            return True, f"Usuario tipo '{tipo_usuario}' creado con éxito."
    except sqlite3.IntegrityError as e:
        return False, f"Error de integridad: El Email, RIF o Cédula ya existen. ({e})"
    except sqlite3.Error as e:
        return False, f"Error inesperado al crear usuario: {e}"


def crear_vacante_db(id_empresa, cargo, descripcion, salario, id_profesion):
    try:
        with get_db_connection() as conn:
            sql = "INSERT INTO Vacantes (ID_Empresa, Cargo_Vacante, Descripcion_Perfil, Salario_Ofrecido, ID_Profesion) VALUES (?, ?, ?, ?, ?)"
            conn.execute(sql, (id_empresa, cargo, descripcion, salario, id_profesion))
            conn.commit()
            return True, "Vacante creada con éxito."
    except sqlite3.Error as e:
        return False, f"Error al crear vacante: {e}"


def contratar_postulante_db(id_postulacion, datos):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            sql_contrato = """INSERT INTO Contratos (ID_Postulacion, Fecha_Contratacion, Tipo_Contrato, Salario_Acordado, Tipo_Sangre, 
                              Contacto_Emergencia_Nombre, Contacto_Emergencia_Telefono, Numero_Cuenta, ID_Banco) 
                              VALUES (?, date('now'), ?, ?, ?, ?, ?, ?, ?)"""
            valores = (
                id_postulacion,
                datos["Tipo_Contrato"],
                datos["Salario_Acordado"],
                datos["Tipo_Sangre"],
                datos["Contacto_Emergencia_Nombre"],
                datos["Contacto_Emergencia_Telefono"],
                datos["Numero_Cuenta"],
                datos["ID_Banco"],
            )
            cursor.execute(sql_contrato, valores)
            cursor.execute(
                "SELECT ID_Vacante FROM Postulaciones WHERE ID_Postulacion = ?",
                (id_postulacion,),
            )
            id_vacante = cursor.fetchone()["ID_Vacante"]
            cursor.execute(
                "UPDATE Vacantes SET Estatus = 'Cerrada' WHERE ID_Vacante = ?",
                (id_vacante,),
            )
            cursor.execute(
                "UPDATE Postulaciones SET Estatus = 'Aceptada' WHERE ID_Postulacion = ?",
                (id_postulacion,),
            )
            conn.commit()
            return True, "Contratación exitosa."
    except sqlite3.Error as e:
        return False, f"Error al contratar: {e}"


def aplicar_a_vacante_db(id_postulante, id_vacante):
    try:
        with get_db_connection() as conn:
            sql = "INSERT INTO Postulaciones (ID_Postulante, ID_Vacante) VALUES (?, ?)"
            conn.execute(sql, (id_postulante, id_vacante))
            conn.commit()
            return True, "¡Postulación exitosa!"
    except sqlite3.IntegrityError:
        return False, "Error: Ya te has postulado a esta vacante."
    except sqlite3.Error as e:
        return False, f"Error inesperado: {e}"


def ejecutar_nomina_db(id_empresa, mes, anio):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            check_query = "SELECT ID_Nomina FROM Nominas WHERE ID_Empresa = ? AND Mes = ? AND Anio = ?"
            cursor.execute(check_query, (id_empresa, mes, anio))
            if cursor.fetchone():
                return (
                    False,
                    "Ya se generó una nómina para esta empresa en este periodo.",
                    None,
                )
            sql_nomina = "INSERT INTO Nominas (ID_Empresa, Mes, Anio) VALUES (?, ?, ?)"
            cursor.execute(sql_nomina, (id_empresa, mes, anio))
            id_nomina = cursor.lastrowid
            sql_contratos = "SELECT c.ID_Contrato, c.Salario_Acordado FROM Contratos c JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante WHERE v.ID_Empresa = ? AND c.Estatus = 'Activo'"
            cursor.execute(sql_contratos, (id_empresa,))
            contratos = cursor.fetchall()
            if not contratos:
                conn.rollback()
                return False, "No hay empleados activos para esta empresa.", None
            for contrato in contratos:
                salario = contrato["Salario_Acordado"]
                ded_inces, ded_ivss, comision = (
                    float(salario) * 0.005,
                    float(salario) * 0.01,
                    float(salario) * 0.02,
                )
                neto = float(salario) - ded_inces - ded_ivss
                sql_recibo = "INSERT INTO Recibos (ID_Nomina, ID_Contrato, Salario_Base, Monto_Deduccion_INCES, Monto_Deduccion_IVSS, Comision_Hiring_Group, Salario_Neto_Pagado, Fecha_Pago) VALUES (?, ?, ?, ?, ?, ?, ?, date('now'))"
                cursor.execute(
                    sql_recibo,
                    (
                        id_nomina,
                        contrato["ID_Contrato"],
                        salario,
                        ded_inces,
                        ded_ivss,
                        comision,
                        neto,
                    ),
                )
            conn.commit()
            return (
                True,
                f"Nómina generada con éxito para {len(contratos)} empleado(s).",
                id_nomina,
            )
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Error al generar nómina: {e}", None


def crear_experiencia_db(id_postulante, datos):
    try:
        with get_db_connection() as conn:
            sql = "INSERT INTO Experiencias_Laborales (ID_Postulante, Empresa, Cargo_Ocupado, Fecha_Inicio, Fecha_Fin, Descripcion) VALUES (?, ?, ?, ?, ?, ?)"
            fecha_fin = datos.get("Fecha Fin (YYYY-MM-DD, opcional)") or None
            conn.execute(
                sql,
                (
                    id_postulante,
                    datos["Empresa"],
                    datos["Cargo"],
                    datos["Fecha Inicio (YYYY-MM-DD)"],
                    fecha_fin,
                    datos["Descripción"],
                ),
            )
            conn.commit()
            return True, "Experiencia agregada."
    except sqlite3.Error as e:
        return False, f"Error al agregar experiencia: {e}"


def get_active_vacantes(filtro_area=None, filtro_prof=None, sort_salary=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """SELECT v.ID_Vacante, v.Cargo_Vacante, v.Descripcion_Perfil, v.Salario_Ofrecido, 
                   e.Nombre_Empresa, p.Nombre_Profesion, ac.Nombre_Area
                   FROM Vacantes v JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa JOIN Profesiones p ON v.ID_Profesion = p.ID_Profesion
                   LEFT JOIN Areas_Conocimiento ac ON p.ID_Area_Conocimiento = ac.ID_Area_Conocimiento
                   WHERE v.Estatus = 'Activa'"""
        params = []
        if filtro_area:
            query += " AND ac.ID_Area_Conocimiento = ?"
            params.append(filtro_area)
        if filtro_prof:
            query += " AND p.ID_Profesion = ?"
            params.append(filtro_prof)
        if sort_salary:
            query += f" ORDER BY v.Salario_Ofrecido {sort_salary}"
        cursor.execute(query, params)
        return cursor.fetchall()


def get_postulaciones_para_contratar():
    with get_db_connection() as conn:
        return conn.execute("""SELECT post.ID_Postulacion, p.Nombres, p.Apellidos, v.Cargo_Vacante 
                               FROM Postulaciones post JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante 
                               JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante 
                               WHERE post.Estatus IN ('Recibida', 'En Revision')""").fetchall()


def get_vacantes_por_empresa(id_empresa):
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT ID_Vacante, Cargo_Vacante, Descripcion_Perfil, Salario_Ofrecido, Estatus FROM Vacantes WHERE ID_Empresa = ?",
            (id_empresa,),
        ).fetchall()


def get_postulaciones_por_postulante(id_postulante):
    with get_db_connection() as conn:
        query = "SELECT v.Cargo_Vacante, v.Salario_Ofrecido, e.Nombre_Empresa, strftime('%Y-%m-%d %H:%M', p.Fecha_Postulacion) as Fecha_Postulacion, p.Estatus FROM Postulaciones p JOIN Vacantes v ON p.ID_Vacante = v.ID_Vacante JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa WHERE p.ID_Postulante = ? ORDER BY p.Fecha_Postulacion DESC"
        return conn.execute(query, (id_postulante,)).fetchall()


def get_recibos_por_contratado(id_postulante, mes=None, anio=None):
    with get_db_connection() as conn:
        query = "SELECT r.Fecha_Pago, r.Salario_Base, r.Salario_Neto_Pagado, n.Mes, n.Anio FROM Recibos r JOIN Nominas n ON r.ID_Nomina = n.ID_Nomina JOIN Contratos c ON r.ID_Contrato = c.ID_Contrato JOIN Postulaciones p ON c.ID_Postulacion = p.ID_Postulacion WHERE p.ID_Postulante = ?"
        params = [id_postulante]
        if mes:
            query += " AND n.Mes = ?"
            params.append(mes)
        if anio:
            query += " AND n.Anio = ?"
            params.append(anio)
        query += " ORDER BY n.Anio DESC, n.Mes DESC"
        return conn.execute(query, params).fetchall()


def get_datos_constancia(id_postulante):
    with get_db_connection() as conn:
        query = """SELECT p.Nombres, p.Apellidos, c.Fecha_Contratacion, c.Salario_Acordado, 
                   v.Cargo_Vacante, e.Nombre_Empresa 
                   FROM Contratos c JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion
                   JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante
                   JOIN Vacantes v ON post.ID_Vacante = v.ID_Vacante
                   JOIN Empresas e ON v.ID_Empresa = e.ID_Empresa
                   WHERE p.ID_Postulante = ? AND c.Estatus = 'Activo'"""
        datos = conn.execute(query, (id_postulante,)).fetchone()
        if not datos:
            return None
        meses_es = (
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        )
        fecha_contrato = datetime.strptime(datos["Fecha_Contratacion"], "%Y-%m-%d")
        fecha_hoy = datetime.now()
        fecha_inicio_str = f"{fecha_contrato.day} de {meses_es[fecha_contrato.month - 1]} de {fecha_contrato.year}"
        fecha_actual_str = (
            f"{fecha_hoy.day} de {meses_es[fecha_hoy.month - 1]} de {fecha_hoy.year}"
        )
        nombre_completo = f"{datos['Nombres']} {datos['Apellidos']}"
        salario_str = f"{float(datos['Salario_Acordado']):.2f}"
        return (
            f"                 A QUIEN PUEDA INTERESAR\n\n"
            f"Por medio de la presente la empresa HIRING GROUP hace constar que el ciudadano(a)\n"
            f"{nombre_completo}, labora con nosotros desde {fecha_inicio_str}, cumpliendo\n"
            f"funciones en el cargo de {datos['Cargo_Vacante']} en la empresa {datos['Nombre_Empresa']}, devengando un\n"
            f"salario mensual de {salario_str}.\n\n"
            f"Constancia que se pide por la parte interesada en la ciudad de Puerto Ordaz en fecha\n"
            f"{fecha_actual_str}"
        )


def get_nomina_reporte_db(id_empresa, mes, anio):
    with get_db_connection() as conn:
        query = """SELECT (p.Nombres || ' ' || p.Apellidos) AS Empleado, p.Cedula_Identidad, rec.Salario_Base
                   FROM Recibos rec JOIN Nominas nom ON rec.ID_Nomina = nom.ID_Nomina
                   JOIN Contratos c ON rec.ID_Contrato = c.ID_Contrato JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion
                   JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante
                   WHERE nom.ID_Empresa = ? AND nom.Mes = ? AND nom.Anio = ?"""
        return conn.execute(query, (id_empresa, mes, anio)).fetchall()


def get_toda_nomina_reporte_db():
    with get_db_connection() as conn:
        query = """SELECT e.Nombre_Empresa, nom.Mes, nom.Anio, SUM(rec.Salario_Base) as Total_Nomina
                   FROM Recibos rec JOIN Nominas nom ON rec.ID_Nomina = nom.ID_Nomina
                   JOIN Empresas e ON nom.ID_Empresa = e.ID_Empresa
                   GROUP BY e.Nombre_Empresa, nom.Mes, nom.Anio ORDER BY e.Nombre_Empresa, nom.Anio DESC, nom.Mes DESC"""
        return conn.execute(query).fetchall()


def get_nomina_generada_detalle_db(id_nomina):
    with get_db_connection() as conn:
        query = """SELECT (p.Nombres || ' ' || p.Apellidos) AS Empleado, p.Cedula_Identidad, rec.Salario_Base,
                   (rec.Monto_Deduccion_INCES + rec.Monto_Deduccion_IVSS) as Total_Deducciones, rec.Salario_Neto_Pagado
                   FROM Recibos rec JOIN Contratos c ON rec.ID_Contrato = c.ID_Contrato 
                   JOIN Postulaciones post ON c.ID_Postulacion = post.ID_Postulacion
                   JOIN Postulantes p ON post.ID_Postulante = p.ID_Postulante
                   WHERE rec.ID_Nomina = ? ORDER BY Empleado"""
        return conn.execute(query, (id_nomina,)).fetchall()


def get_experiencias_db(id_postulante):
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT ID_Experiencia, Empresa, Cargo_Ocupado, Fecha_Inicio, Fecha_Fin, Descripcion FROM Experiencias_Laborales WHERE ID_Postulante = ? ORDER BY Fecha_Inicio DESC",
            (id_postulante,),
        ).fetchall()


def get_single_postulante(id_postulante):
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM Postulantes WHERE ID_Postulante = ?", (id_postulante,)
        ).fetchone()


def get_single_empresa(id_empresa):
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM Empresas WHERE ID_Empresa = ?", (id_empresa,)
        ).fetchone()


def actualizar_usuario_db(id_usuario, tipo_usuario, datos):
    try:
        with get_db_connection() as conn:
            if "Contraseña" in datos and datos["Contraseña"]:
                conn.execute(
                    "UPDATE Usuarios SET Password = ? WHERE ID_Usuario = ?",
                    (datos["Contraseña"], id_usuario),
                )
            if tipo_usuario == "Empresa":
                sql = "UPDATE Empresas SET Nombre_Empresa = ?, Sector_Industrial = ?, Persona_Contacto = ?, Telefono_Contacto = ?, Email_Contacto = ? WHERE ID_Empresa = ?"
                valores = (
                    datos["Nombre Empresa"],
                    datos["Sector"],
                    datos["Persona de Contacto"],
                    datos["Teléfono de Contacto"],
                    datos["Email de Contacto"],
                    id_usuario,
                )
                conn.execute(sql, valores)
            elif tipo_usuario in ["Postulante", "Contratado"]:
                sql = "UPDATE Postulantes SET Nombres = ?, Apellidos = ?, Telefono = ?, ID_Universidad = ? WHERE ID_Postulante = ?"
                valores = (
                    datos["Nombres"],
                    datos["Apellidos"],
                    datos["Teléfono"],
                    datos["ID_Universidad"],
                    id_usuario,
                )
                conn.execute(sql, valores)
            conn.commit()
            return True, "Datos actualizados con éxito."
    except sqlite3.Error as e:
        return False, f"Error al actualizar los datos: {e}"


def actualizar_vacante_db(id_vacante, cargo, descripcion, salario, estatus):
    try:
        with get_db_connection() as conn:
            sql = "UPDATE Vacantes SET Cargo_Vacante = ?, Descripcion_Perfil = ?, Salario_Ofrecido = ?, Estatus = ? WHERE ID_Vacante = ?"
            conn.execute(sql, (cargo, descripcion, salario, estatus, id_vacante))
            conn.commit()
            return True, "Vacante actualizada con éxito."
    except sqlite3.Error as e:
        return False, f"Error al actualizar la vacante: {e}"


def eliminar_vacante_db(id_vacante):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM Postulaciones WHERE ID_Vacante = ?",
                (id_vacante,),
            )
            if cursor.fetchone()["count"] > 0:
                return (
                    False,
                    "No se puede eliminar la vacante porque tiene postulaciones. Considere marcarla como 'Cerrada' o 'Inactiva'.",
                )
            cursor.execute("DELETE FROM Vacantes WHERE ID_Vacante = ?", (id_vacante,))
            conn.commit()
            return True, "Vacante eliminada con éxito."
    except sqlite3.Error as e:
        return False, f"Error al eliminar la vacante: {e}"


def eliminar_usuario_db(id_usuario):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Usuarios WHERE ID_Usuario = ?", (id_usuario,))
            conn.commit()
            if cursor.rowcount > 0:
                return True, "Usuario eliminado con éxito."
            else:
                return False, "No se encontró el usuario para eliminar."
    except sqlite3.IntegrityError as e:
        return (
            False,
            f"Error de integridad: No se puede eliminar. Revise contratos o postulaciones asociadas. ({e})",
        )
    except sqlite3.Error as e:
        return False, f"Error inesperado al eliminar el usuario: {e}"


def eliminar_experiencia_db(id_experiencia):
    try:
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM Experiencias_Laborales WHERE ID_Experiencia = ?",
                (id_experiencia,),
            )
            conn.commit()
            return True, "Experiencia eliminada."
    except sqlite3.Error as e:
        return False, f"Error al eliminar: {e}"
