import os
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="stream_summary_update.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# PostgreSQL settings
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
}

# Function to merge stream data into stream_summary
def update_stream_summary():
    merge_query = """
    MERGE INTO stream_summary AS target
    USING (
        SELECT 
            MAX(time) AS latest_time,
            user_id,
            movie_id,
            COUNT(filename) AS file_count
        FROM stream
        GROUP BY user_id, movie_id
    ) AS source
    ON target.user_id = source.user_id AND target.movie_id = source.movie_id
    WHEN MATCHED THEN
        UPDATE SET 
            latest_time = source.latest_time,
            file_count = source.file_count
    WHEN NOT MATCHED THEN
        INSERT (latest_time, user_id, movie_id, file_count)
        VALUES (source.latest_time, source.user_id, source.movie_id, source.file_count);
    """
    conn = None
    cursor = None

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Execute the MERGE query
        cursor.execute(merge_query)

        # Commit the transaction
        conn.commit()

        # Log successful execution
        logging.info("Successfully merged stream data into stream_summary.")

    except psycopg2.Error as e:
        logging.error(f"Database error during merge: {e}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Run the merge function
if __name__ == "__main__":
    update_stream_summary()
