# transform.py

import pandas as pd
import logging
import pytz
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# These are the exact field names CoinGecko returns in the JSON.
# You know these by either reading the docs or printing the raw response.
COLUMNS_TO_KEEP = [
    "id",
    "symbol",
    "name",
    "current_price",
    "market_cap",
    "total_volume",
    "price_change_percentage_24h",
    "last_updated",
]

# Rename map: CoinGecko name → our preferred name.
# In this case they're already snake_case so it's mostly for explicitness
# and future-proofing if the API ever changes a field name.
COLUMN_RENAMES = {
    "id": "id",
    "symbol": "symbol",
    "name": "name",
    "current_price": "current_price",
    "market_cap": "market_cap",
    "total_volume": "total_volume",
    "price_change_percentage_24h": "price_changes_in_24h",  # shortened
    "last_updated": "last_updated",
}

def transform_coins(raw_data: list[dict]) -> pd.DataFrame:
    """
    Takes raw CoinGecko JSON (list of dicts) and returns a clean DataFrame.
    """
    logger.info(f"Starting transformation on {len(raw_data)} records.")

    # Step 1: Load into a DataFrame.
    # pandas can directly consume a list of dicts — each dict becomes a row.
    df = pd.DataFrame(raw_data)

    # Step 2: Keep only the columns we need.
    # This also protects us if CoinGecko adds new fields later — we ignore them.
    df = df[COLUMNS_TO_KEEP]

    # Step 3: Rename columns.
    df = df.rename(columns=COLUMN_RENAMES)

    # Step 4: Parse last_updated from an ISO 8601 string into a real datetime.
    # utc=True tells pandas to make it timezone-aware (UTC).
    # Without this it's just a plain string — useless for time-based queries.
    df["last_updated"] = pd.to_datetime(df["last_updated"], utc=True).dt.tz_convert("Asia/Jakarta").dt.tz_localize(None)

    # Step 5: Add ingested_at — the moment this pipeline run executed.
    # All 50 rows get the same timestamp since they were all ingested together.
    # timezone.utc ensures we're always storing UTC, never a local timezone.
    wib = pytz.timezone("Asia/Jakarta")
    df["ingested_at"] = datetime.now(wib).replace(tzinfo=None)

    # Step 6: Drop any rows where any value is null.
    rows_before = len(df)
    df = df.dropna()
    rows_after = len(df)

    if rows_before != rows_after:
        logger.warning(f"Dropped {rows_before - rows_after} rows with null values.")

    logger.info(f"Transformation complete. {rows_after} clean rows ready to load.")
    return df