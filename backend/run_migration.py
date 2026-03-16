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
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_summaries INT DEFAULT 1 AFTER avatar_url;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS action_item_alerts INT DEFAULT 1 AFTER email_summaries;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS product_updates INT DEFAULT 0 AFTER action_item_alerts;",
        
        # Table: meetings
        "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS audio_url VARCHAR(500) AFTER transcript;",
        "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS video_url VARCHAR(500) AFTER audio_url;"
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
