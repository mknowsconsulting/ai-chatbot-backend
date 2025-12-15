-- ============================================
-- AI CHATBOT DATABASE SCHEMA
-- SQLite Database for Chat History & Analytics
-- Version: 1.0.0
-- ============================================

-- ============================================
-- 1. CHAT SESSIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id INTEGER,                    -- NULL for public, value for student/admin
    nim TEXT,                           -- Student NIM (NULL for public/admin)
    user_role TEXT CHECK(user_role IN ('public', 'student', 'admin')) NOT NULL,
    language TEXT DEFAULT 'id' CHECK(language IN ('id', 'en')),
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address TEXT
);

CREATE INDEX IF NOT EXISTS idx_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_role ON chat_sessions(user_role);
CREATE INDEX IF NOT EXISTS idx_last_activity ON chat_sessions(last_activity);

-- ============================================
-- 2. CHAT MESSAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant', 'system')) NOT NULL,
    content TEXT NOT NULL,
    language TEXT,
    tokens_used INTEGER DEFAULT 0,      -- For cost tracking
    response_time_ms INTEGER,           -- Performance tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_created ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_role ON chat_messages(role);

-- ============================================
-- 3. FAQ METADATA TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS faq_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT,
    language TEXT DEFAULT 'id' CHECK(language IN ('id', 'en')),
    qdrant_collection TEXT,             -- Which Qdrant collection
    qdrant_id TEXT,                     -- ID in Qdrant
    usage_count INTEGER DEFAULT 0,      -- Track FAQ popularity
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_faq_language ON faq_metadata(language);
CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_metadata(category);
CREATE INDEX IF NOT EXISTS idx_faq_usage ON faq_metadata(usage_count DESC);

-- ============================================
-- 4. RATE LIMITS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL,           -- session_id or user_id
    user_role TEXT,
    date DATE NOT NULL,
    request_count INTEGER DEFAULT 0,
    last_request TIMESTAMP,
    UNIQUE(identifier, date)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_check ON rate_limits(identifier, date);
CREATE INDEX IF NOT EXISTS idx_rate_limit_date ON rate_limits(date);

-- ============================================
-- 5. CHAT ANALYTICS TABLE (Daily Aggregation)
-- ============================================
CREATE TABLE IF NOT EXISTS chat_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    user_role TEXT,
    language TEXT,
    total_sessions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    total_tokens_used INTEGER DEFAULT 0,
    deepseek_cost_usd DECIMAL(10,4) DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    UNIQUE(date, user_role, language)
);

CREATE INDEX IF NOT EXISTS idx_analytics_date ON chat_analytics(date);
CREATE INDEX IF NOT EXISTS idx_analytics_role ON chat_analytics(user_role);
CREATE INDEX IF NOT EXISTS idx_analytics_language ON chat_analytics(language);

-- ============================================
-- 6. POPULAR QUESTIONS TABLE (Auto-learned)
-- ============================================
CREATE TABLE IF NOT EXISTS popular_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    normalized_question TEXT,           -- Lowercase, cleaned version
    ask_count INTEGER DEFAULT 0,
    language TEXT,
    user_role TEXT,
    suggested_as_faq BOOLEAN DEFAULT FALSE,
    last_asked TIMESTAMP,
    UNIQUE(normalized_question, language)
);

CREATE INDEX IF NOT EXISTS idx_popular_q_count ON popular_questions(ask_count DESC);
CREATE INDEX IF NOT EXISTS idx_popular_q_lang ON popular_questions(language);
CREATE INDEX IF NOT EXISTS idx_popular_q_role ON popular_questions(user_role);

-- ============================================
-- 7. ADMIN USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_active ON admin_users(is_active);

-- ============================================
-- 8. SYSTEM LOGS TABLE (Optional - for debugging)
-- ============================================
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT CHECK(log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    module TEXT,
    message TEXT NOT NULL,
    details TEXT,                       -- JSON details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_created ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_module ON system_logs(module);

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Password hash for "admin123" using bcrypt
INSERT OR IGNORE INTO admin_users (username, email, password_hash, full_name, is_active)
VALUES (
    'admin',
    'admin@kampusgratis.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5gGKl7HxUIlVO',
    'System Administrator',
    TRUE
);

-- ============================================
-- END OF SCHEMA
-- ============================================
