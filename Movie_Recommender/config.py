import os
from dotenv import load_dotenv

load_dotenv()

# DB_CONFIG = {
#     "dbname": os.environ["DB_NAME"],
#     "user": os.environ["DB_USER"],
#     "password": os.environ["DB_PASSWORD"],
#     "host": os.environ["DB_HOST"],
# }

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "test_db"),
    "user": os.getenv("DB_USER", "test_user"),
    "password": os.getenv("DB_PASSWORD", "test_password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}
