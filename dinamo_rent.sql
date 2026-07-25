-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 25-05-2026 a las 17:10:32
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
-- Base de datos: `dinamo_rent`
--
CREATE DATABASE IF NOT EXISTS `dinamo_rent` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `dinamo_rent`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `alembic_version`
--
-- Creación: 13-04-2026 a las 05:22:30
--

DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `alembic_version`
--

INSERT INTO `alembic_version` (`version_num`) VALUES
('002_add_password_change_column');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `auditoria`
--
-- Creación: 24-03-2026 a las 19:52:53
--

DROP TABLE IF EXISTS `auditoria`;
CREATE TABLE `auditoria` (
  `id` int(11) NOT NULL,
  `usuario` varchar(50) DEFAULT NULL,
  `accion` varchar(100) DEFAULT NULL,
  `mensaje` text DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `autos`
--
-- Creación: 24-03-2026 a las 19:52:53
--

DROP TABLE IF EXISTS `autos`;
CREATE TABLE `autos` (
  `placa` varchar(20) NOT NULL,
  `marca` varchar(80) DEFAULT NULL,
  `modelo` varchar(80) DEFAULT NULL,
  `version` varchar(80) DEFAULT NULL,
  `color` varchar(50) DEFAULT NULL,
  `tipo` varchar(50) DEFAULT NULL,
  `cilindraje` varchar(30) DEFAULT NULL,
  `transmision` varchar(30) DEFAULT NULL,
  `combustible` varchar(30) DEFAULT NULL,
  `no_motor` varchar(80) DEFAULT NULL,
  `no_chasis` varchar(80) DEFAULT NULL,
  `propietario` varchar(150) DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'Disponible',
  `costo_fijo_mensual` decimal(12,2) NOT NULL DEFAULT 0.00,
  `kilometraje` decimal(10,2) NOT NULL DEFAULT 0.00,
  `ubicacion` varchar(150) DEFAULT NULL,
  `tipo_adquisicion` varchar(30) DEFAULT NULL,
  `proximo_aceite` int(11) DEFAULT 0,
  `proximo_frenos` int(11) DEFAULT 0,
  `vencimiento_soat` date DEFAULT NULL,
  `vencimiento_tecnico` date DEFAULT NULL,
  `vencimiento_extintor` date DEFAULT NULL,
  `vencimiento_bateria` date DEFAULT NULL,
  `observaciones` text DEFAULT NULL,
  `fecha_ingreso` date NOT NULL DEFAULT curdate(),
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `autos`
--

INSERT INTO `autos` (`placa`, `marca`, `modelo`, `version`, `color`, `tipo`, `cilindraje`, `transmision`, `combustible`, `no_motor`, `no_chasis`, `propietario`, `estado`, `costo_fijo_mensual`, `kilometraje`, `ubicacion`, `tipo_adquisicion`, `proximo_aceite`, `proximo_frenos`, `vencimiento_soat`, `vencimiento_tecnico`, `vencimiento_extintor`, `vencimiento_bateria`, `observaciones`, `fecha_ingreso`, `created_at`, `updated_at`) VALUES
('EGN754', 'NISSAN', '2019', 'MARCH', 'PLATA', 'Automóvil', '1600 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 83920.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2026-04-04', '2026-04-02', '2026-11-30', '2026-05-20', '', '2023-09-12', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('ELR277', 'RENAULT', '2019', 'LOGAN', 'GRIS COMETA', 'Automóvil', '1600 CC', 'Automática', 'Gasolina', '', '', '', 'Baja', 0.00, 70470.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2027-01-19', '2027-01-19', '2027-01-19', '2027-01-19', '', '2026-01-19', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('FYW252', 'FORD', '2019', 'ECOSPORT', 'AZUL RELAMPAGO', 'Automóvil', '1500 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 96080.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2027-02-20', '2027-02-15', '2026-11-30', '2026-12-30', '', '2026-01-18', '2026-04-21 18:18:51', '2026-04-30 00:00:16'),
('GSN344', 'KIA', '2020', 'CERATO VIB', 'GRIS', 'Automóvil', '1600 CC', 'Automática', 'Gasolina', 'G4FGKE002822', '3KPF241ABLE090308', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 125610.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2026-11-29', '2026-11-26', '2026-04-30', '2026-12-30', '', '2023-04-14', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('JLR976', 'VOLKSWAGEN', '2020', 'VOYAGE', 'BLANCO', 'Automóvil', '1600 CC', 'Automática', 'Gasolina', 'CWS101651', '9BWDL45U5LT103029', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 74100.00, 'OFICINA CARTAGENA', 'Renting', 0, 0, '2026-03-12', '2026-03-06', '2026-05-31', '2027-06-12', '', '2024-08-02', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('JOT174', 'CHEVROLET', '2021', 'BEAT', 'GRIS MERCURIO METALIZADO', 'Automóvil', '1200 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 124225.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2026-10-05', '2026-10-03', '2026-11-30', '2026-08-15', '', '2023-04-13', '2026-04-21 18:18:51', '2026-04-22 20:20:58'),
('JTM256', 'CHEVROLET', '2021', 'ONIX', 'GRIS SATINADO', 'Automóvil', '1000 CC', 'Automática', 'Gasolina', 'L4F20244D461', '9BGEB69K0MG140724', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 138607.00, 'Oficina', 'Subarrendado', 0, 0, '2026-12-25', '2026-12-28', '2027-01-11', '2027-06-06', '', '2023-08-25', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('JWW149', 'RENAULT', '2022', 'KOLEOS', 'GRIS METALIZADO', 'Camioneta', '2500 CC', 'Automática', 'Gasolina', '2TRC707F052923', 'VF1RZG004NC356364', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 51843.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2026-06-26', '2026-06-30', '2026-05-31', '2027-01-19', '', '2024-09-17', '2026-04-21 18:18:51', '2026-04-22 20:31:56'),
('KRZ625', 'CHEVROLET', '2022', 'BEAT', 'PLATA SABLE', 'Automóvil', '1200 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 111153.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2027-02-23', '2027-02-28', '2026-07-31', '2027-03-04', '', '2023-04-13', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('KUR996', 'CHEVROLET', '2022', 'ONIX', 'PLATA SABLE', 'Automóvil', '1000 CC', 'Automática', 'Gasolina', 'L4F*213554035', '9BGEN69K0NG167978', 'DINAMO RENT A CAR S.A.S', 'Baja', 0.00, 86700.00, 'TALLER CHEVROLET', 'Propio', 0, 0, '2026-03-23', '2027-02-28', '2026-04-30', '2026-12-02', '', '2023-08-27', '2026-04-21 18:18:51', '2026-04-26 22:25:16'),
('LCP166', 'MAZDA', '2023', 'CX30', 'MACHINE GREY', 'Camioneta', '2000 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 67473.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2026-04-27', '2027-04-27', '2026-11-30', '2025-02-13', '', '2024-05-02', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('LFZ148', 'KIA', '2023', 'RIO', 'GRIS ACERO', 'Automóvil', '1400 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 59802.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2027-03-03', '2027-04-28', '2026-07-31', '2026-07-12', '', '2026-06-19', '2026-04-21 18:18:51', '2026-04-30 00:00:32'),
('LHT473', 'SUZUKI', '2023', 'SWIFT DZIRE MT', 'GRIS METALICO', 'Automóvil', '1200 CC', 'Automática', 'Gasolina', 'K12MP4320100', 'MBHZF63S4PG229413', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 54794.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2026-07-21', '2027-07-22', '2026-06-18', '2026-08-18', '', '2025-05-20', '2026-04-21 18:18:51', '2026-04-30 00:00:46'),
('LJL987', 'RENAULT', '2023', 'LOGAN', 'GRIS', 'Automóvil', '1600 CC', 'Mecánica', 'Gasolina', 'J759Q161587', '9FB4SR0ESPM438930', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 88525.00, 'Oficina', 'Renting', 0, 0, '2026-10-28', '2028-04-19', '2026-05-31', '2026-12-30', '', '2025-06-03', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('LJR132', 'CHEVROLET', '2023', 'ONIX', 'NEGRO METALIZADO', 'Automóvil', '1000 CC', 'Mecánica', 'Gasolina', 'L4F*220874987', '9BGEB69K0PG104235', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 87525.00, 'OFICINA CARTAGENA', 'Subarrendado', 0, 0, '2026-06-11', '2027-06-29', '2026-04-30', '2026-02-24', '', '2023-05-19', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('LJR247', 'RENAULT', '2023', 'LOGAN', 'GRIS', 'Automóvil', '1600 CC', 'Mecánica', 'Gasolina', 'A812UH14397', '9FB4SREB4PM297705', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 121570.00, 'OFICINA CARTAGENA', 'Subarrendado', 0, 0, '2026-06-30', '2027-06-30', '2026-03-31', '2026-11-03', '', '2023-01-06', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('LLU459', 'SUZUKI', '2023', 'SWIFT DZIRE TAM', 'GRIS METALICO', 'Automóvil', '1200 CC', 'Automática', 'Gasolina', 'K12MP4314799', 'MBHZF63S0PG213063', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 58850.00, 'OFICINA CARTAGENA', 'Subarrendado', 0, 0, '2027-01-14', '2027-01-14', '2026-07-31', '2027-05-09', '', '2024-07-14', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('LLU969', 'SUZUKI', '2023', 'SWIFT DZIRE TAM', 'GRIS METALICO', 'Automóvil', '1200 CC', 'Automática', 'Gasolina', 'K12MP4315034', 'MBHZF63S0PG214049', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 88423.00, 'OFICINA CARTAGENA', 'Renting', 0, 0, '2026-07-08', '2027-07-11', '2026-06-30', '2026-03-31', '', '2024-04-17', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('LNS110', 'CHEVROLET', '2023', 'ONIX', 'ROJO AÑEJO', 'Automóvil', '1000 CC', 'Automática', 'Gasolina', 'L4F*223554643L4F*223554643', '9BGEP69K0PG265996', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 59092.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2026-04-05', '2028-03-31', '2026-05-31', '2026-09-11', '', '2024-11-02', '2026-04-21 18:18:51', '2026-04-22 20:21:28'),
('LNT615', 'CHEVROLET', '2023', 'CAPTIVA PREMIER', 'PLATA AURORA', 'Camioneta', '1500 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 63842.00, 'OFICINA CARTAGENA', 'Propio', 0, 0, '2027-02-23', '2028-02-27', '2026-11-30', '2026-11-30', '', '2023-04-14', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('LQT411', 'VOLKSWAGEN', '2022', 'VOYAGE', 'GRIS PLATINO', 'Automóvil', '1600 CC', 'Automática', 'Gasolina', '', '', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 52110.00, 'OFICINA CARTAGENA', 'Renting', 0, 0, '2026-10-21', '2027-06-10', '2026-07-31', '2026-03-29', '', '2024-09-17', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('NHN166', 'RENAULT', '2023', 'LOGAN', 'GRIS ESTRELLA', 'Automóvil', '1.600', 'Mecánica', 'Gasolina', 'J759Q383702', '9FB4SR0E8VM517559', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 10.00, 'OFICINA CARTAGENA', 'Renting', 0, 0, '2027-02-13', '2031-02-14', '2027-02-14', '2027-02-14', '', '2026-02-20', '2026-04-21 18:18:51', '2026-04-21 18:18:51'),
('NQN513', 'CHEVROLET', '2023', 'TRAVERSE', 'BLANCO GRANIZO', 'Camioneta', '3600 CC', 'Automática', 'Gasolina', 'LFYHPJ227286', 'IGNEV9KW3PJ227286', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 88000.00, 'OFICINA CARTAGENA', 'Leasing', 0, 0, '2026-08-31', '2027-11-23', '2026-03-31', '2026-11-25', '', '2024-12-28', '2026-04-21 18:18:51', '2026-04-30 00:01:10'),
('PDU708', 'RENAULT', '2025', 'KOLEOS', 'BLANCO', 'Camioneta', '2500 CC', 'Automática', 'Gasolina', '2TRC707RF085816', 'VF1RZG011SC404763', 'DINAMO RENT A CAR S.A.S', 'Disponible', 0.00, 18346.00, 'OFICINA CARTAGENA', 'Leasing', 0, 0, '2026-05-08', '2030-05-08', '2026-05-08', '2026-12-08', '', '2025-05-16', '2026-04-21 18:18:51', '2026-04-21 18:18:51');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `clientes`
--
-- Creación: 14-04-2026 a las 14:43:37
--

DROP TABLE IF EXISTS `clientes`;
CREATE TABLE `clientes` (
  `id` int(11) NOT NULL,
  `tipo_doc` varchar(30) DEFAULT NULL,
  `no_doc` varchar(30) DEFAULT NULL,
  `nombres` varchar(100) DEFAULT NULL,
  `apellidos` varchar(100) DEFAULT NULL,
  `nombre_completo` varchar(200) NOT NULL DEFAULT '',
  `celular` varchar(20) DEFAULT NULL,
  `celular2` varchar(20) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `estado_region` varchar(100) DEFAULT NULL,
  `pais` varchar(80) DEFAULT NULL,
  `nacionalidad` varchar(80) DEFAULT NULL,
  `dir_residencia` varchar(200) DEFAULT NULL,
  `dir_temporal` varchar(200) DEFAULT NULL,
  `hotel` varchar(150) DEFAULT NULL,
  `habitacion` varchar(30) DEFAULT NULL,
  `no_licencia` varchar(50) DEFAULT NULL,
  `tipo_licencia` varchar(50) DEFAULT NULL,
  `vencimiento_licencia` date DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'Activo',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `clientes`
--

INSERT INTO `clientes` (`id`, `tipo_doc`, `no_doc`, `nombres`, `apellidos`, `nombre_completo`, `celular`, `celular2`, `email`, `ciudad`, `estado_region`, `pais`, `nacionalidad`, `dir_residencia`, `dir_temporal`, `hotel`, `habitacion`, `no_licencia`, `tipo_licencia`, `vencimiento_licencia`, `estado`, `created_at`, `updated_at`) VALUES
(1, 'Pasaporte', 'C6K9GH4W1', 'LUKAS', 'STAGGE', 'LUKAS STAGGE', '+491774152497', '+491608347220', 'Lukas-stagge@web.de', 'Quedlinburg', 'Saxony-Anhalt', 'Alemania', 'ALEMANA', 'KAHLENBERGWEG 2A, 06485 QUEDLINBURG', 'CASA LI TAYRONA VIA SANTA MARTA-SAN RAFAEL, 470007 EL ZAINO', 'CASA LI TAYRONA VIA SANTA MARTA-SAN RAFAEL, 470007 EL ZAINO', '', 'C6K9GH4W1', 'B1', '2026-01-14', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(2, 'Cédula', '1036672369', 'TATIANA', 'MOSCOTE MARTINEZ', 'TATIANA MOSCOTE MARTINEZ', '+573147046668', '', 'tatis_2810@hotmail.com', 'Itagui', 'Antioquia Department', 'Colombia', 'COLOMBIANA', 'CARRERA 63 33 60', '', 'AIRBNB', '', '1036672369', 'B1', '2027-01-20', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(3, 'Cédula', '73188562', 'MARTIN ALEJANDRO', 'BELTRAN PUCHE', 'MARTIN ALEJANDRO BELTRAN PUCHE', '+573187168962', '', 'mabeltranp81@gmail.com', 'Bogota', 'Cundinamarca Department', 'Colombia', '', 'CRA 54 126 36 T6 A 402', '', '', '', '73188562', 'B1', '2029-02-28', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(4, 'Cédula', '3176830', 'GUSTAVO ADOLFO', 'VASQUEZ BARRIGA', 'GUSTAVO ADOLFO VASQUEZ BARRIGA', '+573106888777', '+573132516075', 'vasmy1411@hotmail.com', 'Bogota', 'Cundinamarca Department', 'Colombia', 'COLOMBIANA', 'CARRERA 69A #25-35 CIUDAD SALITRE', 'CAPRIELLA TORRE 15 APTO 401', 'CAPRIELLA', '', '3176830', 'B1', '2027-01-22', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(5, 'Pasaporte', '119431212', 'JOSE LUIS ', 'DONOSO HENRIQUEZ', 'JOSE LUIS  DONOSO HENRIQUEZ', '+56968537220', '+56959667908', 'conita75@gmail.com', 'Arica', 'Arica y Parinacota Region', 'Chile', 'CHILENA', 'CONCEPCIÓN 37 40 CASA 11', 'EDIFICIO MARINARE C1 A1', '', '', '119431212', 'B1', '2027-01-22', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(6, 'Cédula', '7822867', 'CHRISTOPHER JOSEPH', 'COLQUIT', 'CHRISTOPHER JOSEPH COLQUIT', '+12158139151', '+573005962882', 'cjcolquit@yahoo.com', 'Ambler', 'Pennsylvania', 'Estados Unidos', 'ESTADOUNIDENSE', '659 MARSTEN GREEN CT', 'CARRERA 2 EDIFICIO MURANO CENTRO UNO APTO 1201', '', '', '7822867', 'B1', '2027-01-22', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(7, 'Cédula', '79848984', 'JOHNSON ALBERTO', 'VELANDIA HERNANDEZ', 'JOHNSON ALBERTO VELANDIA HERNANDEZ', '+573232051774', '+573115491829', 'gerente@agllogistica.com', 'Bogota', 'Cundinamarca Department', 'Colombia', 'COLOMBIANA', 'CALLE 19A 9105.', 'CALLE 25 68 BLAS DE LESO', '', '', '79848984', 'B1', '2027-01-22', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(8, 'Cédula', '45548712', 'CAROLINA', 'BLANCO ALMEIDA', 'CAROLINA BLANCO ALMEIDA', '+573103707240', '+573148354316', 'carolinablanco82@hotmail.com', 'Cartagena', 'Bolívar Department', 'Colombia', 'COLOMBIANA', 'BRISAS DE BARLOVENTO APTO 907 TORRE A DANIEL LEMAITRE', 'NA', 'NA', 'NA', '45548712', 'B1', '2027-01-23', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(9, 'Cédula', '88264006', 'OSCAR YESID', 'MEDINA POSADA', 'OSCAR YESID MEDINA POSADA', '+573105809283', '+573015426687', 'oscarmedinap@gmail.com', 'El Encanto', 'Amazonas Department', 'Colombia', 'COLOMBIANA', 'TRAVERSAL 4TA ESTE 61 05  CHAPINERO', 'NA', 'NA', 'NA', '88264006', 'B1', '2027-01-23', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(10, 'Cédula', '52810793', 'IRMA YANIRA', 'CALDERON QUINTERO', 'IRMA YANIRA CALDERON QUINTERO', '+573118706797', '+573213941246', 'irmayacal@hotmail.com', 'Bogota', 'Cundinamarca Department', 'Colombia', 'COLOMBIANA', 'CALLE 78 58 24', 'SANTA MARTA', '', '', '52810793', 'B1', '2027-01-23', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(11, 'Pasaporte', 'N15954206', 'CARLOS', 'RAMIREZ RAMIREZ', 'CARLOS RAMIREZ RAMIREZ', '+524491833351', '+524495869231', 'carlos.ramirez@inegi.org.mx', 'Aguascalientes', 'Aguascalientes', 'Mexico', 'MEJICANA', 'GENTE BUENA 323, AGUAS CALIENTES', 'HOTEL RADIZON', 'HOTEL REDIZON', '', 'N15954206', 'B1', '2027-01-23', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(12, 'Cédula', '79104650', 'GABRIEL', 'BONILLA ACUÑA', 'GABRIEL BONILLA ACUÑA', '573124311534', '573007446746', 'angela.bonilla.13@gmail.com', 'Bogota', 'Cundinamarca Department', 'Colombia', 'COLOMBIANA', 'CARRERA 42B 12 16', 'CALLE 22 10 CIELO MAR', 'SUNNO', '', '79104650', 'B1', '2027-01-23', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(13, 'Pasaporte', 'EN9622275', 'MICHAL KAROL', 'EJDYS', 'MICHAL KAROL EJDYS', '+48792952222', '+48606628212', 'm.k.ejdys@gmail.com', 'VARSOVIA', 'VARSOVIA', 'Polonia', 'POLACA', 'BITWY WARSZAWSKIEJ 1920 R 21/99 	', 'CARRERA 8 #26 29A, MANZANA 26 LOTE 7 SANTA VERONICA', 'AIRBNB', '', 'EN9622275', 'B1', '2027-02-04', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(14, 'Pasaporte', 'A3925278', 'JOSE JOAQUIN', 'MORILLO PAIMAN', 'JOSE JOAQUIN MORILLO PAIMAN', '+593992757000', '+593999423127', 'joaquin@morillos.net', 'TUMBACO', 'PICHINCHA', 'ECUADOR', 'ECUATORIANA', 'PACHO SALAS CASA 4', 'HOTEL PRADO MAR PUERTO COLOMBIA', 'PRADO MAR', '', 'A3925278', 'B1', '2027-02-05', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(15, 'Cédula', '1143946542', 'HEYDI MARIANA', ' VIAFARA QUIÑONES', 'HEYDI MARIANA  VIAFARA QUIÑONES', '+573168302664', '+573122368209', 'mayrafernandamejiabermudez@gmail.com', 'Cali', 'Valle del Cauca', 'Colombia', 'COLOMBIANA', 'CARRERA 44 #13-56', '', 'AIRBNB', '', '1143946542', 'B1', '2027-02-05', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(16, 'Pasaporte', '566393343', 'STEVEN ', 'COHEN', 'STEVEN  COHEN', '3014603517', 'NA', 'sbcohen24@gmail.com', 'NUEVA YORK', 'NUEVA YORK', 'ESTADOS UNIDOS', 'ESTADOUNIDENSE', '17 MEADOW GLEN ROAD', 'HAYAT BOCA GRANDE', 'HAYAT', '', '566393343', 'B1', '2027-02-05', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(17, 'Cédula', '1052070892', 'DEIVI JOSE', 'FERNANDEZ LEGUIA', 'DEIVI JOSE FERNANDEZ LEGUIA', '+573107142370', '+573146114709', 'fernandezdeivi@hotmail.com', 'CARTAGENA', 'BOLÍVAR DEPARTMENT', 'COLOMBIA', 'COLOMBIANA', 'CARRERA 17 60 29 CANAPOTE', 'NA', 'NA', 'NA', '1052070892', 'B1', '2034-02-26', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(18, 'PAS', 'BE154956', 'RAY DOUGLAS', 'TORRES CANO', 'RAY DOUGLAS TORRES CANO', '17862340770', '', 'tdelahoz@hotmail.com', 'FLORIDA', 'FLORIDA', 'UNITED STATES  ', 'COLOMBIANO', '28501 SW152ND AVE LOT159', 'BARRIO ZARAGOCILLA', 'NA', 'NA', 'T625724921400', 'B1', '2030-02-13', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(19, 'C.C.', '1001043812', 'MARIA ALEJANDRA', 'ESCOBAR GAMBA', 'MARIA ALEJANDRA ESCOBAR GAMBA', '+573058574844', '+573057625792', 'michaelssilva43@gmail.com', 'BOGOTA', 'CUNDINAMARCA DEPARTMENT', 'COLOMBIA', 'COLOMBIANA', 'TV 49 #59C - 73', 'HOTEL SUN O BEACH LA BOQUILLA', 'SUN O BEACH', '', '1013677287', '', '2027-02-07', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(20, 'PAS', 'A22695624', 'CLAUDE BENJAMIN', 'JENKINS JR', 'CLAUDE BENJAMIN JENKINS JR', '+16788874009', 'NA', 'claude423@gmail.com', 'ATLANTA', 'GEORGIA', 'ESTADOS UNIDOS', 'ESTADOUNIDENSE', '3155 SEVEN PINES CT UNIT 203', 'AIRBNB', 'AIRBNB', '', 'A22695624', 'B1', '2027-02-07', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(21, 'PAS', 'F57060212', 'HUGO RIGOBERTO', 'BARRERA QUINTANA', 'HUGO RIGOBERTO BARRERA QUINTANA', '+56996011979', '+56981822389', 'quintana.hrb@gmail.com', 'SANTIAGO', 'SANTIAGO METROPOLITAN REGION', 'CHILE', 'CHILENA', 'PIEDRA DEL AGUILA 15 30', 'DECAMERON BOCAGRANDE', 'DECAMERON BOCA GRANDE', '', 'F57060212', 'B1', '2027-02-07', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(22, 'PAS', 'PA512824', 'TOM', 'MIKULANDRA', 'TOM MIKULANDRA', '+573045562345', '+573006548654', 'ninetyeeightdays@hotmail.com', 'CARTAGENA', 'BOLÍVAR DEPARTMENT', 'COLOMBIA', 'ESTADOUNIDENSE', 'MANGA AVENIDA LA ASAMBLEA EDIF SANTANGEL APTO 404', 'NA', 'NA', 'NA', 'PA512824', 'B1', '2027-02-07', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(23, 'PAS', 'L62176079', 'WALTER AIMAR', 'COCHACHI HINOSTROZA', 'WALTER AIMAR COCHACHI HINOSTROZA', '+51968199756', '+51948528325', 'waltercochachi@gmail.com', 'CHANCHAMAYO', 'JUNÍN', 'PERU', 'PERUANA', 'JR LA UNION E 15 PERENE', 'ARIBNB CRESPO', 'ARIBNB CRESPO', '', 'L62176079', 'B1', '2027-02-08', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(24, 'C.C.', '31938784', 'BLANCA ZORAIDA', 'LERMA ABADIA', 'BLANCA ZORAIDA LERMA ABADIA', '+12154001656', '+573162781772', 'philblanca@aol.com', 'CARTAGENA', 'BOLIVAR', 'COLOMBIA', 'COLOMBIANA', 'CONJUNTO CASTELLO APTO 302 TORRE 6', 'CONJUNTO CASTELLO APTO 302 TORRE 6', 'NA', 'NA', '31938784', 'B1', '2027-02-08', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(25, 'PAS', '667586027', 'ALICIA', 'ALCANTAR', 'ALICIA ALCANTAR', '+13257217714', 'NA', '171216aa@gmail.com', 'ABILENE', 'TEXAS', 'ESTADOS UNIDOS', 'ESTADOUNIDENSE', '2218 OLD ANSON RD', 'BARRANQUILLA', 'BARRANQUILLA', '', '667586027', 'B1', '2029-02-14', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(26, 'PAS', 'L64855727', 'NILTON CESAR', 'VALENCIA SILVA', 'NILTON CESAR VALENCIA SILVA', '+51956669506', '+51954960988', 'niltonvalencia36@gmail.com', 'HUANCAYO', 'DEPARTAMENTO DE JUNÍN', 'PERU', 'PERUANA', 'AV HUANCAVELICA 2883 EL TAMBO', 'SANTA MARTA', 'SANTA MARTA', '', 'L64855727', 'B1', '2030-02-12', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(27, 'PAS', 'L75GHXK1C', 'HERMANNUS RUDOLPHUS', 'ZEEDE MERFORT', 'HERMANNUS RUDOLPHUS ZEEDE MERFORT', '+573043222917', '', 'hmerfort@yahoo.de', 'CARTAGENA', 'DEPARTAMENTO DE BOLIVAR', 'COLOMBIA', 'ALEMANA', 'H2 CONDO, CRA 1 N 2 118', 'NA', 'NA', 'NA', 'L75GHXK1C', 'B1', '2030-02-12', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(28, 'PAS', '1713746798', 'FRANCISCO EDUARDO', 'CALDERON BELTRAN', 'FRANCISCO EDUARDO CALDERON BELTRAN', '+593992925768', '+593995004113', 'fcalderon@hotmail.com', 'QUITO', 'PROVINCIA DE PICHINCHA', 'ECUADOR', 'ECUATORIANA', 'SANGOLQUI, INES GANGOTENA Y CHILLANES', '', 'MINKATES', '', '1713746798', 'B1', '2029-02-14', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(29, 'PAS', 'PB1421887', 'JANEZ', 'EGART', 'JANEZ EGART', '+38641386938', '', 'janez.egart@gmail.com', 'LESCE', 'OBČINA LOŠKA DOLINA', 'ESLOVENIA', 'ESLOVACO', ' DOLINA 31A 4248 LESCE', 'SANTA MARTA', '', '', 'PB1421887', 'B1', '2030-02-17', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(30, 'PAS', 'AAL975813', 'GABRIEL CARLOS', 'FERNANDEZ', 'GABRIEL CARLOS FERNANDEZ', '+573057366685', '+5491131016333', 'gabycfz31@hotmail.com', 'BUENOS AIRES', 'BUENOS AIRES', 'ARGENTINA', 'ARGENTINA', 'JOSE INGENIEROS, ALTURA 6051 VICENTE LOPEZ', 'HOTEL OZ LUXURY CALLE 5 #2 - 14', 'HOTEL OZ LUXURY', '', 'AAL975813', 'B1', '2030-02-13', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(31, 'PAS', '149814482', 'STUART', 'SCOTT MCLAREN', 'STUART SCOTT MCLAREN', '+573148301193', '+573023089031', 'paula.murillo193@gmail.com', 'CHELSFIELD', 'ENGLAND', 'REINO UNIDO', 'BRITANICO', 'CR 53AA 38 22  T 3 APT 102  BRISAS DE ARCO IRIS EL SANTUARIO', 'NA', 'NA', 'NA', 'MCLAE812208SS9C', 'B1', '2030-02-13', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(32, 'C.C.', '1047438423', 'STEFY PAOLA', 'VILLA VILORIA', 'STEFY PAOLA VILLA VILORIA', '+573008048609', '', 'svilla@therozpgroup.com', 'CARTAGENA', 'DEPARTAMENTO DE BOLÍVAR', 'COLOMBIA', 'COLOMBIANA', 'MANGA EDIFICIO HENRRY LL', 'NA', 'NA', 'NA', '1047438423', 'B1', '2030-02-13', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(33, 'C.C.', '92533975', 'GERSON DAVID', 'CORPAS ROMERO', 'GERSON DAVID CORPAS ROMERO', '+573218394422', '+573004624539', 'dcorrom@gmail.com', 'CARTAGENA', 'DEPARTAMENTO DE BOLÍVAR', 'COLOMBIA', 'COLOMBIANA', 'CARRERA 17 #2', 'NA', 'NA', 'NA', '92533975', 'B1', '2029-02-22', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(34, 'PAS', 'A64512513', 'DAGMAWI ANDARGIE', 'ADMASSU', 'DAGMAWI ANDARGIE ADMASSU', '+12407336097', '+13015499204', 'dadmassu12@gmail.com', 'PORTLAND', 'OREGON', 'ESTADOS UNIDOS', 'ESTADOUNIDENSE', '875 NE 27TH AVENUE APT 1413', '', 'INTERCONTINENTAL', '', 'A64512513', 'B1', '2027-02-25', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(35, 'PAS', 'BG009515', 'LAURA CAMILA', 'ALVAREZ GOMEZ', 'LAURA CAMILA ALVAREZ GOMEZ', '+15146226672', '+15146224872', 'alvarezcamila1313@gmail.com', 'LA SARRE', 'QUÉBEC', 'CANADÁ', 'COLOMBIANA', '1 392 RUE BERGEVIN', '', '', '', 'BG009515', 'B1', '2031-02-19', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(36, 'PAS', 'B1053645', 'PEDRO STIVEN', 'CASTILLO YAGUAL', 'PEDRO STIVEN CASTILLO YAGUAL', '+5930991549130', '+5930980248690', 'stivenpedro-1993@hotmail.com', 'GUAYAQUIL', 'PROVINCIA DEL GUAYAS', 'ECUADOR', 'ECUATORIANA', 'LURAN CITY ETAPA CAMELIA 10 7', '', '', '', 'B1053645', 'B1', '2029-07-09', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(37, 'C.C.', '53041741', 'GRISELDA JOHANNA', 'NIÑO OLAVE', 'GRISELDA JOHANNA NIÑO OLAVE', '+573164405618', '+573183904260', 'grijohani@gmail.com', 'CARTAGENA', 'DEPARTAMENTO DE BOLÍVAR', 'COLOMBIA', 'COLOMBIANA', 'GETSEMANI CALLE ESPIRITU SANDO 29 183', 'NA', 'NA', 'NA', '53041741', 'B1', '2030-02-13', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(38, 'C.C.', '79391480', 'JAIR', 'DUQUE GIRALDO', 'JAIR DUQUE GIRALDO', '+19174452204', '', 'jerryduque@gmail.com', 'CARTAGENA', 'DEPARTAMENTO DE BOLÍVAR', 'COLOMBIA', 'COLOMBIANA', 'TERRAZAS DE SAN SEBASTIAN TORRE C APTO 419', 'NA', 'NA', 'NA', '79391480', 'B1', '2030-12-31', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(39, 'PAS', '8139962', 'SERGIO', 'DOMINGUEZ SIERRA', 'SERGIO DOMINGUEZ SIERRA', '+34665412252', '+573138371184', 'sdomsie@outlok.com', 'APARTADÓ', 'DEPARTAMENTO DE ANTIOQUIA', 'COLOMBIA', 'ESPAÑOLA', 'CL 99 108 5 CASA ORTIZ', 'NA', 'NA', 'NA', '8139962', 'B1', '2029-05-16', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(40, 'PAS', 'A71995215', 'JEAMIE DIANNA', 'VELAZCO LERMA', 'JEAMIE DIANNA VELAZCO LERMA', '+12155702544', '+573246643854', 'jeamie.vel@gmail.com', 'PHILADELPHIA', 'PENNSYLVANIA', 'ESTADOS UNIDOS', 'ESTADOUNIDENSE', '6026 ALMA ST, PA 19149', 'SERENA DEL MAR APARTAMENTO CASTELLO TORRE C APTO 302', '', '', 'A71995215', 'B1', '2029-10-17', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(41, 'PAS', '44435261', 'DAVID', 'RUDOLF', 'DAVID RUDOLF', '+420778007750', '+420777563523', 'dilnarudy@gmail.com', 'CHOMUTOV', 'ÚSTECKÝ KRAJ', 'CHEQUIA', 'CHECA', 'NA BORKU 1622 43111, JIRKOV', 'TRAVELLERS ORANGE CARRERA 10 #5A 15 CASTILLO GRANDE', 'TRAVELLERS ORANGE', '', '44435261', 'B1', '2030-06-19', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(42, 'PAS', 'E0529243', 'JEFREY ARIEL', 'ORTEZ ALVAREZ', 'JEFREY ARIEL ORTEZ ALVAREZ', '+50496385545', '+50499026116', 'ariel_ortez_13@hotmail.com', 'TEGUCIGALPA', 'DEPARTAMENTO DE FRANCISCO MORAZÁN', 'HONDURAS', 'HONDUREÑA', 'RESIDENCIAL SAN JUAN CALLE PRINCIPAL APT COLOR OCRE', 'NA', 'NA', 'NA', 'E0529243', 'B1', '2027-02-27', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54'),
(43, 'C.C.', '42779743', 'LINA LORENA', 'ECHEVERRI ROJAS', 'LINA LORENA ECHEVERRI ROJAS', '+573007496852', '+573156333939', 'linalorenaecheverri@gmail.com', 'MEDELLÍN', 'ANTIOQUIA', 'COLOMBIA', 'COLOMBIANA', 'CALLE 23A  65 B 11 TRINIDAD', 'PALMETO 1 CARTAGENA', 'PALMETO 1 CARTAGENA', '', '42779743', 'B1', '2027-02-27', 'Activo', '2026-04-21 18:16:54', '2026-04-21 18:16:54');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `comparendos`
--
-- Creación: 14-04-2026 a las 14:43:37
--

DROP TABLE IF EXISTS `comparendos`;
CREATE TABLE `comparendos` (
  `id` int(11) NOT NULL,
  `placa` varchar(20) NOT NULL,
  `fecha_infraccion` date NOT NULL,
  `hora_infraccion` time NOT NULL,
  `monto` decimal(12,2) NOT NULL DEFAULT 0.00,
  `id_renta` int(11) DEFAULT NULL,
  `id_cliente` int(11) DEFAULT NULL,
  `estado` varchar(20) DEFAULT 'Pendiente',
  `observaciones` text DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `configuracion`
--
-- Creación: 24-03-2026 a las 19:52:53
--

DROP TABLE IF EXISTS `configuracion`;
CREATE TABLE `configuracion` (
  `clave` varchar(100) NOT NULL,
  `valor` text DEFAULT NULL,
  `tipo` varchar(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `gastos`
--
-- Creación: 14-04-2026 a las 14:43:37
--

DROP TABLE IF EXISTS `gastos`;
CREATE TABLE `gastos` (
  `id` int(11) NOT NULL,
  `placa` varchar(20) DEFAULT NULL,
  `fecha` date NOT NULL,
  `categoria` varchar(50) NOT NULL,
  `descripcion` varchar(200) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `comprobante` varchar(50) DEFAULT NULL,
  `usuario` varchar(50) DEFAULT 'Sistema',
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inspecciones`
--
-- Creación: 25-03-2026 a las 20:32:40
--

DROP TABLE IF EXISTS `inspecciones`;
CREATE TABLE `inspecciones` (
  `id` int(11) NOT NULL,
  `id_renta` int(11) NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `kilometraje` decimal(10,2) NOT NULL,
  `nivel_gasolina` varchar(20) NOT NULL,
  `limpieza` varchar(50) DEFAULT 'Limpio',
  `tiene_repuesto` tinyint(1) DEFAULT 1,
  `tiene_gato_cruceta` tinyint(1) DEFAULT 1,
  `tiene_kit_carretera` tinyint(1) DEFAULT 1,
  `tiene_documentos` tinyint(1) DEFAULT 1,
  `danos_carroceria` text DEFAULT NULL,
  `observaciones` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mantenimiento`
--
-- Creación: 29-03-2026 a las 04:51:51
--

DROP TABLE IF EXISTS `mantenimiento`;
CREATE TABLE `mantenimiento` (
  `id` int(11) NOT NULL,
  `placa` varchar(20) DEFAULT NULL,
  `pieza_varias_tipo` varchar(80) DEFAULT NULL,
  `pieza_varias_fecha` date DEFAULT NULL,
  `pieza_varias_desc` varchar(250) DEFAULT NULL,
  `pieza_varias_obs` text DEFAULT NULL,
  `cost_varios` decimal(12,2) DEFAULT 0.00,
  `km_proximo_cambio_aceite` int(11) DEFAULT 0,
  `total_mantenimiento` decimal(12,2) DEFAULT 0.00,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mantenimiento_vehiculos`
--
-- Creación: 14-04-2026 a las 14:43:37
--

DROP TABLE IF EXISTS `mantenimiento_vehiculos`;
CREATE TABLE `mantenimiento_vehiculos` (
  `id` int(11) NOT NULL,
  `placa` varchar(20) DEFAULT NULL,
  `pieza_varias_tipo` varchar(80) DEFAULT NULL,
  `pieza_varias_fecha` date DEFAULT NULL,
  `pieza_varias_desc` varchar(250) DEFAULT NULL,
  `pieza_varias_obs` text DEFAULT NULL,
  `cost_varios` decimal(12,2) DEFAULT 0.00,
  `km_proximo_cambio_aceite` int(11) DEFAULT 0,
  `total_mantenimiento` decimal(12,2) DEFAULT 0.00,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos`
--
-- Creación: 14-04-2026 a las 14:43:37
--

DROP TABLE IF EXISTS `pagos`;
CREATE TABLE `pagos` (
  `id` int(11) NOT NULL,
  `id_renta` int(11) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `monto` decimal(12,2) NOT NULL,
  `metodo_pago` varchar(50) NOT NULL,
  `concepto` varchar(80) NOT NULL,
  `observaciones` text DEFAULT NULL,
  `usuario` varchar(50) DEFAULT 'Sistema',
  `updated_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rentas`
--
-- Creación: 24-03-2026 a las 19:52:53
--

DROP TABLE IF EXISTS `rentas`;
CREATE TABLE `rentas` (
  `id` int(11) NOT NULL,
  `placa` varchar(20) DEFAULT NULL,
  `id_cliente` int(11) DEFAULT NULL,
  `nombre_cliente` varchar(200) DEFAULT NULL,
  `no_licencia` varchar(50) DEFAULT NULL,
  `nacionalidad` varchar(80) DEFAULT NULL,
  `fecha_recogida` date DEFAULT NULL,
  `hora_recogida` time DEFAULT NULL,
  `ubicacion_recogida` varchar(200) DEFAULT NULL,
  `fecha_retorno` date DEFAULT NULL,
  `hora_retorno` time DEFAULT NULL,
  `ubicacion_retorno` varchar(200) DEFAULT NULL,
  `dias_calculados` int(11) DEFAULT 0,
  `horas_extras` int(11) DEFAULT 0,
  `valor_dia` decimal(12,2) DEFAULT 0.00,
  `valor_hora_extra` decimal(12,2) DEFAULT 0.00,
  `valor_dia_extra` decimal(12,2) DEFAULT 0.00,
  `costo_lavado` decimal(12,2) DEFAULT 0.00,
  `costo_silla` decimal(12,2) DEFAULT 0.00,
  `costo_retorno` decimal(12,2) DEFAULT 0.00,
  `costo_domicilio` decimal(12,2) DEFAULT 0.00,
  `costo_cables` decimal(12,2) DEFAULT 0.00,
  `costo_inversor` decimal(12,2) DEFAULT 0.00,
  `descuento` decimal(12,2) DEFAULT 0.00,
  `subtotal` decimal(12,2) DEFAULT 0.00,
  `impuestos` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) DEFAULT 0.00,
  `abono` decimal(12,2) DEFAULT 0.00,
  `saldo_pendiente` decimal(12,2) DEFAULT 0.00,
  `estado` varchar(30) NOT NULL DEFAULT 'Activo',
  `observaciones` text DEFAULT NULL,
  `fecha_devolucion_real` date DEFAULT NULL,
  `hora_devolucion_real` time DEFAULT NULL,
  `km_final` varchar(20) DEFAULT NULL,
  `tanque_final` varchar(20) DEFAULT NULL,
  `km_salida` decimal(10,2) DEFAULT 0.00,
  `tanque_salida` varchar(20) DEFAULT 'Lleno',
  `id_reserva` int(11) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `reservas`
--
-- Creación: 14-04-2026 a las 14:43:37
--

DROP TABLE IF EXISTS `reservas`;
CREATE TABLE `reservas` (
  `id` int(11) NOT NULL,
  `id_cliente` int(11) DEFAULT NULL,
  `nombre_cliente` varchar(200) DEFAULT NULL,
  `nacionalidad` varchar(80) DEFAULT NULL,
  `categoria_vehiculo` varchar(50) DEFAULT NULL,
  `placa_asignada` varchar(20) DEFAULT NULL,
  `fecha_recogida` date DEFAULT NULL,
  `hora_recogida` time DEFAULT NULL,
  `ubicacion_recogida` varchar(200) DEFAULT NULL,
  `fecha_retorno` date DEFAULT NULL,
  `hora_retorno` time DEFAULT NULL,
  `ubicacion_retorno` varchar(200) DEFAULT NULL,
  `dias_calculados` int(11) DEFAULT 0,
  `horas_extras` int(11) DEFAULT 0,
  `valor_dia` decimal(12,2) DEFAULT 0.00,
  `valor_hora_adic` decimal(12,2) DEFAULT 0.00,
  `abono` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) DEFAULT 0.00,
  `observaciones` text DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'Confirmada',
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--
-- Creación: 16-04-2026 a las 03:21:51
--

DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `nombre` varchar(150) DEFAULT NULL,
  `rol` varchar(50) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `intentos_fallidos` int(11) NOT NULL DEFAULT 0,
  `ultimo_acceso` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `debe_cambiar_password` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `username`, `password`, `nombre`, `rol`, `email`, `activo`, `intentos_fallidos`, `ultimo_acceso`, `created_at`, `updated_at`, `debe_cambiar_password`) VALUES
(1, 'admin', '7f65f50115c3a52ae9ff95a6803c626bc16da52ecf216f16c4ad93b82d0f7129:7e575422a71f4819fb0cb08a3da565bd', 'Administrador Principal', 'Administrador', NULL, 1, 0, '2026-05-03 14:05:56', '2026-03-24 14:52:53', '2026-05-03 14:05:56', 0);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Indices de la tabla `auditoria`
--
ALTER TABLE `auditoria`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_auditoria_fecha` (`fecha`),
  ADD KEY `idx_auditoria_usuario` (`usuario`);

--
-- Indices de la tabla `autos`
--
ALTER TABLE `autos`
  ADD PRIMARY KEY (`placa`),
  ADD KEY `idx_autos_estado` (`estado`);

--
-- Indices de la tabla `clientes`
--
ALTER TABLE `clientes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `no_doc` (`no_doc`),
  ADD KEY `idx_clientes_doc` (`no_doc`),
  ADD KEY `idx_clientes_nombre` (`nombre_completo`);

--
-- Indices de la tabla `comparendos`
--
ALTER TABLE `comparendos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_renta` (`id_renta`),
  ADD KEY `id_cliente` (`id_cliente`);

--
-- Indices de la tabla `configuracion`
--
ALTER TABLE `configuracion`
  ADD PRIMARY KEY (`clave`);

--
-- Indices de la tabla `gastos`
--
ALTER TABLE `gastos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_gastos_placa` (`placa`);

--
-- Indices de la tabla `inspecciones`
--
ALTER TABLE `inspecciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_renta` (`id_renta`);

--
-- Indices de la tabla `mantenimiento`
--
ALTER TABLE `mantenimiento`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `mantenimiento_vehiculos`
--
ALTER TABLE `mantenimiento_vehiculos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_mant_placa` (`placa`);

--
-- Indices de la tabla `pagos`
--
ALTER TABLE `pagos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_renta` (`id_renta`);

--
-- Indices de la tabla `rentas`
--
ALTER TABLE `rentas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_renta_cliente` (`id_cliente`),
  ADD KEY `idx_rentas_estado` (`estado`),
  ADD KEY `idx_rentas_placa` (`placa`),
  ADD KEY `idx_rentas_fechas` (`fecha_recogida`,`fecha_retorno`);

--
-- Indices de la tabla `reservas`
--
ALTER TABLE `reservas`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `auditoria`
--
ALTER TABLE `auditoria`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `clientes`
--
ALTER TABLE `clientes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=45;

--
-- AUTO_INCREMENT de la tabla `comparendos`
--
ALTER TABLE `comparendos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `gastos`
--
ALTER TABLE `gastos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `inspecciones`
--
ALTER TABLE `inspecciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `mantenimiento`
--
ALTER TABLE `mantenimiento`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `mantenimiento_vehiculos`
--
ALTER TABLE `mantenimiento_vehiculos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pagos`
--
ALTER TABLE `pagos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `rentas`
--
ALTER TABLE `rentas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `reservas`
--
ALTER TABLE `reservas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `comparendos`
--
ALTER TABLE `comparendos`
  ADD CONSTRAINT `comparendos_ibfk_1` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_10` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_11` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_12` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_13` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_14` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_15` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_16` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_17` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_18` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_19` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_2` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_20` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_21` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_22` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_23` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_24` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_25` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_26` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_27` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_28` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_29` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_3` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_30` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_31` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_32` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_33` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_34` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_35` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_36` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_37` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_38` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_39` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_4` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_40` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_41` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_42` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_43` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_44` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_45` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_46` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_47` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_48` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_49` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_5` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_50` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_51` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_52` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_53` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_54` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_55` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_56` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_57` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_58` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_59` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_6` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_60` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_61` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_62` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_63` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_64` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_65` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_66` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_67` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_68` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_69` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_7` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_70` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_71` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_72` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_73` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_74` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_75` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_76` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_77` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_78` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_8` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `comparendos_ibfk_9` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `inspecciones`
--
ALTER TABLE `inspecciones`
  ADD CONSTRAINT `inspecciones_ibfk_1` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `pagos`
--
ALTER TABLE `pagos`
  ADD CONSTRAINT `pagos_ibfk_1` FOREIGN KEY (`id_renta`) REFERENCES `rentas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `rentas`
--
ALTER TABLE `rentas`
  ADD CONSTRAINT `fk_renta_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`),
  ADD CONSTRAINT `fk_renta_placa` FOREIGN KEY (`placa`) REFERENCES `autos` (`placa`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
