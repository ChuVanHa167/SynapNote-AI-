from pathlib import Path

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/synapnote_ai")

engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    result = connection.execute(text("SELECT id, title, status, audio_url, video_url FROM meetings ORDER BY created_at DESC LIMIT 5"))
    print(f"{'ID':<36} | {'Title':<20} | {'Status':<12} | {'Audio':<20} | {'Video':<20}")
    print("-" * 120)
    for row in result:
        print(f"{row[0]:<36} | {row[1]:<20} | {row[2]:<12} | {str(row[3]):<20} | {str(row[4]):<20}")
