import logging

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session

from db.base import Base
from config import config

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    pool_size=10,  # Customize as per your need
    max_overflow=20,
    echo=config.SQLALCHEMY_ECHO
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def inspect_db(engine):
    inspector = inspect(engine)
    schemas = inspector.get_schema_names()
    print("Schemas:")
    for schema in schemas:
        print(f" - {schema}")

    for schema in schemas:
        tables = inspector.get_table_names(schema=schema)
        print(f"Tables in schema '{schema}':")
        for table in tables:
            print(f" - {table}")

def init_db():
    logging.debug(f"Database URL: {config.SQLALCHEMY_DATABASE_URI}")
    # Uncomment the following line to inspect the database
    # inspect_db(engine) 
    print(config.SQLALCHEMY_DATABASE_URI)
    # Import all models here to register them on the metadata
    logging.info("Initializing database")
    Base.metadata.create_all(bind=engine)
    logging.info("Database initialized")
