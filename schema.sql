CREATE
DATABASE IF NOT EXISTS `discord_bot`;

USE `discord_bot`;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `server_levels`;
DROP TABLE IF EXISTS `server_users`;
DROP TABLE IF EXISTS `servers`;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `servers` (
    `id` BIGINT UNSIGNED NOT NULL,
    `welcome_ch` BIGINT UNSIGNED DEFAULT NULL,
    `farewell_ch` BIGINT UNSIGNED DEFAULT NULL,
    `youtube_ch` BIGINT UNSIGNED DEFAULT NULL,
    `level_up_ch` BIGINT UNSIGNED DEFAULT NULL,
    `level_system_enabled` tinyint(1) DEFAULT 0,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `users` (
    `id` BIGINT UNSIGNED NOT NULL,
    `mal_profil` VARCHAR(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,

    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `server_users` (
    `user_id` BIGINT UNSIGNED NOT NULL,
    `server_id` BIGINT UNSIGNED NOT NULL,
    `user_xp_text` int NOT NULL DEFAULT 0,
    `user_xp_text_monthly` int NOT NULL DEFAULT 0,
    `user_xp_voice` int NOT NULL DEFAULT 0,
    `user_xp_voice_monthly` int NOT NULL DEFAULT 0,
    `level` tinyint UNSIGNED NOT NULL DEFAULT 0,
    `level_sys_number` int DEFAULT 0,
    PRIMARY KEY (`user_id`,`server_id`),
    KEY `fk_server_id` (`server_id`),
    KEY `fk_user_id` (`user_id`),
    CONSTRAINT `fk_server_id` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
    CONSTRAINT `fk_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `server_levels` (
    `level_sys_number` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `server_id` BIGINT UNSIGNED NOT NULL,
    `level` INT UNSIGNED NOT NULL DEFAULT 0,
    `role_id` BIGINT UNSIGNED NOT NULL,
    `level_sys_name` VARCHAR(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
    PRIMARY KEY (`level_sys_number`),
    UNIQUE KEY `uq_server_level` (`server_id`, `level`),
    KEY `fk_server_level` (`server_id`),
    CONSTRAINT `fk_server_level` FOREIGN KEY (`server_id`) REFERENCES `servers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
