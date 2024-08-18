import os

class Config:
    # Construct the SQLALCHEMY_DATABASE_URI dynamically from environment variables
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'mydatabase')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True to log SQL queries

    # Custom configuration settings
    SOURCE_URL = "https://www.bethowen.ru/"

config = Config()
