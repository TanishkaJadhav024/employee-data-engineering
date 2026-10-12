
import logging

from database import get_connection
from logging_config import *
from scd_type4_operations import load_employees_scd_type4

logger = logging.getLogger(__name__)


def main():
    connection = None

    try:
        connection = get_connection()

        logger.info("Starting SCD Type 4 pipeline")

        inserted_count, changed_count = (
            load_employees_scd_type4(connection)
        )

        connection.commit()

        logger.info(
            "SCD Type 4 pipeline completed successfully: "
            "inserted=%d, changed=%d",
            inserted_count,
            changed_count,
        )

    except Exception:
        if connection is not None:
            connection.rollback()

        logger.exception("SCD Type 4 pipeline failed")
        raise

    finally:
        if connection is not None:
            connection.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    main()
