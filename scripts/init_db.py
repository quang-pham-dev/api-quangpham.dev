import subprocess
from src.core.database import db
from src.app import create_app


def init_database():
    app = create_app()
    with app.app_context():
        # Create database tables
        db.create_all()
        print("Database tables created!")

        # Apply migrations
        try:
            subprocess.run(["flask", "db", "init"], check=True)
        except subprocess.CalledProcessError:
            print("Migrations folder already exists")

        subprocess.run(
            ["flask", "db", "migrate", "-m", "Initial migration"], check=True
        )
        subprocess.run(["flask", "db", "upgrade"], check=True)
        print("Migrations applied successfully!")


if __name__ == "__main__":
    init_database()
