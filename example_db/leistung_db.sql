-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: db
-- Generation Time: Mar 26, 2023 at 07:34 PM
-- Server version: 10.11.2-MariaDB-1:10.11.2+maria~ubu2204
-- PHP Version: 8.1.17

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `leistungs_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `leistungstag`
--

CREATE TABLE `leistungstag` (
  `key` int(11) NOT NULL,
  `location` int(11) NOT NULL,
  `date` date NOT NULL,
  `poll_id` bigint(20) NOT NULL,
  `venue_id` bigint(20) NOT NULL,
  `type` smallint(6) NOT NULL,
  `closed` bit(1) NOT NULL DEFAULT b'0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `leistungstag`
--

INSERT INTO `leistungstag` (`key`, `location`, `date`, `poll_id`, `venue_id`, `type`, `closed`) VALUES
(1, 5, '2022-01-25', 0, 0, 1, b'1'),
(3, 6, '2022-02-01', 0, 0, 1, b'1'),
(5, 7, '2022-02-08', 0, 0, 1, b'1'),
(6, 8, '2022-02-15', 0, 0, 1, b'1'),
(7, 10, '2022-02-22', 0, 0, 1, b'1'),
(8, 11, '2022-03-01', 0, 0, 1, b'1'),
(9, 12, '2022-03-08', 0, 0, 1, b'1'),
(10, 13, '2022-03-15', 0, 0, 1, b'1'),
(11, 14, '2022-03-22', 0, 0, 1, b'1'),
(12, 15, '2022-03-29', 0, 0, 1, b'1'),
(13, 16, '2022-04-05', 0, 0, 1, b'1'),
(14, 17, '2022-04-12', 0, 0, 1, b'1'),
(15, 18, '2022-04-19', 0, 0, 1, b'1'),
(16, 19, '2022-04-26', 0, 0, 1, b'1'),
(17, 20, '2022-05-03', 0, 0, 1, b'1'),
(18, 21, '2022-05-10', 0, 0, 1, b'1'),
(19, 22, '2022-05-17', 0, 0, 1, b'1'),
(20, 23, '2022-05-24', 0, 0, 1, b'1'),
(21, 24, '2022-05-31', 0, 0, 1, b'1'),
(22, 26, '2022-06-07', 0, 0, 1, b'1'),
(23, 27, '2022-06-14', 0, 0, 1, b'1'),
(24, 28, '2022-06-21', 0, 0, 1, b'1'),
(25, 30, '2022-06-28', 0, 0, 1, b'1'),
(26, 31, '2022-07-05', 0, 0, 1, b'1'),
(27, 32, '2022-07-12', 0, 0, 1, b'1'),
(28, 33, '2022-07-19', 0, 0, 1, b'1'),
(29, 34, '2022-07-26', 0, 0, 1, b'1'),
(30, 36, '2022-08-02', 0, 0, 1, b'1'),
(31, 37, '2022-08-09', 0, 0, 1, b'1'),
(32, 38, '2022-08-16', 0, 0, 1, b'1'),
(33, 39, '2022-08-23', 0, 0, 1, b'1'),
(34, 40, '2022-08-30', 0, 0, 1, b'1'),
(35, 41, '2022-09-06', 0, 0, 1, b'1'),
(36, 42, '2022-09-13', 0, 0, 1, b'1'),
(37, 43, '2022-09-20', 0, 0, 1, b'1'),
(38, 44, '2022-09-27', 0, 0, 1, b'1'),
(39, 45, '2022-10-04', 0, 0, 1, b'1'),
(40, 46, '2022-10-11', 0, 0, 1, b'1'),
(44, 9, '2022-02-16', 0, 0, 3, b'1'),
(45, 25, '2022-06-06', 0, 0, 3, b'1'),
(46, 49, '2022-10-11', 0, 0, 2, b'1'),
(47, 50, '2022-10-04', 0, 0, 2, b'1'),
(49, 53, '2022-10-25', 732, 731, 1, b'1'),
(50, 56, '2022-11-01', 746, 745, 1, b'1'),
(51, 59, '2022-11-08', 753, 752, 1, b'1'),
(52, 61, '2022-11-15', 771, 770, 1, b'1'),
(54, 65, '2022-11-22', 796, 795, 1, b'1'),
(55, 29, '2022-06-24', 0, 0, 3, b'1'),
(56, 47, '2022-10-18', 0, 0, 1, b'1'),
(57, 87, '2022-11-29', 830, 829, 1, b'1'),
(58, 90, '2022-12-06', 847, 846, 1, b'1'),
(59, 91, '2022-12-13', 862, 861, 1, b'1'),
(60, 92, '2022-12-20', 878, 877, 1, b'1'),
(61, 100, '2022-12-27', 899, 898, 1, b'1'),
(62, 98, '2023-01-03', 912, 911, 1, b'1'),
(63, 103, '2023-01-10', 936, 935, 1, b'1'),
(64, 13, '2023-01-17', 968, 967, 1, b'1'),
(65, 101, '2023-01-24', 970, 969, 1, b'1'),
(66, 113, '2023-01-31', 980, 979, 1, b'0'),
(67, 114, '2023-02-07', 988, 987, 1, b'0'),
(68, 85, '2023-02-14', 1005, 1004, 1, b'0'),
(69, 125, '2023-02-21', 1012, 1011, 1, b'0'),
(70, 97, '2023-02-28', 1039, 1038, 1, b'0'),
(71, 127, '2023-03-07', 1056, 1055, 1, b'0'),
(72, 129, '2023-03-14', 1070, 1069, 1, b'0'),
(73, 84, '2023-03-21', 1099, 1098, 1, b'0');

-- --------------------------------------------------------

--
-- Table structure for table `locations`
--

CREATE TABLE `locations` (
  `key` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `google-place-id` text NOT NULL,
  `visited` bit(1) NOT NULL DEFAULT b'0',
  `address` text NOT NULL,
  `phone` varchar(255) DEFAULT NULL,
  `url` varchar(255) NOT NULL,
  `lng` double(9,6) NOT NULL,
  `lat` double(9,6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `locations`
--

INSERT INTO `locations` (`key`, `name`, `google-place-id`, `visited`, `address`, `phone`, `url`, `lng`, `lat`) VALUES
(2, 'Cafe Phönixhof', 'ChIJ5UvV55IHbUcRMq6el31MzZI', b'0', 'Neustiftgasse 55, 1070 Wien, Österreich', '+43 699 17331072', 'https://g.page/Phoenixhof?share', 16.349794, 48.205268),
(3, 'Hofkneipe', 'ChIJ-V7XVyaYc0cRvWHfZO7pBSk', b'0', 'Ludlgasse 16, 4020 Linz, Österreich', '+43 732 771188', 'https://maps.google.com/?cid=2956025940542448061', 14.300611, 48.312142),
(4, 'Golden Pub', 'ChIJgxV7OdWZc0cRLnHvxuahDv8', b'0', 'Jahnstraße 9, 4040 Linz, Österreich', '+43 732 732097', 'https://maps.google.com/?cid=18378805141897703726', 14.282590, 48.312924),
(5, 'Chelsea Pub', 'ChIJPUxAF4SXc0cRroF8A6rKvgg', b'1', 'Domgasse 5, 4020 Linz, Österreich', '+43 732 779409', 'https://maps.google.com/?cid=630163829430190510', 14.288023, 48.304780),
(6, 'stadtliebe', 'ChIJk1NadIWXc0cRKiCtqbbQBTg', b'1', 'Landstraße 31, 4020 Linz, Österreich', '+43 732 770605', 'https://maps.google.com/?cid=4036862123956838442', 14.290209, 48.302237),
(7, 'Gösserkeller', 'ChIJU91lHYSXc0cRx27qE7Y3ORs', b'1', 'Pfarrgasse 8, 4020 Linz, Österreich', '+43 699 10891110', 'https://maps.google.com/?cid=1961660367854268103', 14.287853, 48.305611),
(8, 'Cafe Strom', 'ChIJGT-7boCXc0cRQjXbCI4gYFA', b'1', 'Kirchengasse 4, 4040 Linz, Österreich', '+43 732 731209205', 'https://maps.google.com/?cid=5791664915204486466', 14.284583, 48.310119),
(9, 'Gemeinde Hinterstoder', 'ChIJH-DHUJtmcUcRsFvv2z4X8j4', b'1', 'Gemeinde Hinterstoder, Hinterstoder, Österreich', NULL, 'https://maps.google.com/?q=Gemeinde+Hinterstoder,+Hinterstoder,+%C3%96sterreich&ftid=0x4771669b50c7e01f:0x3ef2173edbef5bb0', 14.156330, 47.699980),
(10, 'Jack the Ripperl', 'ChIJg4_kToSXc0cRD8jsvm6MdMc', b'1', 'Landstraße 11, 4020 Linz, Österreich', '+43 732 239899', 'https://maps.google.com/?cid=14372266718123575311', 14.288770, 48.303822),
(11, 'DAO', 'ChIJ6Un2FoOXc0cRr_nKbeIWkmY', b'1', 'Klammstraße 20a, 4020 Linz, Österreich', '+43 676 3794900', 'https://maps.google.com/?cid=7390995100228843951', 14.283000, 48.302738),
(12, 'Leberkas-Pepi Linz Hauptbahnhof', 'ChIJ942_IpaXc0cRBGtWeBAUa0E', b'1', 'Bahnhofpl. 3-6, 4020 Linz, Österreich', '+43 650 2435739', 'https://maps.google.com/?cid=4713883495944317700', 14.291190, 48.290533),
(13, 'Alte Welt', 'ChIJSyTkT4GXc0cRZgYZvTlyitE', b'1', 'Hauptpl. 4, 4020 Linz, Österreich', '+43 732 770053', 'https://maps.google.com/?cid=15099006293024245350', 14.286654, 48.306482),
(14, 'Glorious Bastards Linz', 'ChIJ_TFte4OXc0cRH_7XjWM08Rs', b'1', 'Promenade 25, 4020 Linz, Österreich', '+43 732 299800', 'https://maps.google.com/?cid=2013448110597471775', 14.285155, 48.302864),
(15, 'Barok Belgie', 'ChIJF5KL2IOXc0cR2yVRfvsh2GI', b'1', 'Hofgasse 14, 4020 Linz, Österreich', '+43 732 273878', 'https://maps.google.com/?cid=7122480174726194651', 14.284799, 48.305859),
(16, 'Die Donauwirtinnen', 'ChIJYS7oE3-Xc0cRwnhcbqap5Jk', b'1', 'Webergasse 2, 4040 Linz, Österreich', '+43 732 737706', 'https://maps.google.com/?cid=11089174714774223042', 14.279226, 48.308352),
(17, 'Die Wirtsleut im Leopoldistüberl', 'ChIJDW19za2Xc0cRLGpfHNDZ-nw', b'1', 'Adlergasse 6, 4020 Linz, Österreich', '+43 732 777242', 'https://maps.google.com/?cid=9005749892733168172', 14.287179, 48.306619),
(18, 'Zur Liesl', 'ChIJidVHJkSZc0cRVHiS2hQNWPQ', b'1', 'Peter-Behrens-Platz 1, 4020 Linz, Österreich', '+43 664 800221180', 'https://maps.google.com/?cid=17606837126422493268', 14.298564, 48.311904),
(19, 'The Old Dubliner', 'ChIJc3Rl_IOXc0cRP72ceq9mp7o', b'1', 'Hauptpl. 15-16, 4020 Linz, Österreich', '+43 732 917050', 'https://maps.google.com/?cid=13449831716027678015', 14.285816, 48.305557),
(20, 'Urfahrmarkt', 'ChIJv0PpSCqYc0cRJ9yoZPWTLG8', b'1', 'Urfahrmarkt, 4040 Linz, Österreich', NULL, 'https://maps.google.com/?q=Urfahrmarkt,+4040+Linz,+%C3%96sterreich&ftid=0x4773982a48e943bf:0x6f2c93f564a8dc27', 14.288896, 48.312662),
(21, 'Biergartl an der Donau in Linz Urfahr', 'ChIJnY7c1YGXc0cRJlOIPruBfTk', b'1', 'Fischergasse 17, 4040 Linz, Österreich', '+43 664 6417619', 'https://maps.google.com/?cid=4142609873458713382', 14.281751, 48.308582),
(22, 'Gallanderstüberl', 'ChIJ0zZYvSSYc0cRgUtiu0lXUEk', b'1', 'Gallanderstraße 3, 4020 Linz, Österreich', '+43 732 205017', 'https://maps.google.com/?cid=5282818337093602177', 14.305951, 48.317276),
(23, 'Schlossbrauerei Weinberg Erste oö. Gasthausbrauerei', 'ChIJhyzSWuQJc0cRiWMkDpZiH7Q', b'1', 'Weinberg 2, 4292 Kefermarkt, Österreich', '+43 7947 7111', 'https://maps.google.com/?cid=12979201047726941065', 14.539495, 48.448537),
(24, 'Salonschiff Fräulein Florentine', 'ChIJdx7wEiqYc0cRAK0G0kAluWc', b'1', '4040 Linz, Österreich', NULL, 'https://maps.google.com/?cid=7474046016929836288', 14.288256, 48.311423),
(25, 'Michaeli Bräu', 'ChIJu84Bp2qXc0cRNjBhPLkTlRY', b'1', 'Lugwiesstraße 40, 4060 Leonding, Österreich', NULL, 'https://maps.google.com/?cid=1627228526667182134', 14.247520, 48.296301),
(26, 'PAULS steak & veggi Linz', 'ChIJ_fshKZuXc0cRY-O-6j-7rL0', b'1', 'Domplatz 3, 4020 Linz, Österreich', '+43 732 783338', 'https://maps.google.com/?cid=13667504852358325091', 14.287225, 48.300272),
(27, 'Gasthaus Zum Schiefen Apfelbaum', 'ChIJR9Z8QriXc0cR15JfIYm0Jqg', b'1', 'Hanuschstraße 26, 4020 Linz, Österreich', '+43 732 660380', 'https://maps.google.com/?cid=12116570348550329047', 14.293566, 48.281294),
(28, 'Sputnik Rockcafe', 'ChIJZ4CaH4eXc0cRd9PffZY_0z8', b'1', 'Untere Donaulände 16, 4020 Linz, Österreich', '+43 660 1611209', 'https://maps.google.com/?cid=4599089560064873335', 14.289862, 48.308034),
(29, 'Wochenmarkt', 'ChIJmxLTWuqbc0cRU83uUpXkRck', b'1', 'Marktpl. 5-2, 4100 Ottensheim, Österreich', NULL, 'https://maps.google.com/?cid=14503249505009192275', 14.176252, 48.331522),
(30, 'Rox Musicbar & Grill Linz | Burger & American Kitchen', 'ChIJ_QZUKoSXc0cRNp4YiXzzdzQ', b'1', 'Graben 18, 4020 Linz, Österreich', '+43 732 210318', 'https://maps.google.com/?cid=3780758128402406966', 14.289844, 48.305200),
(31, 'HEMINGWAY\'S COCKTAIL&MUSIC BAR', 'ChIJjS3MH4SXc0cRvUvyHkzUrF4', b'1', 'Domgasse 8, 4020 Linz, Österreich', '+43 650 6101820', 'https://maps.google.com/?cid=6822060958961257405', 14.288337, 48.305454),
(32, 'SanTelmo', 'ChIJbxTMHtGnc0cRqwz9jsq3hJ0', b'1', 'Softwarepark 30, 4232 Hagenberg im Mühlkreis, Österreich', '+43 664 99901558', 'https://maps.google.com/?cid=11350399041490717867', 14.514741, 48.370271),
(33, 'SANDBURG', 'ChIJb-cJ1ymYc0cR1ydGPsATqlc', b'1', 'Untere Donaulände 5, 4020 Linz, Österreich', '+43 664 2512600', 'https://maps.google.com/?cid=6316883143739975639', 14.291962, 48.310235),
(34, 'Ristorante Pizzeria La Ruffa Donaulände (ehemals Amici)', 'ChIJ1TQ3WSqYc0cRPeLEGGJmwQU', b'1', 'Verlängerte Kirchengasse 15, 4020 Linz, Österreich', '+43 650 8855701', 'https://maps.google.com/?cid=414725212203180605', 14.287164, 48.312401),
(36, 'Cafe Bar Aquarium', 'ChIJeUoXSEeXc0cRffsS6dbrBMQ', b'1', 'Altstadt 22, 4020 Linz, Österreich', '+43 664 99887638', 'https://maps.google.com/?cid=14124673639606582141', 14.284264, 48.304663),
(37, 'Linzer Heuriger', 'ChIJo1XNXoaXc0cRaY6dG3ZYP6U', b'1', 'Lederergasse 15, 4020 Linz, Österreich', '+43 732 781517', 'https://maps.google.com/?cid=11907333204083576425', 14.291149, 48.306691),
(38, 'Frühjahrsmarkt Linz Urfahr', 'ChIJ7WhbVYqZc0cRHswn1PSRJ5E', b'1', '4040 Linz, Österreich', NULL, 'https://maps.google.com/?cid=10459489140308691998', 14.289043, 48.313168),
(39, 'Sam\'s Steakhouse', 'ChIJ6SOz9CaYc0cRXoIUPSYKLu0', b'1', 'Hauptpl. 16-18, 4020 Linz, Österreich', '+43 676 6973198', 'https://maps.google.com/?cid=17090608795267400286', 14.286157, 48.305534),
(40, 'Wirtshaus Keintzel', 'ChIJMxpxsoaXc0cR-qOb7Bdvctk', b'1', 'Rathausgasse 8, 4020 Linz, Österreich', '+43 732 777550', 'https://maps.google.com/?cid=15668708202119930874', 14.287655, 48.306380),
(41, 'Gościnna Chata', 'ChIJgbhmxiWYc0cRgqrYpEdMl5I', b'1', 'Hafenstraße 4, 4020 Linz, Österreich', '+43 732 770961', 'https://maps.google.com/?cid=10562995321612839554', 14.301701, 48.314874),
(42, 'Coconut', 'ChIJ-wnbt4WXc0cRz8j2fJ7QOX8', b'1', 'Marienstraße 11, 4020 Linz, Österreich', '+43 650 2220032', 'https://maps.google.com/?cid=9167587895609313487', 14.290401, 48.304150),
(43, 'Bugs', 'ChIJZ5HmT4GXc0cRkEmEQhq1s_8', b'1', 'Hauptpl. 3, 4020 Linz, Österreich', '+43 732 785688', 'https://maps.google.com/?cid=18425269624892574096', 14.286754, 48.306374),
(44, 'Julia\'s Wohnzimmer', 'ChIJy-PDgTKYc0cRwig2sXdUDrM', b'1', 'Linke Brückenstraße 20, 4040 Linz, Österreich', '+43 664 3130701', 'https://maps.google.com/?cid=12902342855514007746', 14.290425, 48.319876),
(45, 'Miyako Ramen', 'ChIJiXXVIbeXc0cRBNqCmjt-TGw', b'1', 'Altstadt 28, 4020 Linz, Österreich', '+43 732 918155', 'https://maps.google.com/?cid=7803751048786663940', 14.284674, 48.304677),
(46, 'Pandana Thai Restaurant', 'ChIJrx75C4SXc0cRO_pyg2GRyxg', b'1', 'Hauptpl. 23, 4020 Linz, Österreich', '+43 732 775100', 'https://maps.google.com/?cid=1786681525185739323', 14.286870, 48.304692),
(47, 'New Namastey India', 'ChIJaTbZEsCXc0cRTtcZs6QlBGE', b'1', 'Volksgartenstraße 19, 4020 Linz, Österreich', '+43 732 280880', 'https://maps.google.com/?cid=6990753910895531854', 14.290089, 48.296169),
(48, 'Zinöggerstüberl', 'ChIJeU_0a8yXc0cR8-XgNrFE81M', b'1', 'Zinöggerweg 6, 4020 Linz, Österreich', '+43 676 6454988', 'https://maps.google.com/?cid=6049254252409316851', 14.298985, 48.272214),
(49, 'The Monkey Beach', 'ChIJS1Hf_DNXTo8RyVJ1dOURIVk', b'1', 'Av. Rafael E. Melgar 9, El Parque, 77600 San Miguel de Cozumel, Q.R., Mexiko', '+52 987 107 0004', 'https://maps.google.com/?cid=6422434220806066889', -86.968467, 20.487866),
(50, 'Hooters', 'ChIJgRW7ZF8oTI8Rfrx67z0Gb-Y', b'1', 'Blvd. Kukulcan KM 12.5, La Isla, Zona Hotelera, 77500 Cancún, Q.R., Mexiko', '+52 998 176 8035', 'https://maps.google.com/?cid=16604497214218878078', -86.764854, 21.110326),
(51, 'Izakaya Restaurant OG', 'ChIJMfRtuX-Xc0cRBcpB8OiVWK4', b'0', 'Klammstraße 6, 4020 Linz, Österreich', '+43 732 716817', 'https://maps.google.com/?cid=12562955988245793285', 14.284076, 48.302948),
(53, 'Das neue Muldenstüberl', 'ChIJHf5oagOXc0cRl33COfm_E5U', b'1', 'Muldenstraße 35, 4020 Linz, Österreich', '+43 676 5536649', 'https://maps.google.com/?cid=10742140613345574295', 14.299230, 48.274877),
(54, 'Hasenstall', 'ChIJD3rc-NSZc0cRnF-XU_6Kq0U', b'1', 'Hauptstraße 62, 4040 Linz, Österreich', '+43 732 716029', 'https://maps.google.com/?cid=5020259034563305372', 14.281115, 48.314499),
(55, 'Wirzhaus zur ewigen Ruh', 'ChIJk-2evNeXc0cRtVW89AJjmeI', b'0', 'Friedhofstraße 12, 4020 Linz, Österreich', '+43 732 776554', 'https://maps.google.com/?cid=16328190788355511733', 14.298545, 48.294294),
(56, 'Stiegl-Klosterhof', 'ChIJhZ_3D4WXc0cRjdtq97Y8SuA', b'1', 'Landstraße 30, 4020 Linz, Österreich', '+43 732 773373', 'https://maps.google.com/?cid=16161796969305136013', 14.289349, 48.302190),
(59, 'tamu sana', 'ChIJp9rTu3-Xc0cRS8By0zGYW8c', b'1', 'Kirchengasse 6, 4040 Linz, Österreich', '+43 732 711095', 'https://maps.google.com/?cid=14365242776196661323', 14.284466, 48.310065),
(60, 'Dos Muchachos', 'ChIJY-FcgPCXc0cR56HfqSAAv40', b'0', 'Zollamtstraße 14, 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=10213882620188533223', 14.287801, 48.306782),
(61, 'Lisis Schmankerlstube', 'ChIJG0fhrsyXc0cRJuDm29BZItU', b'1', 'Goethestraße 32, 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=15357936432864223270', 14.296674, 48.297292),
(63, 'LeBüsch', 'ChIJZ0fcuReXc0cRM4iu4aMxZcs', b'0', 'Graben 24, 4020 Linz, Österreich', '+43 670 6044004', 'https://maps.google.com/?cid=14656175142282889267', 14.289407, 48.305026),
(64, 'Bock-Treff', 'ChIJQdr4mfu9c0cRPUqFYqMT37I', b'0', 'Wiener Str. 501, 4030 Linz, Österreich', NULL, 'https://maps.google.com/?cid=12889042251011148349', 14.329796, 48.244639),
(65, 'Bayern Stubn', 'ChIJdRgoYMGXc0cRvPgyWURV4qE', b'1', 'Wiener Str. 89, 4020 Linz, Österreich', '+43 681 20790170', 'https://maps.google.com/?cid=11664979736885655740', 14.303935, 48.284670),
(66, 'Das Auerhahn', 'ChIJ5Q2ukviZc0cRLT03JhNyzI4', b'0', 'B125 228, 4040 Linz, Österreich', '+43 732 237888', 'https://maps.google.com/?cid=10289724675205840173', 14.302631, 48.326524),
(67, 'Union Cafe', 'ChIJC1T0LLmXc0cRZF9mEU9g1nk', b'0', 'Unionstraße 53, 4020 Linz, Österreich', '+43 732 652487', 'https://maps.google.com/?cid=8779310416315965284', 14.292744, 48.284404),
(68, 'Residenz-Cafe', 'ChIJnRXDUsqZc0cRWE_SjYr5kcQ', b'0', 'Leonfeldner Str. 78, 4040 Linz, Österreich', '+43 732 710670', 'https://maps.google.com/?cid=14164376676537093976', 14.286325, 48.327884),
(69, 'Grillstube Familie Danilovic', 'ChIJtb_0MuuXc0cRMf1GujbAfr0', b'0', 'Hamerlingstraße 17, 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=13654562461519904049', 14.300867, 48.291978),
(70, 'Carly - Connected Car', 'ChIJYVhJXuTenUcRcq0abxmryGU', b'0', 'Kolpingring 8, 82041 Oberhaching, Deutschland', '+49 89 45225817', 'https://maps.google.com/?cid=7334300118899404146', 11.585154, 48.030864),
(71, 'Charly\'s essen und trinken', 'ChIJYbM4nPKZc0cRp3UktA8Qwp0', b'0', 'Ferihumerstraße 44, 4040 Linz, Österreich', '+43 732 711439', 'https://maps.google.com/?cid=11367666069069395367', 14.289895, 48.315579),
(72, 'Gasthaus Little Saigon Linz', 'ChIJux16AYyXc0cRMdFt6zFbLTE', b'0', 'Gruberstraße 82, 4020 Linz, Österreich', '+43 699 10997312', 'https://maps.google.com/?cid=3543588751771816241', 14.300142, 48.303683),
(73, 'Cafe Scorpion', 'ChIJCwPn2_GXc0cR7g-5XQ87td0', b'0', 'Garnisonstraße 51A, 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=15975740190349660142', 14.312915, 48.297730),
(75, 'Magdalenal', 'ChIJu8P45UuYc0cR8C9HAsZORpU', b'0', 'Griesmayrstraße 18, 4040 Linz, Österreich', '+43 732 248659', 'https://maps.google.com/?cid=10756371372369719280', 14.300180, 48.333592),
(83, 'Restaurant Rauchkuchl', 'ChIJ7UbD5yaYc0cRhMpT8tkMo-Y', b'0', 'Holzstraße 18, 4020 Linz, Österreich', '+43 732 777108', 'https://maps.google.com/?cid=16619141180140276356', 14.302069, 48.312061),
(84, 'Lüfti - Lüfteneggerstüberl', 'ChIJzQkn7oeXc0cRL_tHMHRHro4', b'1', 'Lüfteneggerstraße 4, 4020 Linz, Österreich', '+43 732 282757', 'https://maps.google.com/?cid=10281233563685223215', 14.294309, 48.309128),
(85, 'Thüsen Tak', 'ChIJ0wmurYSXc0cR5xP5Mqianh8', b'1', 'Waltherstraße 21, 4020 Linz, Österreich', '+43 650 2271403', 'https://maps.google.com/?cid=2278428508696417255', 14.285138, 48.301086),
(86, 'Valdés', 'ChIJsTY5y4LWAr4RKOaySgOPusk', b'0', 'Valdés, Provinz Chubut, Argentinien', NULL, 'https://maps.google.com/?q=Vald%C3%A9s&ftid=0xbe02d682cb3936b1:0xc9ba8f034ab2e628', -63.879015, -42.528587),
(87, 'Cafe Valdés', 'ChIJUbPDhYSXc0cR6_9X7pgH62w', b'1', 'Herrenstraße 7, 4020 Linz, Österreich', '+43 676 3724301', 'https://maps.google.com/?cid=7848375129038389227', 14.286206, 48.302945),
(88, 'Kletterzentrum AM TURM', 'ChIJswP3rGuYc0cR2N7oh6ZksR0', b'0', 'Julius-Raab-Straße 4, 4040 Linz, Österreich', '+43 680 1292222', 'https://maps.google.com/?cid=2139601964385230552', 14.323422, 48.329218),
(89, 'Tramway im Stockhof', 'ChIJT_Gg7ZmXc0cRBUD975bSvAI', b'0', 'Stockhofstraße 27, 4020 Linz, Österreich', '+43 732 781564', 'https://maps.google.com/?cid=197264029410738181', 14.286863, 48.294925),
(90, 'Christkindlmarkt Hauptplatz', 'ChIJVVVV_oOXc0cRkTPeALT4Wck', b'1', 'Hauptpl., 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=14508901126543127441', 14.286646, 48.305633),
(91, 'amsec', 'ChIJcz6BPpmmc0cR06rdYnj_G6A', b'1', 'Softwarepark 37, 4232 Hagenberg im Mühlkreis, Österreich', '+43 7236 33510', 'https://maps.google.com/?cid=11537095762959510227', 14.513291, 48.369844),
(92, 'Alte Metzgerei', 'ChIJ-dDggISXc0cRKFU83UubDGY', b'1', 'Herrenstraße 5, 4020 Linz, Österreich', '+43 732 774434', 'https://maps.google.com/?cid=7353423041725748520', 14.285996, 48.303146),
(93, 'Szechuan Impression', 'ChIJAdXQVhyXc0cR9VtNT_sygto', b'0', 'Rathausgasse 1, 4020 Linz, Österreich', '+43 664 5142589', 'https://maps.google.com/?cid=15745203302189325301', 14.287078, 48.306264),
(94, 'Gasthaus Eckerl', 'ChIJW2sjGbCXc0cReS6nEtq3AUo', b'0', 'Unionstraße 92, 4020 Linz, Österreich', '+43 732 670880', 'https://maps.google.com/?cid=5332745581027077753', 14.281200, 48.279995),
(96, 'amsec2', 'ChIJcz6BPpmmc0cR06rdYnj_G6A', b'0', 'Softwarepark 37, 4232 Hagenberg im Mühlkreis, Österreich', '+43 7236 33510', 'https://maps.google.com/?cid=11537095762959510227', 14.513291, 48.369844),
(97, 'Goethe Stub\'n', 'ChIJ69q1P5KXc0cRuHk0-ZRgSF8', b'1', 'Dinghoferstraße 52, 4020 Linz, Österreich', '+43 732 658617', 'https://maps.google.com/?cid=6865843824878713272', 14.298333, 48.297936),
(98, 'Gasthaus \"Zur Eisernen Hand\"', 'ChIJgzchoI6Xc0cRTiu46C6yUAw', b'1', 'Eisenhandstraße 43, 4020 Linz, Österreich', '+43 732 770182', 'https://maps.google.com/?cid=887405041134611278', 14.299259, 48.302878),
(99, 'Asia Restaurant Grandmother Food', 'ChIJGY_iCvIHbUcRrMCRUj6TKwA', b'0', 'Burggasse 101, 1070 Wien, Österreich', '+43 1 5234398', 'https://maps.google.com/?cid=12265319881097388', 16.341829, 48.204245),
(100, 'Cafe Andi\"s Cool', 'ChIJ0S4vM5CXc0cRlYTL4xp-iNo', b'1', 'Bürgerstraße 21, 4020 Linz, Österreich', '+43 677 63165482', 'https://maps.google.com/?cid=15746974751056954517', 14.293909, 48.299045),
(101, 'Fischerhäusl', 'ChIJK3f_LICXc0cRflIr3odrAt8', b'1', 'Flußgasse 3, 4040 Linz, Österreich', '+43 732 232700', 'https://maps.google.com/?cid=16069524651703489150', 14.282267, 48.309040),
(103, 'Gasthaus \"Zur Eisernen Hand\"2', 'ChIJgzchoI6Xc0cRTiu46C6yUAw', b'1', 'Eisenhandstraße 43, 4020 Linz, Österreich', '+43 732 770182', 'https://maps.google.com/?cid=887405041134611278', 14.299259, 48.302878),
(104, 'Restaurant \"Alte Brücke Mostar\"', 'ChIJVdPpeD-Wc0cRofmWntVxGUk', b'0', 'Dauphinestraße 224, 4030 Linz, Österreich', '+43 732 380490', 'https://maps.google.com/?cid=5267366401489172897', 14.284930, 48.253845),
(105, 'Bangkok smile', 'ChIJ6w_9WIOXc0cRs-Sckjsnm-M', b'0', 'Waltherstraße 11, 4020 Linz, Österreich', '+43 732 773820', 'https://maps.google.com/?cid=16400745604816102579', 14.284683, 48.301784),
(106, 'Restaurant Rauner', 'ChIJh28l4sGXc0cRUnmG_3K1bLY', b'0', 'Kraußstraße 16, 4020 Linz, Österreich', '+43 732 918484', 'https://maps.google.com/?cid=13145080917905537362', 14.304922, 48.288137),
(107, 'Cafe Bar Mezzanin', 'ChIJUdpvP4CXc0cRlBP4Oke1XlU', b'0', 'Johann-Konrad-Vogel-Straße 11, 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=6151553458571318164', 14.292468, 48.300785),
(108, 'Exxtrablatt', 'ChIJVVWF8YSXc0cRIHIdYMySvbU', b'0', 'Spittelwiese 8, 4020 Linz, Österreich', '+43 732 77247755', 'https://maps.google.com/?cid=13095784697946796576', 14.287548, 48.302621),
(109, 'dombar', 'ChIJfW7yivqXc0cRj1muRiIWGAE', b'0', 'Stifterstraße 4, 4020 Linz, Österreich', '+43 676 6739017', 'https://maps.google.com/?cid=78837329949514127', 14.286917, 48.299779),
(110, 'Schlosscafe - Linz', 'ChIJf3vWLYKXc0cRtVWQgsnTqHk', b'0', 'Schlossberg 1, 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=8766489537109054901', 14.282341, 48.305391),
(112, 'Hofkneipe2', 'ChIJ-V7XVyaYc0cRvWHfZO7pBSk', b'0', 'Ludlgasse 16, 4020 Linz, Österreich', '+43 732 771188', 'https://maps.google.com/?cid=2956025940542448061', 14.300611, 48.312142),
(113, 'TAIFUN asiatisches Restaurant', 'ChIJzQGxIliWc0cRZnO5l_-LL50', b'1', 'Dr. Herbert-Sperl-Ring 2, 4060 Leonding, Österreich', '+43 732 671463', 'https://maps.google.com/?cid=11326425517738521446', 14.259807, 48.262852),
(114, 'Gelbes Krokodil', 'ChIJv-10mYWXc0cRpod6T3TDtxs', b'1', 'OK-Platz 1, 4020 Linz, Österreich', '+43 732 784182', 'https://maps.google.com/?cid=1997279864079157158', 14.290849, 48.302931),
(116, 'Gelbes Krokodil2', 'ChIJv-10mYWXc0cRpod6T3TDtxs', b'0', 'OK-Platz 1, 4020 Linz, Österreich', '+43 732 784182', 'https://maps.google.com/?cid=1997279864079157158', 14.290849, 48.302931),
(117, 'China Restaurant - Xu Wok & More Linz', 'ChIJEx0De4WXc0cR7ANKqzz0Mn8', b'0', 'Mozartstraße 7, 4020 Linz, Österreich', '+43 732 234372', 'https://maps.google.com/?cid=9165656733061350380', 14.291433, 48.302315),
(118, 'Sudhaus Traun', 'ChIJpe6lkMuVc0cRByQDfAay-Jo', b'0', 'Madlschenterweg 7, 4050 Traun, Österreich', '+43 7229 21109', 'https://maps.google.com/?cid=11166871016985273351', 14.240133, 48.219343),
(119, 'Hannis Beisl', 'ChIJ2Xt6cISXc0cR70O_FdNsumc', b'0', 'Sankt-Peter-Straße 42, 4020 Linz, Österreich', NULL, 'https://maps.google.com/?cid=7474406185433514991', 14.322264, 48.287280),
(120, 'La Bottega', 'ChIJg7ZLDe2bc0cRAKgqLDiijE4', b'0', 'Weingartenstraße 14, 4100 Ottensheim, Österreich', '+43 7234 82128', 'https://maps.google.com/?cid=5660077193840732160', 14.177024, 48.338088),
(121, 'Pizzamanufaktur Casa Vecchia', 'ChIJEd9Nl4aac0cRVzP3s-PazaU', b'0', 'Marktpl. 4, 4100 Ottensheim, Österreich', '+43 7234 85055', 'https://maps.google.com/?cid=11947446057995547479', 14.176232, 48.331672),
(122, 'Gasthof Zur Post Ottensheim', 'ChIJ4f4w9Iaac0cRikbUhetQaOY', b'0', 'Linzer Str. 17, 4100 Ottensheim, Österreich', '+43 7234 82228', 'https://maps.google.com/?cid=16602608998794151562', 14.177847, 48.332321),
(123, 'Donauhof An der Fähre', 'ChIJdQ9syIaac0cRzQFxUxhqXGA', b'0', 'Donaulände 9, 4100 Ottensheim, Österreich', '+43 7234 83818', 'https://maps.google.com/?cid=6943541378210136525', 14.176375, 48.330346),
(124, 'ARIS Taverna.Ouserie', 'ChIJ9XMOsHeXc0cRxHzgQh2666o', b'0', 'Mariahilfgasse 40, 4020 Linz, Österreich', '+43 664 3728801', 'https://maps.google.com/?cid=12316142240813579460', 14.274590, 48.300216),
(125, 'Schnellimbiss am Schillerpark', 'ChIJAyv6kX6Xc0cRvbFQbkMHhuA', b'1', 'Schillerpl., 4020 Linz, Österreich', '+43 660 1591069', 'https://maps.google.com/?cid=16178626697570070973', 14.291130, 48.298316),
(126, 'Wia z\'haus Lehner', 'ChIJ4ZhLUc-Zc0cR7kS77ggnP10', b'0', 'Harbacher Str. 38, 4040 Linz, Österreich', '+43 732 730510', 'https://maps.google.com/?cid=6719132088378541294', 14.277377, 48.326938),
(127, 'Rosi\'s Pub', 'ChIJsR9QqZ2Xc0cR69Ja-gtNLzU', b'1', 'Wiener Str. 18, 4020 Linz, Österreich', '+43 732 658172', 'https://maps.google.com/?cid=3832366521755816683', 14.298363, 48.289003),
(128, 'Kirchenwirt am Pöstlingberg Haudum/Ruetz OG', 'ChIJB3su1eeZc0cRakv6GB3kNlM', b'0', 'Am Pöstlingberg 6, 4040 Linz, Österreich', '+43 732 731071', 'https://maps.google.com/?cid=5996230767514635114', 14.258292, 48.324600),
(129, 'Liebhaberei Linz', 'ChIJOxXB6KaXc0cRFHoZojh625k', b'1', 'Hauptpl. 11, 4020 Linz, Österreich', '+43 732 776784', 'https://maps.google.com/?cid=11086589291358943764', 14.285684, 48.306083),
(130, 'Da Giulio Linz', 'ChIJTdnK4wO9c0cRg2Mzm9NjXlE', b'0', 'Wiener Str. 485, 4030 Linz, Österreich', '+43 732 272707', 'https://maps.google.com/?cid=5863233525376050051', 14.328602, 48.245425),
(131, 'Trattoria Scollo', 'ChIJJQiKfjOZc0cRp_T0jAuUhaQ', b'0', 'Knabenseminarstraße 6, 4040 Linz, Österreich', '+43 650 8040696', 'https://maps.google.com/?cid=11855044371453113511', 14.280439, 48.316168);

-- --------------------------------------------------------

--
-- Table structure for table `location_rating`
--

CREATE TABLE `location_rating` (
  `key` int(11) NOT NULL,
  `location` int(11) NOT NULL,
  `member` int(11) NOT NULL,
  `rating` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `members`
--

CREATE TABLE `members` (
  `key` int(11) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `chat_id` bigint(20) DEFAULT NULL,
  `score` int(11) NOT NULL DEFAULT 0,
  `joined` datetime NOT NULL,
  `left` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `members`
--

INSERT INTO `members` (`key`, `user_id`, `chat_id`, `score`, `joined`, `left`) VALUES
(4, 4711, NULL, 0, '2022-10-13 19:50:14', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `participants`
--

CREATE TABLE `participants` (
  `key` int(11) NOT NULL,
  `member` int(11) NOT NULL,
  `event` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `participants`
--

INSERT INTO `participants` (`key`, `member`, `event`) VALUES
(1, 4, 1),
(2, 4, 1),
(3, 4, 1),
(4, 4, 1);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `leistungstag`
--
ALTER TABLE `leistungstag`
  ADD PRIMARY KEY (`key`),
  ADD KEY `leistungstag_fk0` (`location`);

--
-- Indexes for table `locations`
--
ALTER TABLE `locations`
  ADD PRIMARY KEY (`key`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `location_rating`
--
ALTER TABLE `location_rating`
  ADD PRIMARY KEY (`key`),
  ADD KEY `location_rating_fk0` (`location`),
  ADD KEY `location_rating_fk1` (`member`);

--
-- Indexes for table `members`
--
ALTER TABLE `members`
  ADD PRIMARY KEY (`key`),
  ADD UNIQUE KEY `user_id` (`user_id`),
  ADD UNIQUE KEY `chat_id` (`chat_id`);

--
-- Indexes for table `participants`
--
ALTER TABLE `participants`
  ADD PRIMARY KEY (`key`),
  ADD KEY `participants_fk0` (`member`),
  ADD KEY `participants_fk1` (`event`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `leistungstag`
--
ALTER TABLE `leistungstag`
  MODIFY `key` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=74;

--
-- AUTO_INCREMENT for table `locations`
--
ALTER TABLE `locations`
  MODIFY `key` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=132;

--
-- AUTO_INCREMENT for table `location_rating`
--
ALTER TABLE `location_rating`
  MODIFY `key` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `members`
--
ALTER TABLE `members`
  MODIFY `key` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `participants`
--
ALTER TABLE `participants`
  MODIFY `key` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `leistungstag`
--
ALTER TABLE `leistungstag`
  ADD CONSTRAINT `leistungstag_fk0` FOREIGN KEY (`location`) REFERENCES `locations` (`key`);

--
-- Constraints for table `location_rating`
--
ALTER TABLE `location_rating`
  ADD CONSTRAINT `location_rating_fk0` FOREIGN KEY (`location`) REFERENCES `locations` (`key`),
  ADD CONSTRAINT `location_rating_fk1` FOREIGN KEY (`member`) REFERENCES `members` (`key`);

--
-- Constraints for table `participants`
--
ALTER TABLE `participants`
  ADD CONSTRAINT `participants_fk0` FOREIGN KEY (`member`) REFERENCES `members` (`key`),
  ADD CONSTRAINT `participants_fk1` FOREIGN KEY (`event`) REFERENCES `leistungstag` (`key`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
