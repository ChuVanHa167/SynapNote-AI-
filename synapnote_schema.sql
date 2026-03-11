-- Tạo Database (Nếu chưa có)
CREATE DATABASE IF NOT EXISTS `synapnote_ai` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `synapnote_ai`;

-- --------------------------------------------------------
-- 1. Bảng: users (Tài khoản người dùng)
-- --------------------------------------------------------
CREATE TABLE `users` (
  `id` VARCHAR(36) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `display_name` VARCHAR(100) NOT NULL,
  `title` VARCHAR(100) DEFAULT NULL,
  `hashed_password` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 2. Bảng: meetings (Thông tin cuộc họp & Audio)
-- --------------------------------------------------------
CREATE TABLE `meetings` (
  `id` VARCHAR(36) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `participants` INT DEFAULT 1,
  `date` VARCHAR(50) NOT NULL,
  `duration` VARCHAR(50) DEFAULT '0m 0s',
  `status` ENUM('PENDING', 'ĐANG XỬ LÝ', 'HOÀN THÀNH', 'LỖI') DEFAULT 'PENDING',
  
  -- Kết quả AI sinh ra
  `summary` TEXT DEFAULT NULL,
  `transcript` LONGTEXT DEFAULT NULL,
  
  -- Foreign key link tới người tải lên (tùy chọn)
  `user_id` VARCHAR(36) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (`id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 3. Bảng: meeting_decisions (Các quyết định được AI rút ra)
-- --------------------------------------------------------
CREATE TABLE `meeting_decisions` (
  `id` INT AUTO_INCREMENT NOT NULL,
  `meeting_id` VARCHAR(36) NOT NULL,
  `content` TEXT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`meeting_id`) REFERENCES `meetings`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 4. Bảng: action_items (Công việc cần làm)
-- --------------------------------------------------------
CREATE TABLE `action_items` (
  `id` VARCHAR(36) NOT NULL,
  `meeting_id` VARCHAR(36) NOT NULL,
  `task` VARCHAR(255) NOT NULL,
  `assignee` VARCHAR(100) DEFAULT NULL,
  `deadline` VARCHAR(50) DEFAULT NULL,
  `status` ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`meeting_id`) REFERENCES `meetings`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 5. Bảng: api_keys (Token tích hợp Zapier/Make)
-- --------------------------------------------------------
CREATE TABLE `api_keys` (
  `id` VARCHAR(36) NOT NULL,
  `user_id` VARCHAR(36) NOT NULL,
  `api_key` VARCHAR(255) NOT NULL,
  `name` VARCHAR(100) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_api_key` (`api_key`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- DATA: Seed Mẫu Admin User
-- Mật khẩu mặc định: 123456 (Đã hash Bcrypt mẫu)
-- --------------------------------------------------------
INSERT INTO `users` (`id`, `email`, `display_name`, `title`, `hashed_password`) 
VALUES 
('user_admin_123', 'admin@synapnote.com', 'Alexander', 'Quản trị viên', '$2b$12$N9Zxh7F.G8V/lA/V/g31.e41B5uXF0e4q5v6l17h/v3T70r3g5mG2');
