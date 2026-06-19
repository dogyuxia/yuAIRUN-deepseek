-- ============================================================
-- yuAIRUN 数据库初始化脚本
-- 版本: v1.0
-- 数据库: yuairundeep (MySQL 8.0+)
-- 说明: 执行此脚本将删除旧库并重建完整表结构
-- ============================================================

-- 删除旧库并创建新库
DROP DATABASE IF EXISTS yuairun;
CREATE DATABASE IF NOT EXISTS yuairundeep
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE yuairundeep;

-- ============================================================
-- 1. 用户表 (users)
-- ============================================================
CREATE TABLE users (
    id VARCHAR(32) PRIMARY KEY COMMENT '用户唯一ID，格式 u_xxx',
    openid VARCHAR(128) NOT NULL UNIQUE COMMENT '微信 openid',
    unionid VARCHAR(128) DEFAULT NULL COMMENT '微信 unionid（多平台时使用）',
    nickname VARCHAR(64) NOT NULL DEFAULT '' COMMENT '微信昵称',
    avatar_url VARCHAR(512) NOT NULL DEFAULT '' COMMENT '微信头像 URL',
    xp INT NOT NULL DEFAULT 0 COMMENT '经验值',
    level INT NOT NULL DEFAULT 1 COMMENT '等级',
    last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
    is_deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '软删除标记',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    updated_at DATETIME NOT NULL COMMENT '更新时间',
    INDEX idx_openid (openid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 2. 闯关历史表 (quiz_history)
-- ============================================================
CREATE TABLE quiz_history (
    id VARCHAR(32) PRIMARY KEY COMMENT '记录ID，格式 h_xxx',
    user_id VARCHAR(32) NOT NULL COMMENT '用户ID',
    subject VARCHAR(64) NOT NULL COMMENT '学科',
    topic VARCHAR(256) NOT NULL COMMENT '知识点',
    question_count INT NOT NULL COMMENT '总题数',
    correct_count INT NOT NULL COMMENT '正确数',
    accuracy DECIMAL(4,3) NOT NULL COMMENT '正确率 0.000~1.000',
    duration INT NOT NULL DEFAULT 0 COMMENT '答题用时（秒）',
    xp_earned INT NOT NULL DEFAULT 0 COMMENT '获得经验值',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_created (user_id, created_at DESC) COMMENT '用户按时间查询历史',
    INDEX idx_user_subject (user_id, subject) COMMENT '按学科筛选'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='闯关历史表';

-- ============================================================
-- 3. 答题详情表 (quiz_answers)
-- ============================================================
CREATE TABLE quiz_answers (
    id VARCHAR(32) PRIMARY KEY COMMENT '记录ID，格式 qa_xxx',
    history_id VARCHAR(32) NOT NULL COMMENT '关联的闯关记录ID',
    user_id VARCHAR(32) NOT NULL COMMENT '用户ID',
    question JSON NOT NULL COMMENT '完整题目对象（含选项、答案、解析）',
    user_answer VARCHAR(256) NOT NULL COMMENT '用户的答案',
    is_correct TINYINT(1) NOT NULL COMMENT '是否正确',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    FOREIGN KEY (history_id) REFERENCES quiz_history(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_history (history_id),
    INDEX idx_user_correct (user_id, is_correct)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='答题详情表';

-- ============================================================
-- 4. 错题本表 (wrong_book)
-- ============================================================
CREATE TABLE wrong_book (
    id VARCHAR(32) PRIMARY KEY COMMENT '记录ID，格式 wb_xxx',
    user_id VARCHAR(32) NOT NULL COMMENT '用户ID',
    history_id VARCHAR(32) NOT NULL COMMENT '来源闯关记录ID',
    question JSON NOT NULL COMMENT '完整题目对象',
    user_answer VARCHAR(256) NOT NULL COMMENT '用户当时的选择',
    correct_answer VARCHAR(256) NOT NULL COMMENT '正确答案',
    subject VARCHAR(64) NOT NULL COMMENT '学科',
    topic VARCHAR(256) NOT NULL COMMENT '知识点',
    wrong_count INT NOT NULL DEFAULT 1 COMMENT '答错次数（累计）',
    last_wrong_at DATETIME NOT NULL COMMENT '最近一次答错时间',
    is_mastered TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已掌握',
    created_at DATETIME NOT NULL COMMENT '首次加入错题本时间',
    updated_at DATETIME NOT NULL COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (history_id) REFERENCES quiz_history(id) ON DELETE CASCADE,
    INDEX idx_user_subject (user_id, subject),
    INDEX idx_user_mastered (user_id, is_mastered)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='错题本表';

-- ============================================================
-- 初始化完成
-- ============================================================
SELECT '✅ 数据库 yuairundeep 初始化完成!' AS result;
