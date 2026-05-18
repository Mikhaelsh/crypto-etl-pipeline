import requests
import logging

# Use logger, to make tracing back from logs easier
logger = logging.getLogger(__name__)

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

def extract_coins(per_page: int = 50) -> list[dict]:
    """
    Fetch the top N cryptocurrencies by market cap from CoinGecko.
    Returns a list of raw dicts (one per coin).
    Raises an exception if the request fails, so main.py can catch it.
    """
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": 1,
        "sparkline": False,  # we don't need sparkline price data
    }

    logger.info(f"Requesting top {per_page} coins from CoinGecko...")

    try:
        # timeout=10 means: give up if the server doesn't respond in 10 seconds.
        # Without a timeout, a slow server could hang your pipeline forever.
        response = requests.get(COINGECKO_URL, params=params, timeout=10)

        # raise_for_status() throws an HTTPError if the status code is 4xx or 5xx.
        # Cleaner than manually checking response.status_code == 200.
        response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.error("Request timed out after 10 seconds.")
        raise
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to CoinGecko. Check your internet connection.")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from CoinGecko: {e}")
        raise

    data = response.json()
    logger.info(f"Successfully extracted {len(data)} coins.")
    return data