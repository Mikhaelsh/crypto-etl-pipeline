# load.py

import logging
import os
import pandas as pd
from datetime import timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# load_dotenv() reads your .env file and injects each line as an
# environment variable. After this call, os.getenv("DB_HOST") works.
# If .env doesn't exist it fails silently — so we validate below.
load_dotenv()

def get_db_engine():
    """
    Reads credentials from environment variables and returns a
    SQLAlchemy engine connected to MySQL.
    Raises a clear error if any credential is missing.
    """
    host     = os.getenv("DB_HOST")
    port     = os.getenv("DB_PORT", "3306")  # 3306 is MySQL's default port
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    db_name  = os.getenv("DB_NAME")

    # Validate that nothing is missing.
    # os.getenv() returns None silently if a variable isn't set —
    # without this check you'd get a cryptic SQLAlchemy error instead
    # of a clear message about what's wrong.
    missing = [k for k, v in {
        "DB_HOST": host,
        "DB_USER": user,
        "DB_PASSWORD": password,
        "DB_NAME": db_name,
    }.items() if v is None]

    if missing:
        raise EnvironmentError(f"Missing required environment variables: {missing}")

    # The connection string format SQLAlchemy uses for MySQL:
    # dialect+driver://user:password@host:port/database
    # mysqlconnector is the driver from mysql-connector-python
    connection_string = (
        f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db_name}"
    )

    logger.info(f"Connecting to MySQL at {host}:{port}/{db_name}...")

    try:
        engine = create_engine(connection_string)

        # .connect() actually tests the connection — create_engine() alone
        # is lazy and won't fail even with wrong credentials.
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("Database connection successful.")
        return engine

    except SQLAlchemyError as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


def load_coins(df: pd.DataFrame, engine) -> None:
    """
    Appends the cleaned DataFrame to the coin_prices table in MySQL.
    Creates the table automatically if it doesn't exist.
    """
    table_name = "coin_prices"

    try:
        # to_sql() does the heavy lifting:
        # - if_exists="append" adds new rows without touching existing ones
        # - if_exists="replace" would DROP and recreate the table — dangerous
        # - if_exists="fail" would error if the table exists — useless here
        # - index=False means don't write the DataFrame's row index as a column
        # - method="multi" batches inserts for better performance
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="append",
            index=False,
            method="multi",
        )

        logger.info(f"Successfully loaded {len(df)} rows into `{table_name}`.")

    except SQLAlchemyError as e:
        logger.error(f"Failed to write to database: {e}")
        raise