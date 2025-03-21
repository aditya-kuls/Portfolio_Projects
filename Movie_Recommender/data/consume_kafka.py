import os
import psycopg2
import re
import logging
from kafka import KafkaConsumer
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="consumer_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Kafka settings
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))  # Default to 100 if not set

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    group_id=KAFKA_GROUP_ID,
    auto_offset_reset="latest",
    value_deserializer=lambda x: x.decode("utf-8"),
)

# PostgreSQL settings
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
}


def connect_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None


def parse_message(message):
    """Parse Kafka message and return structured data."""

    try:
        parts = message.split(",")
        if len(parts) != 3:
            raise ValueError("Invalid format: message does not have exactly 3 parts")

        timestamp = parts[0].strip()
        user_id = parts[1].strip()
        request = parts[2].strip()

        # Validate timestamp format
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise ValueError("Invalid timestamp format")

        # Validate user_id
        if not user_id.isdigit():
            raise ValueError("user_id is not a valid number")

        # Determine message type
        data = {"time": dt.strftime("%Y-%m-%d %H:%M:%S"), "user_id": user_id}

        match_stream = re.match(r"GET /data/m/(?P<movie_id>.+)/(?P<filename>.+)", request)
        match_rating = re.match(r"GET /rate/(?P<movie_id>.+)=(?P<rating>\d+)", request)

        if match_stream:
            data.update({
                "movie_id": match_stream.group("movie_id"),
                "filename": match_stream.group("filename"),
                "type": "stream"
            })
        elif match_rating:
            data.update({
                "movie_id": match_rating.group("movie_id"),
                "rating": int(match_rating.group("rating")),
                "type": "rating"
            })
        else:
            raise ValueError("Invalid request format")

        return data
    except Exception as e:
        logging.error(f"Message parsing failed: {e} | Raw message: {message}")
        return None


def check_existing_records(conn, batch, table):
    """Check if records already exist in the database and filter out duplicates."""
    if not batch:
        return []

    try:
        cursor = conn.cursor()
        if table == "stream":
            query = "SELECT user_id, movie_id, time, filename FROM stream WHERE (user_id, movie_id, time, filename) IN %s"
            values = tuple((d["user_id"], d["movie_id"], d["time"], d["filename"]) for d in batch)
        else:
            query = "SELECT user_id, movie_id, time, rating FROM rating WHERE (user_id, movie_id, time, rating) IN %s"
            values = tuple((d["user_id"], d["movie_id"], d["time"], d["rating"]) for d in batch)

        cursor.execute(query, (values,))
        existing_records = set(cursor.fetchall())
        cursor.close()

        # Filter out duplicates
        new_batch = [d for d in batch if tuple(d.values()) not in existing_records]
        return new_batch
    except Exception as e:
        logging.error(f"Error checking existing records: {e}")
        return batch


def insert_into_db(batch):
    """Insert parsed Kafka data into the database, avoiding duplicates."""
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()

            # Separate data by type
            stream_data = [d for d in batch if d["type"] == "stream"]
            rating_data = [d for d in batch if d["type"] == "rating"]
            filtered_stream = []
            filtered_rating = []

            if stream_data:
                filtered_stream = check_existing_records(conn, stream_data, "stream")
                if filtered_stream:
                    query = "INSERT INTO stream (user_id, movie_id, time, filename) VALUES %s"
                    values = ",".join(
                        cursor.mogrify("(%s, %s, %s, %s)",
                                       (d["user_id"], d["movie_id"], d["time"], d["filename"])).decode('utf-8')
                        for d in filtered_stream
                    )
                    cursor.execute(query % values)

            if rating_data:
                filtered_rating = check_existing_records(conn, rating_data, "rating")
                if filtered_rating:
                    query = "INSERT INTO rating (user_id, movie_id, time, rating) VALUES %s"
                    values = ",".join(
                        cursor.mogrify("(%s, %s, %s, %s)",
                                       (d["user_id"], d["movie_id"], d["time"], d["rating"])).decode('utf-8')
                        for d in filtered_rating
                    )
                    cursor.execute(query % values)

            conn.commit()
            cursor.close()
            print(f"Inserted {len(filtered_stream)} stream records and {len(filtered_rating)} rating records")

        except Exception as e:
            logging.error(f"Batch insert failed: {e} | Data: {batch}")
        finally:
            conn.close()


print("Starting Kafka consumer...")
message_batch = []

try:
    for msg in consumer:
        raw_data = msg.value
        parsed_data = parse_message(raw_data)
        if parsed_data:
            message_batch.append(parsed_data)

        if len(message_batch) >= BATCH_SIZE:
            insert_into_db(message_batch)
            message_batch = []

except KeyboardInterrupt:
    print("Consumer manually stopped")
finally:
    if message_batch:
        insert_into_db(message_batch)
    consumer.close()
