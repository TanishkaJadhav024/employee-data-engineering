# Employee Incremental ETL Pipeline

A Python and PostgreSQL learning project that demonstrates incremental ETL processing and Slowly Changing Dimensions (SCD).

## Features

- Incremental extraction using source update timestamps
- SCD Type 2: stores current and historical versions in one table
- SCD Type 4: separates current records from historical records
- Watermark-based progress tracking for each pipeline
- Transaction handling with commit and rollback
- Structured logging to the console and a local log file

## Technologies

- Python
- PostgreSQL
- Psycopg
- python-dotenv

## Pipelines

- `main.py` — runs the SCD Type 2 pipeline
- `main_type4.py` — runs the SCD Type 4 pipeline

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies from `requirements.txt`.
3. Create a local `.env` file using `.env.example` as a template.
4. Create the required PostgreSQL tables and initialize the watermarks.
5. Run the desired pipeline.

## Learning objectives

This project explores incremental loading, historical data preservation, watermark management, database transactions, and logging.

## Limitations

This is a learning project. Timestamp-based incremental loading with an overlap window has limitations, and source deletions and intermediate changes between runs are not fully handled.
