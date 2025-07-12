-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 12-07-2025 a las 18:47:39
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `hiring_group`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `areas_conocimiento`
--

CREATE TABLE `areas_conocimiento` (
  `ID_Area_Conocimiento` int(11) NOT NULL,
  `Nombre_Area` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo para agrupar profesiones, ej: Salud, Tecnología.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `bancos`
--

CREATE TABLE `bancos` (
  `ID_Banco` int(11) NOT NULL,
  `Nombre_Banco` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de bancos para los pagos de nómina.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `contratos`
--

CREATE TABLE `contratos` (
  `ID_Contrato` int(11) NOT NULL,
  `ID_Postulacion` int(11) NOT NULL COMMENT 'Un contrato se origina de una única postulación aceptada.',
  `Fecha_Contratacion` date NOT NULL,
  `Tipo_Contrato` enum('Un mes','Seis meses','Un año','Indefinido') NOT NULL,
  `Salario_Acordado` decimal(12,2) NOT NULL,
  `Tipo_Sangre` varchar(5) DEFAULT NULL,
  `Contacto_Emergencia_Nombre` varchar(100) DEFAULT NULL,
  `Contacto_Emergencia_Telefono` varchar(20) DEFAULT NULL,
  `Numero_Cuenta` varchar(30) DEFAULT NULL,
  `ID_Banco` int(11) DEFAULT NULL,
  `Estatus` enum('Activo','Finalizado') NOT NULL DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Formaliza la contratación de un candidato y almacena los detalles del acuerdo.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empresas`
--

CREATE TABLE `empresas` (
  `ID_Empresa` int(11) NOT NULL COMMENT 'Clave primaria y foránea que referencia a Usuarios (relación 1-a-1).',
  `Nombre_Empresa` varchar(150) NOT NULL,
  `RIF` varchar(20) DEFAULT NULL,
  `Sector_Industrial` varchar(100) DEFAULT NULL,
  `Persona_Contacto` varchar(100) DEFAULT NULL,
  `Telefono_Contacto` varchar(20) DEFAULT NULL,
  `Email_Contacto` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Datos específicos de los usuarios que son empresas cliente.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `experiencias_laborales`
--

CREATE TABLE `experiencias_laborales` (
  `ID_Experiencia` int(11) NOT NULL,
  `ID_Postulante` int(11) NOT NULL,
  `Empresa` varchar(150) NOT NULL,
  `Cargo_Ocupado` varchar(150) NOT NULL,
  `Fecha_Inicio` date NOT NULL,
  `Fecha_Fin` date DEFAULT NULL COMMENT 'Nulo si es el trabajo actual.',
  `Descripcion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Historial laboral de los postulantes.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `nominas`
--

CREATE TABLE `nominas` (
  `ID_Nomina` int(11) NOT NULL,
  `ID_Empresa` int(11) NOT NULL,
  `Mes` int(11) NOT NULL,
  `Anio` int(11) NOT NULL,
  `Fecha_Generacion` datetime DEFAULT current_timestamp(),
  `Estatus` enum('Generada','Pagada') NOT NULL DEFAULT 'Generada'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Agrupa los pagos de una empresa en un periodo determinado (corrida de nómina).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `postulaciones`
--

CREATE TABLE `postulaciones` (
  `ID_Postulacion` int(11) NOT NULL,
  `ID_Postulante` int(11) NOT NULL,
  `ID_Vacante` int(11) NOT NULL,
  `Fecha_Postulacion` datetime DEFAULT current_timestamp(),
  `Estatus` enum('Recibida','En Revision','Aceptada','Rechazada') NOT NULL DEFAULT 'Recibida'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Tabla que conecta a los postulantes con las vacantes a las que aplican.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `postulantes`
--

CREATE TABLE `postulantes` (
  `ID_Postulante` int(11) NOT NULL COMMENT 'Clave primaria y foránea que referencia a Usuarios (relación 1-a-1).',
  `Nombres` varchar(100) NOT NULL,
  `Apellidos` varchar(100) NOT NULL,
  `Cedula_Identidad` varchar(20) DEFAULT NULL,
  `Fecha_Nacimiento` date DEFAULT NULL,
  `Direccion` text DEFAULT NULL,
  `Telefono` varchar(20) DEFAULT NULL,
  `ID_Universidad` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Datos específicos de los usuarios que son candidatos.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `profesiones`
--

CREATE TABLE `profesiones` (
  `ID_Profesion` int(11) NOT NULL,
  `Nombre_Profesion` varchar(100) NOT NULL,
  `ID_Area_Conocimiento` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de profesiones que pueden ser requeridas en las vacantes.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `recibos`
--

CREATE TABLE `recibos` (
  `ID_Recibo` int(11) NOT NULL,
  `ID_Nomina` int(11) NOT NULL,
  `ID_Contrato` int(11) NOT NULL,
  `Salario_Base` decimal(12,2) NOT NULL,
  `Monto_Deduccion_INCES` decimal(10,2) NOT NULL COMMENT 'Calculado como el 0.5% del salario.',
  `Monto_Deduccion_IVSS` decimal(10,2) NOT NULL COMMENT 'Calculado como el 1% del salario.',
  `Comision_Hiring_Group` decimal(10,2) NOT NULL COMMENT 'Calculado como el 2% del salario.',
  `Salario_Neto_Pagado` decimal(12,2) NOT NULL,
  `Fecha_Pago` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Detalle del pago individual para cada empleado contratado en una nómina.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `universidades`
--

CREATE TABLE `universidades` (
  `ID_Universidad` int(11) NOT NULL,
  `Nombre_Universidad` varchar(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de universidades de egreso de los postulantes.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `ID_Usuario` int(11) NOT NULL,
  `Email` varchar(100) NOT NULL COMMENT 'Dato de login para todos los usuarios.',
  `Password` varchar(255) NOT NULL COMMENT 'Debe almacenarse de forma encriptada (hash).',
  `Tipo_Usuario` enum('HiringGroup','Empresa','Postulante') NOT NULL COMMENT 'Discriminador para identificar el tipo de usuario.',
  `Fecha_Creacion` datetime DEFAULT current_timestamp(),
  `Estatus` enum('Activo','Inactivo') DEFAULT 'Activo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Tabla base con los datos comunes de todos los usuarios del sistema.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `vacantes`
--

CREATE TABLE `vacantes` (
  `ID_Vacante` int(11) NOT NULL,
  `ID_Empresa` int(11) NOT NULL,
  `Cargo_Vacante` varchar(150) NOT NULL,
  `Descripcion_Perfil` text NOT NULL,
  `Salario_Ofrecido` decimal(12,2) NOT NULL,
  `ID_Profesion` int(11) DEFAULT NULL,
  `Fecha_Publicacion` datetime DEFAULT current_timestamp(),
  `Estatus` enum('Activa','Inactiva','Cerrada') NOT NULL DEFAULT 'Activa'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Ofertas de empleo publicadas por las empresas.';

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `areas_conocimiento`
--
ALTER TABLE `areas_conocimiento`
  ADD PRIMARY KEY (`ID_Area_Conocimiento`),
  ADD UNIQUE KEY `Nombre_Area` (`Nombre_Area`);

--
-- Indices de la tabla `bancos`
--
ALTER TABLE `bancos`
  ADD PRIMARY KEY (`ID_Banco`),
  ADD UNIQUE KEY `Nombre_Banco` (`Nombre_Banco`);

--
-- Indices de la tabla `contratos`
--
ALTER TABLE `contratos`
  ADD PRIMARY KEY (`ID_Contrato`),
  ADD UNIQUE KEY `ID_Postulacion` (`ID_Postulacion`),
  ADD KEY `ID_Banco` (`ID_Banco`);

--
-- Indices de la tabla `empresas`
--
ALTER TABLE `empresas`
  ADD PRIMARY KEY (`ID_Empresa`),
  ADD UNIQUE KEY `RIF` (`RIF`);

--
-- Indices de la tabla `experiencias_laborales`
--
ALTER TABLE `experiencias_laborales`
  ADD PRIMARY KEY (`ID_Experiencia`),
  ADD KEY `ID_Postulante` (`ID_Postulante`);

--
-- Indices de la tabla `nominas`
--
ALTER TABLE `nominas`
  ADD PRIMARY KEY (`ID_Nomina`),
  ADD UNIQUE KEY `ID_Empresa` (`ID_Empresa`,`Mes`,`Anio`) COMMENT 'Solo puede existir una nómina por empresa para un mes y año específico.';

--
-- Indices de la tabla `postulaciones`
--
ALTER TABLE `postulaciones`
  ADD PRIMARY KEY (`ID_Postulacion`),
  ADD UNIQUE KEY `ID_Postulante` (`ID_Postulante`,`ID_Vacante`) COMMENT 'Un postulante solo puede aplicar una vez a la misma vacante.',
  ADD KEY `ID_Vacante` (`ID_Vacante`);

--
-- Indices de la tabla `postulantes`
--
ALTER TABLE `postulantes`
  ADD PRIMARY KEY (`ID_Postulante`),
  ADD UNIQUE KEY `Cedula_Identidad` (`Cedula_Identidad`),
  ADD KEY `ID_Universidad` (`ID_Universidad`);

--
-- Indices de la tabla `profesiones`
--
ALTER TABLE `profesiones`
  ADD PRIMARY KEY (`ID_Profesion`),
  ADD KEY `ID_Area_Conocimiento` (`ID_Area_Conocimiento`);

--
-- Indices de la tabla `recibos`
--
ALTER TABLE `recibos`
  ADD PRIMARY KEY (`ID_Recibo`),
  ADD KEY `ID_Nomina` (`ID_Nomina`),
  ADD KEY `ID_Contrato` (`ID_Contrato`);

--
-- Indices de la tabla `universidades`
--
ALTER TABLE `universidades`
  ADD PRIMARY KEY (`ID_Universidad`),
  ADD UNIQUE KEY `Nombre_Universidad` (`Nombre_Universidad`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`ID_Usuario`),
  ADD UNIQUE KEY `Email` (`Email`);

--
-- Indices de la tabla `vacantes`
--
ALTER TABLE `vacantes`
  ADD PRIMARY KEY (`ID_Vacante`),
  ADD KEY `ID_Empresa` (`ID_Empresa`),
  ADD KEY `ID_Profesion` (`ID_Profesion`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `areas_conocimiento`
--
ALTER TABLE `areas_conocimiento`
  MODIFY `ID_Area_Conocimiento` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `bancos`
--
ALTER TABLE `bancos`
  MODIFY `ID_Banco` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `contratos`
--
ALTER TABLE `contratos`
  MODIFY `ID_Contrato` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `experiencias_laborales`
--
ALTER TABLE `experiencias_laborales`
  MODIFY `ID_Experiencia` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `nominas`
--
ALTER TABLE `nominas`
  MODIFY `ID_Nomina` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `postulaciones`
--
ALTER TABLE `postulaciones`
  MODIFY `ID_Postulacion` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `profesiones`
--
ALTER TABLE `profesiones`
  MODIFY `ID_Profesion` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `recibos`
--
ALTER TABLE `recibos`
  MODIFY `ID_Recibo` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `universidades`
--
ALTER TABLE `universidades`
  MODIFY `ID_Universidad` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `ID_Usuario` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `vacantes`
--
ALTER TABLE `vacantes`
  MODIFY `ID_Vacante` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `contratos`
--
ALTER TABLE `contratos`
  ADD CONSTRAINT `contratos_ibfk_1` FOREIGN KEY (`ID_Postulacion`) REFERENCES `postulaciones` (`ID_Postulacion`),
  ADD CONSTRAINT `contratos_ibfk_2` FOREIGN KEY (`ID_Banco`) REFERENCES `bancos` (`ID_Banco`) ON DELETE SET NULL;

--
-- Filtros para la tabla `empresas`
--
ALTER TABLE `empresas`
  ADD CONSTRAINT `empresas_ibfk_1` FOREIGN KEY (`ID_Empresa`) REFERENCES `usuarios` (`ID_Usuario`) ON DELETE CASCADE;

--
-- Filtros para la tabla `experiencias_laborales`
--
ALTER TABLE `experiencias_laborales`
  ADD CONSTRAINT `experiencias_laborales_ibfk_1` FOREIGN KEY (`ID_Postulante`) REFERENCES `postulantes` (`ID_Postulante`) ON DELETE CASCADE;

--
-- Filtros para la tabla `nominas`
--
ALTER TABLE `nominas`
  ADD CONSTRAINT `nominas_ibfk_1` FOREIGN KEY (`ID_Empresa`) REFERENCES `empresas` (`ID_Empresa`) ON DELETE CASCADE;

--
-- Filtros para la tabla `postulaciones`
--
ALTER TABLE `postulaciones`
  ADD CONSTRAINT `postulaciones_ibfk_1` FOREIGN KEY (`ID_Postulante`) REFERENCES `postulantes` (`ID_Postulante`) ON DELETE CASCADE,
  ADD CONSTRAINT `postulaciones_ibfk_2` FOREIGN KEY (`ID_Vacante`) REFERENCES `vacantes` (`ID_Vacante`) ON DELETE CASCADE;

--
-- Filtros para la tabla `postulantes`
--
ALTER TABLE `postulantes`
  ADD CONSTRAINT `postulantes_ibfk_1` FOREIGN KEY (`ID_Postulante`) REFERENCES `usuarios` (`ID_Usuario`) ON DELETE CASCADE,
  ADD CONSTRAINT `postulantes_ibfk_2` FOREIGN KEY (`ID_Universidad`) REFERENCES `universidades` (`ID_Universidad`) ON DELETE SET NULL;

--
-- Filtros para la tabla `profesiones`
--
ALTER TABLE `profesiones`
  ADD CONSTRAINT `profesiones_ibfk_1` FOREIGN KEY (`ID_Area_Conocimiento`) REFERENCES `areas_conocimiento` (`ID_Area_Conocimiento`) ON DELETE SET NULL;

--
-- Filtros para la tabla `recibos`
--
ALTER TABLE `recibos`
  ADD CONSTRAINT `recibos_ibfk_1` FOREIGN KEY (`ID_Nomina`) REFERENCES `nominas` (`ID_Nomina`) ON DELETE CASCADE,
  ADD CONSTRAINT `recibos_ibfk_2` FOREIGN KEY (`ID_Contrato`) REFERENCES `contratos` (`ID_Contrato`);

--
-- Filtros para la tabla `vacantes`
--
ALTER TABLE `vacantes`
  ADD CONSTRAINT `vacantes_ibfk_1` FOREIGN KEY (`ID_Empresa`) REFERENCES `empresas` (`ID_Empresa`) ON DELETE CASCADE,
  ADD CONSTRAINT `vacantes_ibfk_2` FOREIGN KEY (`ID_Profesion`) REFERENCES `profesiones` (`ID_Profesion`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
