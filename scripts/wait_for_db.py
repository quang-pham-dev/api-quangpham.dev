import time
import psycopg2
from src.config.settings import settings


def wait_for_db():
    max_tries = 60  # 5 minutes
    while max_tries > 0:
        try:
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                dbname=settings.DB_NAME,
            )
            conn.close()
            print("Database is ready!")
            return True
        except psycopg2.OperationalError:
            max_tries -= 1
            print(f"Waiting for database... {max_tries} tries left")
            time.sleep(5)

    print("Could not connect to database")
    return False


if __name__ == "__main__":
    wait_for_db()
