
USE `discord_bot`;

DROP TABLE IF EXISTS `servers`;


CREATE TABLE `servers` (
  `id` bigint UNSIGNED NOT NULL,
  `welcome_ch` bigint UNSIGNED DEFAULT NULL,
  `level_up_ch` bigint UNSIGNED DEFAULT NULL,
  `level_sys` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



DROP TABLE IF EXISTS `server_users`;


CREATE TABLE `server_users` (
  `id` bigint UNSIGNED  NOT NULL,
  `server_id` bigint UNSIGNED NOT NULL,
  `user_xp` int NOT NULL DEFAULT 0,
  `level` tinyint UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`,`server_id`),
  KEY `fk_server_id` (`server_id`),
  CONSTRAINT `fk_server_id` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;