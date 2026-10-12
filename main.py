import logging
import logging_config

from database import get_connection
from scd_operations import load_employees_scd

from table_operations import (
    create_target_table,
    copy_employees,
    row_count_validation,
    data_validation
    # delete_missing_employees
)

logger= logging.getLogger(__name__)

def main():
    
    connection=get_connection()
    try:
        # from line 22-28->logic for scd
        logger.info("SCD pipeline started")
        connection = get_connection()
        logger.info("Database connection established") 
        inserted_count, changed_count = load_employees_scd(connection)
        connection.commit()
        logger.info("Database transaction committed")
        logger.info( "SCD pipeline completed successfully: inserted=%d, changed=%d", inserted_count, changed_count, )
        # create_target_table(connection)
        # logger.info("Database conection established")

        # copy_employees(connection)
        # logger.info("Data copied and inserted successfully")

        # row_count_validation(connection)
        # data_validation(connection)
        # # delete_missing_employees()

        # connection.commit()
        # logger.info("Database transactions committed")

        # logger.info("Pipeline completed successfully")

    except Exception:
        if connection is not None: 
            connection.rollback()
            logger.warning("Database transaction rolled back") 
        logger.exception("SCD pipeline failed") 
    finally: 
        if connection is not None: 
            connection.close() 
            logger.info("Database connection closed")
if __name__ == "__main__":
    main()