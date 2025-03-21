# data_loader.py

import psycopg2
import pandas as pd
from config import DB_CONFIG


def get_connection():
    """Establish and return a database connection."""
    return psycopg2.connect(**DB_CONFIG)


def fetch_data(query):
    """Fetch data from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()  # Close cursor before closing connection
    conn.close()
    return pd.DataFrame(data, columns=columns)


def load_ratings():
    """Load ratings data from the database."""
    return fetch_data("SELECT * FROM rating;")


def load_movies():
    """Load movies data from the database."""
    return fetch_data("SELECT * FROM movie;")


def load_users():
    """Load user information from the database."""
    return fetch_data("SELECT * FROM user_info;")
