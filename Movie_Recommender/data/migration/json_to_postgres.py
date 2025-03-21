import json
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST")
)
cursor = conn.cursor()

# Read JSONL file and insert into "movie" table
with open("movie.json", "r") as f:
    movie_data = [json.loads(line) for line in f]  # Read JSONL format file

# Batch insert into "movie" table
for row in movie_data:
    cursor.execute(
        "INSERT INTO movie (movie_id, json_data) VALUES (%s, %s) ON CONFLICT (movie_id) DO NOTHING",
        (row["movie_id"], json.dumps(row["json"]))  # Convert to JSONB
    )

# Read JSONL file and insert into "user_info" table
with open("user.json", "r") as f:
    user_data = [json.loads(line) for line in f]  # Read JSONL format file

# Batch insert into "user_info" table
for row in user_data:
    cursor.execute(
        "INSERT INTO user_info (user_id, json_data) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
        (row["user_id"], json.dumps(row["json"]))  # Convert to JSONB
    )

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()
