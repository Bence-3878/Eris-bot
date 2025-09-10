CREATE
DATABASE IF NOT EXISTS `discord_bot`;

USE `discord_bot`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `server_levels`;
DROP TABLE IF EXISTS `server_users`;
DROP TABLE IF EXISTS `servers`;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `servers` (
  `id` bigint UNSIGNED NOT NULL,
  `welcome_ch` bigint UNSIGNED DEFAULT NULL,
  `level_up_ch` bigint UNSIGNED DEFAULT NULL,
  `level_sys` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `server_users` (
  `id` bigint UNSIGNED  NOT NULL,
  `server_id` bigint UNSIGNED NOT NULL,
  `user_xp` int NOT NULL DEFAULT 0,
  `level` tinyint UNSIGNED NOT NULL DEFAULT 0,
  `level_sys` int DEFAULT 0,
  PRIMARY KEY (`id`,`server_id`),
  KEY `fk_server_id` (`server_id`),
  CONSTRAINT `fk_server_id` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `server_levels` (
  `server_id` bigint UNSIGNED NOT NULL,
  `level` int UNSIGNED NOT NULL DEFAULT 0,
  `role_id` bigint UNSIGNED NOT NULL,
  `level_sys` int DEFAULT 0,
  PRIMARY KEY (`server_id`,`level`,`role_id`),
  KEY `fk_server_level` (`server_id`),
  CONSTRAINT `fk_server_level` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
