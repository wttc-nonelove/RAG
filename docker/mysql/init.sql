-- RAG 智能问答系统 - 数据库初始化脚本
-- MySQL 8.0

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

USE rag_db;

-- ============================================================
-- 1. users 表
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','user') NOT NULL DEFAULT 'user',
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. documents 表
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type ENUM('PDF','DOCX','TXT','MD','XLSX','XLS','CSV') NOT NULL,
    file_size BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    tag VARCHAR(100),
    parse_status ENUM('pending','parsing','completed','failed') NOT NULL DEFAULT 'pending',
    version INT NOT NULL DEFAULT 1,
    uploaded_by INT,
    error_message TEXT,
    embedding_tokens INT DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_documents_parse_status ON documents(parse_status);
CREATE INDEX idx_documents_tag ON documents(tag);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);

-- ============================================================
-- 3. conversations 表
-- ============================================================
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL DEFAULT 'New Conversation',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_conversations_user_id ON conversations(user_id);

-- ============================================================
-- 4. messages 表
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    role ENUM('user','bot') NOT NULL,
    content TEXT NOT NULL,
    sources JSON,
    kg_references JSON,
    model_name VARCHAR(100),
    tokens_used INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- ============================================================
-- 5. system_config 表
-- ============================================================
CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. model_providers 表
-- ============================================================
CREATE TABLE IF NOT EXISTS model_providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider_name VARCHAR(50) UNIQUE NOT NULL,
    api_base_url VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. model_configs 表
-- ============================================================
CREATE TABLE IF NOT EXISTS model_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_type ENUM('chat','embedding') NOT NULL,
    system_prompt TEXT,
    embedding_dimension INT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES model_providers(id) ON DELETE CASCADE,
    UNIQUE KEY uk_provider_model (provider_id, model_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 8. model_presets 表
-- ============================================================
CREATE TABLE IF NOT EXISTS model_presets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model_config_id INT NOT NULL,
    scope ENUM('global','personal') NOT NULL DEFAULT 'personal',
    description VARCHAR(255),
    system_prompt TEXT,
    temperature DECIMAL(3,2) DEFAULT 0.70,
    top_p DECIMAL(3,2) DEFAULT 0.90,
    max_tokens INT DEFAULT 2048,
    created_by INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_config_id) REFERENCES model_configs(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 预置数据
-- ============================================================

-- 预置管理员账号 (密码: admin123)
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$VhgnspI4uFL.hNt8Env6/eSMib7ZzL2y1U8Sv5KMRxNEBH4w3sfR2', 'admin');

-- 预置系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
('temperature', '0.7', 'LLM 温度参数'),
('top_p', '0.9', 'LLM Top-P 参数'),
('max_tokens', '2048', 'LLM 最大 Token 数'),
('top_k', '5', '向量检索返回数'),
('similarity_threshold', '0.6', '相似度阈值'),
('chunk_size', '512', '文本分块大小（字符数）'),
('chunk_overlap', '128', '文本分块重叠长度（字符数）'),
('kg_enabled', 'true', '是否启用知识图谱增强'),
('history_rounds', '5', '多轮对话携带历史轮数');

-- 预置 DeepSeek 模型供应商（API Key 需部署时替换）
INSERT INTO model_providers (provider_name, api_base_url, api_key_encrypted) VALUES
('DeepSeek', 'https://api.deepseek.com/v1', '8q4udIELD32nF+4fEYYUUZiItvMP9241SnO3IalbH/g=');

-- 预置模型配置
INSERT INTO model_configs (provider_id, model_name, model_type, system_prompt, embedding_dimension, is_default, is_active) VALUES
(1, 'deepseek-chat', 'chat',
 '你是一个专业的企业知识库助手，请根据以下参考资料回答用户的问题。\n\n## 参考资料\n{context}\n\n## 对话历史\n{history}\n\n## 回答要求\n1. 基于参考资料进行回答，不要编造信息\n2. 如果参考资料中没有相关信息，请明确说明\n3. 回答结构清晰，使用 markdown 格式\n4. 在回答末尾注明引用来源',
 NULL, TRUE, TRUE),
(1, 'deepseek-reasoner', 'chat',
 '你是一个逻辑推理专家，请基于提供的知识库内容进行深入分析和推理。\n\n## 参考资料\n{context}\n\n## 对话历史\n{history}',
 NULL, FALSE, TRUE),
(1, 'deepseek-embedding', 'embedding', NULL, 1536, TRUE, TRUE);

-- ============================================================
-- 11. token_usage 表（独立记录 token 消耗，不随文档/对话删除）
-- ============================================================
CREATE TABLE IF NOT EXISTS token_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type ENUM('chat','embedding') NOT NULL,
    tokens_used INT NOT NULL DEFAULT 0,
    source_type ENUM('qa','document') NOT NULL,
    source_id INT,
    source_name VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_token_usage_model ON token_usage(model_name, model_type);
CREATE INDEX idx_token_usage_source ON token_usage(source_type, source_id);
