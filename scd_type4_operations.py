
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

PIPELINE_NAME = "employees_scd_type4"
OVERLAP_MINUTES = 5


def load_employees_scd_type4(connection):
    """Incrementally load employee data using SCD Type 4."""

    inserted_count = 0
    changed_count = 0

    with connection.cursor() as cursor:
        # Read the Type 4 watermark.
        cursor.execute(
            """
            SELECT last_loaded_at
            FROM etl_watermark
            WHERE pipeline_name = %s;
            """,
            (PIPELINE_NAME,),
        )

        watermark_row = cursor.fetchone()

        if watermark_row is None:
            raise RuntimeError(
                f"Watermark not initialized for {PIPELINE_NAME}"
            )

        last_loaded_at = watermark_row[0]
        lower_bound = last_loaded_at - timedelta(
            minutes=OVERLAP_MINUTES
        )

        # Capture the upper boundary for this run.
        cursor.execute("SELECT clock_timestamp();")
        upper_bound = cursor.fetchone()[0]

        logger.info(
            "SCD Type 4 started: lower_bound=%s, upper_bound=%s",
            lower_bound,
            upper_bound,
        )

        # Fetch changed source records.
        cursor.execute(
            """
            SELECT employee_id, name, department, salary
            FROM employees
            WHERE updated_at >= %s
              AND updated_at <= %s
            ORDER BY employee_id;
            """,
            (lower_bound, upper_bound),
        )

        source_rows = cursor.fetchall()

        for employee_id, name, department, salary in source_rows:
            cursor.execute(
                """
                SELECT name, department, salary
                FROM employees_current
                WHERE employee_id = %s;
                """,
                (employee_id,),
            )

            current_row = cursor.fetchone()

            # New employee: insert the current version.
            if current_row is None:
                cursor.execute(
                    """
                    INSERT INTO employees_current (
                        employee_id, name, department, salary,
                        effective_from
                    )
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (
                        employee_id,
                        name,
                        department,
                        salary,
                        upper_bound,
                    ),
                )

                inserted_count += 1
                continue

            # No tracked changes: skip this employee.
            if current_row == (name, department, salary):
                continue

            # Archive the previous current version exactly once.
            cursor.execute(
                """
                INSERT INTO employees_history (
                    employee_id, name, department, salary,
                    effective_from, effective_to
                )
                SELECT
                    employee_id, name, department, salary,
                    effective_from, %s
                FROM employees_current
                WHERE employee_id = %s;
                """,
                (upper_bound, employee_id),
            )

            # Update the current row with the latest values.
            cursor.execute(
                """
                UPDATE employees_current
                SET name = %s,
                    department = %s,
                    salary = %s,
                    effective_from = %s
                WHERE employee_id = %s;
                """,
                (
                    name,
                    department,
                    salary,
                    upper_bound,
                    employee_id,
                ),
            )

            changed_count += 1

        # Advance only the Type 4 watermark.
        cursor.execute(
            """
            UPDATE etl_watermark
            SET last_loaded_at = %s
            WHERE pipeline_name = %s;
            """,
            (upper_bound, PIPELINE_NAME),
        )

    logger.info(
        "SCD Type 4 completed: inserted=%d, changed=%d",
        inserted_count,
        changed_count,
    )

    return inserted_count, changed_count
