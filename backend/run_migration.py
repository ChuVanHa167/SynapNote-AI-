from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
# Adjusting to backend directory if running from root, or assume running from backend
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/synapnote_ai")

engine = create_engine(DATABASE_URL)

def run_migration():
    migrations = [
        # Table: users
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500) AFTER title;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS theme VARCHAR(10) DEFAULT 'dark' AFTER avatar_url;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_summaries INT DEFAULT 1 AFTER theme;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS action_item_alerts INT DEFAULT 1 AFTER email_summaries;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS product_updates INT DEFAULT 0 AFTER action_item_alerts;",
        
        # Table: meetings
        "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS audio_url VARCHAR(500) AFTER transcript;",
        "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS video_url VARCHAR(500) AFTER audio_url;",
        "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS link_url VARCHAR(500) AFTER video_url;",

        # Billing & Subscription tables
        """
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            name VARCHAR(50) NOT NULL,
            price_vnd INT NOT NULL,
            billing_cycle VARCHAR(20) DEFAULT 'monthly',
            meetings_limit INT NOT NULL,
            audio_hours_limit INT NOT NULL,
            features TEXT,
            is_active TINYINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            user_id VARCHAR(36) NOT NULL,
            plan_id VARCHAR(36) NOT NULL,
            status ENUM('active', 'cancelled', 'expired', 'pending') DEFAULT 'active',
            current_period_start TIMESTAMP NULL DEFAULT NULL,
            current_period_end TIMESTAMP NULL DEFAULT NULL,
            cancel_at_period_end TINYINT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS payment_methods (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            user_id VARCHAR(36) NOT NULL,
            type VARCHAR(50) NOT NULL,
            provider VARCHAR(50),
            last4 VARCHAR(4),
            expiry_month INT,
            expiry_year INT,
            is_default TINYINT DEFAULT 0,
            is_active TINYINT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS billing_history (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            user_id VARCHAR(36) NOT NULL,
            amount_vnd INT NOT NULL,
            description VARCHAR(255),
            status ENUM('success', 'failed', 'pending', 'refunded') DEFAULT 'pending',
            payment_method_id VARCHAR(36),
            invoice_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS usage_stats (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            user_id VARCHAR(36) NOT NULL,
            month INT NOT NULL,
            year INT NOT NULL,
            meetings_count INT DEFAULT 0,
            audio_hours_used DECIMAL(10,1) DEFAULT 0.0,
            ai_processing_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """,
        # Integrations table
        """
        CREATE TABLE IF NOT EXISTS user_integrations (
            id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
            user_id VARCHAR(36) NOT NULL,
            provider VARCHAR(50) NOT NULL,
            provider_name VARCHAR(100),
            status ENUM('connected', 'disconnected', 'error') DEFAULT 'disconnected',
            access_token TEXT,
            refresh_token TEXT,
            token_expires_at TIMESTAMP NULL DEFAULT NULL,
            settings TEXT,
            webhook_url VARCHAR(500),
            last_sync_at TIMESTAMP NULL DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
        );
        """,
    ]
    
    with engine.connect() as connection:
        for sql in migrations:
            try:
                connection.execute(text(sql))
                connection.commit()
                print(f"Executed: {sql}")
            except Exception as e:
                print(f"Error executing {sql}: {e}")

if __name__ == "__main__":
    run_migration()
