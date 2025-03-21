import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connect to SQLite
sqlite_conn = sqlite3.connect("group-project-f24-50-shades-of-gradient-descent/data/movie21.db")
sqlite_cursor = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST")
)
pg_cursor = pg_conn.cursor()

# Batch processing parameters
batch_size = 1000000  # Number of records per batch
offset = 0  # Start from the first record

while True:
    # Fetch batch of records from SQLite
    sqlite_cursor.execute(f"SELECT * FROM stream LIMIT {batch_size} OFFSET {offset}")
    rows = sqlite_cursor.fetchall()

    # Stop when there are no more records
    if not rows:
        break

    # Insert batch into PostgreSQL (ignore duplicates)
    pg_cursor.executemany(
        "INSERT INTO stream (id, user_id, movie_id, time, filename) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        rows
    )

    pg_conn.commit()
    offset += batch_size
    print(f"Migrated {offset} records...")

# 設定批量處理的大小
batch_size = 10000
offset = 0

while True:
    # 讀取 SQLite 的 rating 資料表
    sqlite_cursor.execute(f"SELECT id, user_id, movie_id, time, rating FROM rating LIMIT {batch_size} OFFSET {offset}")
    rows = sqlite_cursor.fetchall()

    if not rows:  # 如果沒有更多資料，則結束
        break

    # 批量插入 PostgreSQL，防止重複資料
    pg_cursor.executemany(
        "INSERT INTO rating (id, user_id, movie_id, time, rating) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        rows
    )

    pg_conn.commit()
    offset += batch_size
    print(f"Migrated {offset} records...")

# Close database connections
sqlite_cursor.close()
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()
