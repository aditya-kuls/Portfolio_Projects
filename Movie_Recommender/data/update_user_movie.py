import os
import psycopg2
import requests
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="database_update.log",
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

# API endpoints
USER_API_URL = "http://128.2.204.215:8080/user/"
MOVIE_API_URL = "http://128.2.204.215:8080/movie/"

# Function to fetch JSON data from API
def fetch_json_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for non-2xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed for {url}: {e}")
        return None

# Function to insert user data into the database
def insert_user(cursor, user_id, json_data):
    cursor.execute(
        "INSERT INTO user_info (user_id, json_data) VALUES (%s, %s)",
        (user_id, json.dumps(json_data)),
    )

# Function to insert movie data into the database
def insert_movie(cursor, movie_id, json_data):
    cursor.execute(
        "INSERT INTO movie (movie_id, json_data) VALUES (%s, %s)",
        (movie_id, json.dumps(json_data)),
    )

# Main function to check the stream table and update missing data
def update_user_movie_data():
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Find missing user_id in the user table
        cursor.execute("""
            SELECT DISTINCT s.user_id 
            FROM stream s 
            LEFT JOIN user_info u ON s.user_id = u.user_id 
            WHERE u.user_id IS NULL
        """)
        missing_users = [row[0] for row in cursor.fetchall()]

        # Find missing movie_id in the movie table
        cursor.execute("""
            SELECT DISTINCT s.movie_id 
            FROM stream s 
            LEFT JOIN movie m ON s.movie_id = m.movie_id 
            WHERE m.movie_id IS NULL
        """)
        missing_movies = [row[0] for row in cursor.fetchall()]

        inserted_users = 0
        inserted_movies = 0

        # Insert missing users
        for user_id in missing_users:
            logging.info(f"Fetching user {user_id} from API...")
            user_data = fetch_json_data(USER_API_URL + str(user_id))
            if user_data:
                insert_user(cursor, user_id, user_data)
                inserted_users += 1
                logging.info(f"Inserted user {user_id} into the database.")

        # Insert missing movies
        for movie_id in missing_movies:
            logging.info(f"Fetching movie {movie_id} from API...")
            movie_data = fetch_json_data(MOVIE_API_URL + str(movie_id))
            if movie_data:
                insert_movie(cursor, movie_id, movie_data)
                inserted_movies += 1
                logging.info(f"Inserted movie {movie_id} into the database.")

        # Commit changes and close connection
        conn.commit()
        cursor.close()
        conn.close()

        # Log summary
        logging.info(f"Database update completed: {inserted_users} users and {inserted_movies} movies inserted.")

    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")

# Run the update function
if __name__ == "__main__":
    update_user_movie_data()
