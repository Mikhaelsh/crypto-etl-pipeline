![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20Dashboard-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange?logo=mysql)
![pandas](https://img.shields.io/badge/pandas-Transform-lightblue?logo=pandas)

# Crypto ETL Pipeline

A data engineering portfolio project that extracts live cryptocurrency market data from the CoinGecko public API, transforms it using pandas, loads it into a MySQL database, and displays it on a Flask web dashboard.

---

## What It Does

The pipeline runs in three stages:

**Extract** — Sends an HTTP GET request to the CoinGecko `/coins/markets` endpoint and fetches the top 50 cryptocurrencies ranked by market cap. The response is a list of JSON objects, one per coin.

**Transform** — Loads the raw JSON into a pandas DataFrame. Filters down to 8 relevant columns, renames them to clean snake_case, parses the `last_updated` field from an ISO 8601 string into a proper timezone-aware datetime, rounds the 24h price change to 2 decimal places, adds an `ingested_at` timestamp marking when the pipeline ran, and drops any rows with null values.

**Load** — Connects to a MySQL database using SQLAlchemy and appends the cleaned DataFrame to a table called `coin_prices`. If the table does not exist yet, it is created automatically. Each pipeline run adds 50 new rows without overwriting historical data, so the table accumulates a full history of every run.

A Flask web dashboard reads the most recent snapshot from MySQL and displays it as a formatted table with green/red price change indicators. A "Run Pipeline" button on the dashboard triggers the full ETL process on demand.

---

## Project Structure

```
crypto-etl/
│
├── extract.py          # Fetches raw data from CoinGecko API
├── transform.py        # Cleans and reshapes raw JSON into a DataFrame
├── load.py             # Connects to MySQL and writes the DataFrame
├── main.py             # Orchestrates the full ETL pipeline
├── app.py              # Flask web server and dashboard routes
│
├── templates/
│   └── index.html      # Dashboard HTML template
│
├── static/
│   └── style.css       # Dashboard styling
│
├── .env                # Your real credentials (never commit this)
├── .env.example        # Template showing required variables
├── .gitignore          # Ensures .env is never pushed to GitHub
└── requirements.txt    # Python dependencies
```

---

## Pipeline Architecture

```
CoinGecko API  (https://api.coingecko.com/api/v3/coins/markets)
      |
      |  raw JSON (list of dicts, ~25 fields per coin)
      v
  extract.py
      |  requests.get() with timeout and error handling
      |
      v
 transform.py
      |  pandas: filter columns, rename, parse datetime, dropna, add ingested_at
      |
      v
    load.py
      |  SQLAlchemy + mysql-connector: append to coin_prices table
      |
      v
  MySQL Database (crypto_db.coin_prices)
      |
      v
   app.py  (Flask)
      |  SELECT * WHERE ingested_at = MAX(ingested_at)
      |
      v
  Browser Dashboard (http://127.0.0.1:5000)
```

---

## Prerequisites

- Python 3.10 or higher
- XAMPP (or any MySQL installation) running locally
- Git

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/crypto-etl.git
cd crypto-etl
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up MySQL

If you are using XAMPP:

1. Open the XAMPP Control Panel and click **Start** next to MySQL
2. Go to `http://localhost/phpmyadmin` in your browser
3. Click **New** in the left sidebar
4. Name the database `crypto_db` and click **Create**

The `coin_prices` table will be created automatically on the first pipeline run.

### 4. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` and set your values:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=crypto_db
```

For XAMPP, `DB_PASSWORD` is blank by default.

### 5. Run the pipeline

```bash
python main.py
```

You should see log output for each step. On success, 49 to 50 rows will be written to the `coin_prices` table.

### 6. Start the dashboard

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## Running the Pipeline from the Dashboard

Click the **Run Pipeline** button in the top right corner of the dashboard. The button calls the `/run-pipeline` Flask route, which executes `main.py` as a subprocess and waits for it to finish. Refresh the page after it completes to see the updated data.

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DB_HOST` | MySQL host address | `localhost` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | MySQL username | `root` |
| `DB_PASSWORD` | MySQL password | *(blank for XAMPP default)* |
| `DB_NAME` | Database name | `crypto_db` |

---

## Key Design Decisions

**Credentials are stored in `.env`, never hardcoded.** The `python-dotenv` library loads them into environment variables at runtime. The `.env` file is listed in `.gitignore` so it is never pushed to version control.

**Column filtering happens before null checks.** The raw CoinGecko response contains fields like `roi` that are null for many coins. By selecting only the 8 needed columns first and then calling `dropna()`, the pipeline avoids dropping valid rows because of irrelevant null fields.

**`if_exists="append"` preserves history.** Every pipeline run adds new rows rather than overwriting the table. This means the database builds up a time series of market snapshots that could be used for trend analysis.

**The dashboard always shows the latest snapshot.** The SQL query filters by `WHERE ingested_at = (SELECT MAX(ingested_at) FROM coin_prices)` so historical rows from previous runs do not appear in the table alongside current data.

**UTC is used everywhere.** Both `pd.to_datetime(..., utc=True)` and `datetime.now(timezone.utc)` ensure all timestamps are timezone-aware and stored in UTC, avoiding bugs caused by local machine timezone differences.

---

## Technologies Used

| Tool | Purpose |
|---|---|
| `requests` | HTTP calls to CoinGecko API |
| `pandas` | Data cleaning and transformation |
| `SQLAlchemy` | Database ORM and connection management |
| `mysql-connector-python` | MySQL driver used by SQLAlchemy |
| `python-dotenv` | Loading credentials from `.env` |
| `Flask` | Web server and dashboard routing |
| `logging` | Pipeline observability and debugging |
