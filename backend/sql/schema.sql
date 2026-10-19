-- =============================================================================
-- 校园报修系统：数据库与表结构（MySQL 8，utf8mb4）
-- 用途：在 DataGrip 中直接执行本脚本即可创建库、表与演示账号。
-- 连接：host=localhost, port=3307, database=repair_system
-- 账号：应用连接 repair / repair；如需在 DataGrip 中执行本脚本，请使用 root 账号。
-- =============================================================================

CREATE DATABASE IF NOT EXISTS repair_system
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- 应用专用账号（与 backend/.env 的 DATABASE_URL 对应；已存在则跳过）
CREATE USER IF NOT EXISTS 'repair'@'localhost' IDENTIFIED BY 'repair';
CREATE USER IF NOT EXISTS 'repair'@'%' IDENTIFIED BY 'repair';
GRANT ALL PRIVILEGES ON repair_system.* TO 'repair'@'localhost';
GRANT ALL PRIVILEGES ON repair_system.* TO 'repair'@'%';
FLUSH PRIVILEGES;

USE repair_system;

-- -----------------------------------------------------------------------------
-- users：学生 / 维修人员 / 管理员
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  display_name VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL COMMENT 'student | tech | admin',
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username),
  KEY ix_users_username (username),
  KEY ix_users_role (role)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- sequence_counters：工单编号顺序计数器（ADR-0002）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sequence_counters (
  name VARCHAR(32) NOT NULL,
  value INT NOT NULL DEFAULT 0,
  PRIMARY KEY (name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- tickets：工单主表（PENDING -> PROCESSING -> RESOLVED -> CLOSED / CANCELLED）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tickets (
  id INT NOT NULL AUTO_INCREMENT,
  ticket_no VARCHAR(20) NOT NULL,
  title VARCHAR(80) NOT NULL,
  description TEXT NOT NULL,
  category VARCHAR(50) NOT NULL COMMENT '教学设备 / 电脑设备 / 网络故障 / 水电设施',
  location VARCHAR(100) NOT NULL,
  priority VARCHAR(10) NOT NULL COMMENT 'LOW | MEDIUM | HIGH',
  status VARCHAR(20) NOT NULL COMMENT 'PENDING | PROCESSING | RESOLVED | CLOSED | CANCELLED',
  reporter_id INT NOT NULL,
  assignee_id INT NULL,
  assigned_by INT NULL,
  assigned_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_tickets_ticket_no (ticket_no),
  KEY ix_tickets_ticket_no (ticket_no),
  KEY ix_tickets_priority (priority),
  KEY ix_tickets_status (status),
  KEY ix_tickets_reporter_id (reporter_id),
  KEY ix_tickets_assignee_id (assignee_id),
  CONSTRAINT fk_tickets_reporter FOREIGN KEY (reporter_id) REFERENCES users (id),
  CONSTRAINT fk_tickets_assignee FOREIGN KEY (assignee_id) REFERENCES users (id),
  CONSTRAINT fk_tickets_assigned_by FOREIGN KEY (assigned_by) REFERENCES users (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- ticket_comments：工单留言
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ticket_comments (
  id INT NOT NULL AUTO_INCREMENT,
  ticket_id INT NOT NULL,
  author_id INT NOT NULL,
  content VARCHAR(500) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_ticket_comments_ticket_id (ticket_id),
  KEY ix_ticket_comments_author_id (author_id),
  CONSTRAINT fk_ticket_comments_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (id),
  CONSTRAINT fk_ticket_comments_author FOREIGN KEY (author_id) REFERENCES users (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- ticket_logs：操作日志时间线（追加写入，不修改不删除）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ticket_logs (
  id INT NOT NULL AUTO_INCREMENT,
  ticket_id INT NOT NULL,
  actor_id INT NOT NULL,
  action VARCHAR(20) NOT NULL COMMENT 'CREATE | ACCEPT | ASSIGN | RESOLVE | CLOSE | CANCEL | COMMENT',
  from_status VARCHAR(20) NULL,
  to_status VARCHAR(20) NULL,
  detail VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_ticket_logs_ticket_id (ticket_id),
  KEY ix_ticket_logs_actor_id (actor_id),
  KEY ix_ticket_logs_action (action),
  CONSTRAINT fk_ticket_logs_ticket FOREIGN KEY (ticket_id) REFERENCES tickets (id),
  CONSTRAINT fk_ticket_logs_actor FOREIGN KEY (actor_id) REFERENCES users (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 演示账号（密码均为 123456；幂等，可重复执行）
-- 更多样例工单数据请运行：uv run python -m scripts.seed
-- -----------------------------------------------------------------------------
INSERT IGNORE INTO users (username, display_name, password_hash, role) VALUES
  ('student', '学生用户', '$argon2id$v=19$m=65536,t=3,p=4$L8w7/cnjYZUjjXGIV771kQ$mwPAnSUKMA3VLn1cv+8MrJAsL9r/fKZhEAziqSlVpes', 'student'),
  ('tech', '维修人员', '$argon2id$v=19$m=65536,t=3,p=4$L8w7/cnjYZUjjXGIV771kQ$mwPAnSUKMA3VLn1cv+8MrJAsL9r/fKZhEAziqSlVpes', 'tech'),
  ('admin', '系统管理员', '$argon2id$v=19$m=65536,t=3,p=4$L8w7/cnjYZUjjXGIV771kQ$mwPAnSUKMA3VLn1cv+8MrJAsL9r/fKZhEAziqSlVpes', 'admin');

-- 工单编号计数器：初始值为 7（与 seed 样例 REP-0001..REP-0007 对齐）
INSERT IGNORE INTO sequence_counters (name, value) VALUES ('ticket_no', 7);
