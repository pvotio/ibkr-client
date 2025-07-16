# IBKR Contract Metadata Scraper

## Overview

This project is a high-concurrency web scraper for retrieving contract metadata from Interactive Brokers (IBKR) product pages. It extracts key financial instrument attributes—including ISIN, CONID, asset type, and exchange details—for a predefined list of tickers. The data is normalized and stored in a Microsoft SQL Server database for downstream use.

## Key Features

- Multithreaded and multiprocess parallelization
- Robust retry and backoff logic for web requests
- Contract metadata extraction using HTML parsing
- Flexible configuration via `.env`
- SQL Server integration for persistent storage

## Source of Data

The scraper targets IBKR's official product pages, using pre-configured URLs provided in `tickers.json`. These pages are publicly accessible and contain detailed product contract metadata embedded within HTML tables.

Example URL format:
```
https://www.interactivebrokers.com/en/index.php?f=2222&conid=XYZ
```

## Extracted Fields

| Field               | Description                           |
|--------------------|---------------------------------------|
| `ticker`           | Ticker symbol and exchange suffix     |
| `name`             | Company or asset name (if present)    |
| `currency`         | Trading currency                      |
| `exchange`         | Official exchange name                |
| `primary_exchange` | First exchange in the parsed field    |
| `contract_type`    | Security type (e.g. Stock, ETF)       |
| `country`          | Region or country of origin           |
| `closing_price`    | Last known trading price              |
| `conid`            | IBKR contract ID                      |
| `isin`             | ISIN identifier                       |
| `assetid`          | IBKR internal asset ID                |
| `timestamp_created_utc` | UTC timestamp of ingestion     |

## Directory Structure

```
ibkr-client-main/
├── main.py                       # Entrypoint: scraping + transformation + DB write
├── scraper/
│   ├── ibkr.py                   # Core scraper logic
│   ├── request.py                # Retry-enabled HTTP wrapper
│   ├── tickers.json              # Input ticker list (symbol, exchange, url)
│   └── useragents.txt            # Optional: rotating User-Agent pool
├── transformer/
│   └── agent.py                  # Data normalization and cleansing
├── database/
│   └── mssql.py                  # SQL Server loader
├── config/
│   ├── settings.py               # Environment variable parser
│   └── logger.py                 # Unified logging
├── .env.sample                   # Template for environment variables
├── Dockerfile                    # Docker image support
└── requirements.txt              # Dependencies
```

## Environment Configuration

Create a `.env` file based on `.env.sample` and fill in required fields:

| Variable               | Purpose                          |
|------------------------|----------------------------------|
| `LOG_LEVEL`            | Logging verbosity (e.g. DEBUG)   |
| `THREAD_COUNT`         | Threads per process              |
| `OUTPUT_TABLE`         | SQL Server table for output      |
| `INSERTER_MAX_RETRIES` | DB retry attempts                |
| `REQUEST_MAX_RETRIES`  | Web retry attempts               |
| `REQUEST_BACKOFF_FACTOR` | Backoff multiplier for retries |
| `MSSQL_*`              | SQL Server connection info       |
| `BRIGHTDATA_*`         | Optional proxy configuration     |

## Usage

### Locally

```bash
pip install -r requirements.txt
cp .env.sample .env  # Edit with real credentials
python main.py
```

### Using Docker

```bash
docker build -t ibkr-client .
docker run --env-file .env ibkr-client
```

## Logging & Monitoring

All processing steps are logged, including:
- Scraper startup
- Ticker processing
- Transformation summary
- Database insertion status

## License

This project is licensed under the MIT License. Use of IBKR web data must comply with their public data usage policies.
