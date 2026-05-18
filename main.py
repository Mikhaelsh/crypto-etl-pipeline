# main.py

import logging
from extract import extract_coins
from transform import transform_coins
from load import get_db_engine, load_coins

# Configure logging once here, at the entry point of the pipeline.
# All other modules use getLogger(__name__) which plug into this config
# automatically — you only need to set this up in one place.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def run_pipeline():
    logger.info("=" * 50)
    logger.info("Pipeline started.")

    # --- EXTRACT ---
    try:
        raw_data = extract_coins(per_page=50)
    except Exception as e:
        logger.error(f"Extract step failed: {e}")
        logger.error("Pipeline aborted.")
        return  # stop here, no point continuing without data

    # --- TRANSFORM ---
    try:
        clean_df = transform_coins(raw_data)
    except Exception as e:
        logger.error(f"Transform step failed: {e}")
        logger.error("Pipeline aborted.")
        return

    # --- LOAD ---
    try:
        engine = get_db_engine()
        load_coins(clean_df, engine)
    except Exception as e:
        logger.error(f"Load step failed: {e}")
        logger.error("Pipeline aborted.")
        return

    logger.info("Pipeline completed successfully.")
    logger.info("=" * 50)


if __name__ == "__main__":
    run_pipeline()