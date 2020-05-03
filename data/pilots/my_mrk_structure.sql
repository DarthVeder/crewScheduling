SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;


CREATE TABLE IF NOT EXISTS `flights` (
  `id` int(16) unsigned NOT NULL AUTO_INCREMENT,
  `datestamp` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  `UserName` varchar(22) NOT NULL DEFAULT '',
  `CompanyName` varchar(35) NOT NULL DEFAULT '',
  `PilotName` varchar(35) NOT NULL DEFAULT '',
  `FlightId` varchar(10) NOT NULL DEFAULT '',
  `OnlineNetworkNbr` tinyint(4) NOT NULL DEFAULT '0',
  `FlightDate` date NOT NULL DEFAULT '0000-00-00',
  `AircraftName` varchar(50) NOT NULL DEFAULT '',
  `AircraftType` varchar(5) NOT NULL DEFAULT '',
  `NbrPassengers` smallint(2) NOT NULL DEFAULT '0',
  `CargoWeight` varchar(15) NOT NULL DEFAULT '',
  `Mtow` varchar(15) NOT NULL DEFAULT '',
  `StartAircraftWeight` varchar(15) NOT NULL DEFAULT '',
  `EndAircraftWeight` varchar(15) NOT NULL DEFAULT '',
  `StartFuelQuantity` varchar(15) NOT NULL DEFAULT '',
  `EndFuelQuantity` varchar(15) NOT NULL DEFAULT '',
  `DepartureIcaoName` varchar(50) NOT NULL DEFAULT '',
  `ArrivalIcaoName` varchar(50) NOT NULL DEFAULT '',
  `DepartureLocalHour` time NOT NULL DEFAULT '00:00:00',
  `ArrivalLocalHour` time NOT NULL DEFAULT '00:00:00',
  `DepartureGmtHour` time NOT NULL DEFAULT '00:00:00',
  `ArrivalGmtHour` time NOT NULL DEFAULT '00:00:00',
  `TotalBlockTime` time NOT NULL DEFAULT '00:00:00',
  `TotalBlockTimeNight` time NOT NULL DEFAULT '00:00:00',
  `TotalAirbornTime` time NOT NULL DEFAULT '00:00:00',
  `TotalTimeOnGround` time NOT NULL DEFAULT '00:00:00',
  `TotalDistance` varchar(18) NOT NULL DEFAULT '',
  `MaxAltitude` varchar(15) NOT NULL DEFAULT '',
  `CruiseSpeed` varchar(15) NOT NULL DEFAULT '',
  `CruiseMachSpeed` varchar(15) NOT NULL DEFAULT '',
  `CruiseTimeStartSec` time NOT NULL DEFAULT '00:00:00',
  `CruiseTimeStopSec` time NOT NULL DEFAULT '00:00:00',
  `CruiseFuelStart` varchar(15) NOT NULL DEFAULT '',
  `CruiseFuelStop` varchar(15) NOT NULL DEFAULT '',
  `LandingSpeed` varchar(15) NOT NULL DEFAULT '',
  `LandingPitch` varchar(15) NOT NULL DEFAULT '',
  `TouchDownVertSpeedFt` float NOT NULL DEFAULT '0',
  `CaptainSentMayday` tinyint(3) NOT NULL DEFAULT '0',
  `CrashFlag` tinyint(3) NOT NULL DEFAULT '0',
  `FlightResult` varchar(15) NOT NULL DEFAULT '',
  `PassengersOpinion` tinyint(4) NOT NULL DEFAULT '0',
  `PassengersOpinionText` text NOT NULL,
  `FailureText` text NOT NULL,
  `CasualtiesText` text NOT NULL,
  `PilotBonusText` text NOT NULL,
  `BonusPoints` int(10) NOT NULL DEFAULT '0',
  `PilotPenalityText` text NOT NULL,
  `PenalityPoints` int(10) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `datestamp` (`datestamp`),
  KEY `UserName` (`UserName`),
  KEY `CompanyName` (`CompanyName`),
  KEY `PilotName` (`PilotName`),
  KEY `AircraftName` (`AircraftName`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=54 ;

CREATE TABLE IF NOT EXISTS `user_profile` (
  `id` int(16) unsigned NOT NULL AUTO_INCREMENT,
  `UserName` varchar(22) NOT NULL DEFAULT '',
  `Password` varchar(22) NOT NULL DEFAULT '',
  `Email` varchar(40) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `UserName` (`UserName`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=4 ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
