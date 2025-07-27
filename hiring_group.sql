PRAGMA foreign_keys = ON;

-- --- Tabla de Usuarios (Tabla Central) ---
CREATE TABLE IF NOT EXISTS `usuarios` (
  `ID_Usuario` INTEGER PRIMARY KEY,
  `Email` TEXT NOT NULL UNIQUE,
  `Password` TEXT NOT NULL,
  `Tipo_Usuario` TEXT NOT NULL CHECK(`Tipo_Usuario` IN ('HiringGroup','Empresa','Postulante')),
  `Fecha_Creacion` TEXT DEFAULT CURRENT_TIMESTAMP,
  `Estatus` TEXT DEFAULT 'Activo' CHECK(`Estatus` IN ('Activo','Inactivo'))
);

-- --- Tablas de Catálogos ---
CREATE TABLE IF NOT EXISTS `areas_conocimiento` (
  `ID_Area_Conocimiento` INTEGER PRIMARY KEY,
  `Nombre_Area` TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS `bancos` (
  `ID_Banco` INTEGER PRIMARY KEY,
  `Nombre_Banco` TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS `universidades` (
  `ID_Universidad` INTEGER PRIMARY KEY,
  `Nombre_Universidad` TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS `profesiones` (
  `ID_Profesion` INTEGER PRIMARY KEY,
  `Nombre_Profesion` TEXT NOT NULL UNIQUE,
  `ID_Area_Conocimiento` INTEGER,
  FOREIGN KEY(`ID_Area_Conocimiento`) REFERENCES `areas_conocimiento`(`ID_Area_Conocimiento`) ON DELETE SET NULL
);

-- --- Tablas de Perfiles (Especialización de Usuarios) ---
CREATE TABLE IF NOT EXISTS `empresas` (
  `ID_Empresa` INTEGER PRIMARY KEY,
  `Nombre_Empresa` TEXT NOT NULL,
  `RIF` TEXT DEFAULT NULL UNIQUE,
  `Sector_Industrial` TEXT DEFAULT NULL,
  `Persona_Contacto` TEXT DEFAULT NULL,
  `Telefono_Contacto` TEXT DEFAULT NULL,
  `Email_Contacto` TEXT DEFAULT NULL,
  FOREIGN KEY(`ID_Empresa`) REFERENCES `usuarios`(`ID_Usuario`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `postulantes` (
  `ID_Postulante` INTEGER PRIMARY KEY,
  `Nombres` TEXT NOT NULL,
  `Apellidos` TEXT NOT NULL,
  `Cedula_Identidad` TEXT DEFAULT NULL UNIQUE,
  `Fecha_Nacimiento` TEXT DEFAULT NULL,
  `Direccion` TEXT DEFAULT NULL,
  `Telefono` TEXT DEFAULT NULL,
  `ID_Universidad` INTEGER DEFAULT NULL,
  FOREIGN KEY(`ID_Postulante`) REFERENCES `usuarios`(`ID_Usuario`) ON DELETE CASCADE,
  FOREIGN KEY(`ID_Universidad`) REFERENCES `universidades`(`ID_Universidad`) ON DELETE SET NULL
);

-- --- Tablas del Flujo Principal ---
CREATE TABLE IF NOT EXISTS `vacantes` (
  `ID_Vacante` INTEGER PRIMARY KEY,
  `ID_Empresa` INTEGER NOT NULL,
  `Cargo_Vacante` TEXT NOT NULL,
  `Descripcion_Perfil` TEXT NOT NULL,
  `Salario_Ofrecido` REAL NOT NULL,
  `ID_Profesion` INTEGER DEFAULT NULL,
  `Fecha_Publicacion` TEXT DEFAULT CURRENT_TIMESTAMP,
  `Estatus` TEXT NOT NULL DEFAULT 'Activa' CHECK(`Estatus` IN ('Activa','Inactiva','Cerrada')),
  FOREIGN KEY(`ID_Empresa`) REFERENCES `empresas`(`ID_Empresa`) ON DELETE CASCADE,
  FOREIGN KEY(`ID_Profesion`) REFERENCES `profesiones`(`ID_Profesion`) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS `postulaciones` (
  `ID_Postulacion` INTEGER PRIMARY KEY,
  `ID_Postulante` INTEGER NOT NULL,
  `ID_Vacante` INTEGER NOT NULL,
  `Fecha_Postulacion` TEXT DEFAULT CURRENT_TIMESTAMP,
  `Estatus` TEXT NOT NULL DEFAULT 'Recibida' CHECK(`Estatus` IN ('Recibida','En Revision','Aceptada','Rechazada')),
  UNIQUE (`ID_Postulante`,`ID_Vacante`),
  FOREIGN KEY(`ID_Postulante`) REFERENCES `postulantes`(`ID_Postulante`) ON DELETE CASCADE,
  FOREIGN KEY(`ID_Vacante`) REFERENCES `vacantes`(`ID_Vacante`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `contratos` (
  `ID_Contrato` INTEGER PRIMARY KEY,
  `ID_Postulacion` INTEGER NOT NULL UNIQUE,
  `Fecha_Contratacion` TEXT NOT NULL,
  `Tipo_Contrato` TEXT NOT NULL CHECK(`Tipo_Contrato` IN ('Un mes','Seis meses','Un año','Indefinido')),
  `Salario_Acordado` REAL NOT NULL,
  `Tipo_Sangre` TEXT DEFAULT NULL,
  `Contacto_Emergencia_Nombre` TEXT DEFAULT NULL,
  `Contacto_Emergencia_Telefono` TEXT DEFAULT NULL,
  `Numero_Cuenta` TEXT DEFAULT NULL,
  `ID_Banco` INTEGER DEFAULT NULL,
  `Estatus` TEXT NOT NULL DEFAULT 'Activo' CHECK(`Estatus` IN ('Activo','Finalizado')),
  FOREIGN KEY(`ID_Postulacion`) REFERENCES `postulaciones`(`ID_Postulacion`),
  FOREIGN KEY(`ID_Banco`) REFERENCES `bancos`(`ID_Banco`) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS `experiencias_laborales` (
  `ID_Experiencia` INTEGER PRIMARY KEY,
  `ID_Postulante` INTEGER NOT NULL,
  `Empresa` TEXT NOT NULL,
  `Cargo_Ocupado` TEXT NOT NULL,
  `Fecha_Inicio` TEXT NOT NULL,
  `Fecha_Fin` TEXT DEFAULT NULL,
  `Descripcion` TEXT DEFAULT NULL,
  FOREIGN KEY(`ID_Postulante`) REFERENCES `postulantes`(`ID_Postulante`) ON DELETE CASCADE
);

-- --- Tablas del Módulo de Nómina ---
CREATE TABLE IF NOT EXISTS `nominas` (
  `ID_Nomina` INTEGER PRIMARY KEY,
  `ID_Empresa` INTEGER NOT NULL,
  `Mes` INTEGER NOT NULL,
  `Anio` INTEGER NOT NULL,
  `Fecha_Generacion` TEXT DEFAULT CURRENT_TIMESTAMP,
  `Estatus` TEXT NOT NULL DEFAULT 'Generada' CHECK(`Estatus` IN ('Generada','Pagada')),
  UNIQUE (`ID_Empresa`,`Mes`,`Anio`),
  FOREIGN KEY(`ID_Empresa`) REFERENCES `empresas`(`ID_Empresa`) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS `recibos` (
  `ID_Recibo` INTEGER PRIMARY KEY,
  `ID_Nomina` INTEGER NOT NULL,
  `ID_Contrato` INTEGER NOT NULL,
  `Salario_Base` REAL NOT NULL,
  `Monto_Deduccion_INCES` REAL NOT NULL,
  `Monto_Deduccion_IVSS` REAL NOT NULL,
  `Comision_Hiring_Group` REAL NOT NULL,
  `Salario_Neto_Pagado` REAL NOT NULL,
  `Fecha_Pago` TEXT DEFAULT NULL,
  FOREIGN KEY(`ID_Nomina`) REFERENCES `nominas`(`ID_Nomina`) ON DELETE CASCADE,
  FOREIGN KEY(`ID_Contrato`) REFERENCES `contratos`(`ID_Contrato`)
);

-- --- Creación de Índices para optimizar búsquedas ---
CREATE INDEX IF NOT EXISTS idx_postulaciones_vacante ON postulaciones(ID_Vacante);
CREATE INDEX IF NOT EXISTS idx_vacantes_empresa ON vacantes(ID_Empresa);
CREATE INDEX IF NOT EXISTS idx_recibos_contrato ON recibos(ID_Contrato);

COMMIT;