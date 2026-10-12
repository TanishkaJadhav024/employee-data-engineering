
import logging

logger = logging.getLogger(__name__)


def create_target_table(connection):
    """Create the target table if it does not already exist."""

    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees_backup (
                employee_id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                department VARCHAR(100),
                salary NUMERIC
            );
        """)

    logger.info("Target table created successfully")


def copy_employees(connection, batch_size=3):
    """Copy employees from source to target in batches."""

    total_rows = 0

    with connection.cursor() as source_cursor:
        with connection.cursor() as target_cursor:

            source_cursor.execute("""
                SELECT employee_id, name, department, salary
                FROM employees
                ORDER BY employee_id;
            """)

            while True:
                employees = source_cursor.fetchmany(batch_size)

                if not employees:
                    break

                target_cursor.executemany("""
                    INSERT INTO employees_backup
                        (employee_id, name, department, salary)
                    VALUES
                        (%s, %s, %s, %s)
                    ON CONFLICT (employee_id)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        department = EXCLUDED.department,
                        salary = EXCLUDED.salary;
                """, employees)

                total_rows += len(employees)

                logger.info("Processed %d rows", total_rows)

    logger.info(
        "Employees copied successfully: %d rows",
        total_rows,
    )


def delete_missing_employees(connection):
    """Delete target rows that no longer exist in the source table."""

    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM employees_backup
            WHERE NOT EXISTS (
                SELECT 1
                FROM employees
                WHERE employees.employee_id =
                      employees_backup.employee_id
            );
        """)

        deleted_rows = cursor.rowcount

    logger.info("Deleted %d rows from backup", deleted_rows)


def row_count_validation(connection):
    """Compare source and target row counts."""

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM employees;")
        source_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM employees_backup;")
        target_count = cursor.fetchone()[0]

    if source_count == target_count:
        logger.info(
            "Row count validation successful: source=%d, target=%d",
            source_count,
            target_count,
        )
        return True

    logger.warning(
        "Row count mismatch: source=%d, target=%d",
        source_count,
        target_count,
    )
    return False


def data_validation(connection):
    """Compare source and target employee data."""

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT employee_id, name, department, salary
            FROM employees
            ORDER BY employee_id;
        """)
        source_rows = cursor.fetchall()

        cursor.execute("""
            SELECT employee_id, name, department, salary
            FROM employees_backup
            ORDER BY employee_id;
        """)
        target_rows = cursor.fetchall()

    source_data = {
        row[0]: row
        for row in source_rows
    }

    target_data = {
        row[0]: row
        for row in target_rows
    }

    if source_data == target_data:
        logger.info("Data validation successful")
        return True

    logger.warning("Data validation failed")

    all_employee_ids = source_data.keys() | target_data.keys()

    for employee_id in sorted(all_employee_ids):
        source_row = source_data.get(employee_id)
        target_row = target_data.get(employee_id)

        if source_row != target_row:
            logger.warning(
                "Data mismatch for employee_id=%s",
                employee_id,
            )
            logger.warning("Source row: %s", source_row)
            logger.warning("Target row: %s", target_row)

    return False

