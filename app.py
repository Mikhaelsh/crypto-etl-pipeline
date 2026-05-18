# app.py

import logging
import subprocess
from flask import Flask, render_template, jsonify
from sqlalchemy import text
from load import get_db_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
engine = get_db_engine()


@app.route("/")
def index():
    """
    Main dashboard page.
    Reads the latest snapshot from MySQL and passes it to the HTML template.
    """
    with engine.connect() as conn:
        # We only want the most recent ingestion run.
        # This subquery finds the latest ingested_at timestamp,
        # then the outer query filters to only rows from that run.
        result = conn.execute(text("""
            SELECT *
            FROM coin_prices
            WHERE ingested_at = (
                SELECT MAX(ingested_at) FROM coin_prices
            )
            ORDER BY market_cap DESC
        """))
        coins = result.mappings().all()

    logger.info(f"Dashboard loaded {len(coins)} coins.")
    return render_template("index.html", coins=coins)


@app.route("/run-pipeline", methods=["POST"])
def run_pipeline():
    """
    Triggers main.py as a subprocess when the user clicks 'Run Pipeline'.
    subprocess.run() waits for it to finish before responding.
    """
    try:
        logger.info("Pipeline triggered from dashboard.")
        subprocess.run(["python", "main.py"], check=True)
        return jsonify({"status": "success", "message": "Pipeline ran successfully."})
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline failed: {e}")
        return jsonify({"status": "error", "message": "Pipeline failed. Check logs."}), 500


if __name__ == "__main__":
    # debug=True means Flask auto-reloads when you save changes.
    # Never use debug=True in production.
    app.run(debug=True)