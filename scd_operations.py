#************************************After SDC Type 2**************************************
# import logging

# logger = logging.getLogger(__name__)


# def load_employees_scd(connection):
#     """Apply SCD Type 2 logic to employee records."""

#     inserted_count = 0
#     changed_count = 0

#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT employee_id, name, department, salary
#             FROM employees
#             ORDER BY employee_id;
#         """)

#         source_rows = cursor.fetchall()

#         for employee_id, name, department, salary in source_rows:
#             cursor.execute("""
#                 SELECT name, department, salary
#                 FROM employees_scd
#                 WHERE employee_id = %s
#                   AND is_current = TRUE;
#             """, (employee_id,))

#             current_row = cursor.fetchone()

#             # Insert employees that do not exist in the SCD table.
#             if current_row is None:
#                 cursor.execute("""
#                     INSERT INTO employees_scd (
#                         employee_id,
#                         name,
#                         department,
#                         salary,
#                         effective_from,
#                         effective_to,
#                         is_current
#                     )
#                     VALUES (
#                         %s, %s, %s, %s,
#                         CURRENT_TIMESTAMP, NULL, TRUE
#                     );
#                 """, (employee_id, name, department, salary))

#                 inserted_count += 1
#                 logger.info(
#                     "New employee inserted into SCD table: employee_id=%s",
#                     employee_id,
#                 )
#                 continue

#             # Do nothing if the employee's tracked attributes are unchanged.
#             if current_row == (name, department, salary):
#                 continue

#             # Expire the current version.
#             cursor.execute("""
#                 UPDATE employees_scd
#                 SET effective_to = CURRENT_TIMESTAMP,
#                     is_current = FALSE
#                 WHERE employee_id = %s
#                   AND is_current = TRUE;
#             """, (employee_id,))

#             # Insert the new version.
#             cursor.execute("""
#                 INSERT INTO employees_scd (
#                     employee_id,
#                     name,
#                     department,
#                     salary,
#                     effective_from,
#                     effective_to,
#                     is_current
#                 )
#                 VALUES (
#                     %s, %s, %s, %s,
#                     CURRENT_TIMESTAMP, NULL, TRUE
#                 );
#             """, (employee_id, name, department, salary))

#             changed_count += 1
#             logger.info(
#                 "Employee version updated: employee_id=%s",
#                 employee_id,
#             )

#     logger.info(
#         "SCD load completed: inserted=%d, changed=%d",
#         inserted_count,
#         changed_count,
#     )

#     return inserted_count, changed_count


#************************************After incremental loading**************************************


import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

PIPELINE_NAME = "employees_scd"
OVERLAP_MINUTES = 5


def load_employees_scd(connection):
    """Apply SCD Type 2 logic using a watermark."""

    inserted_count = 0
    changed_count = 0

    with connection.cursor() as cursor:
        # Read the last successful watermark.
        cursor.execute("""
            SELECT last_loaded_at
            FROM etl_watermark
            WHERE pipeline_name = %s;
        """, (PIPELINE_NAME,))

        watermark_row = cursor.fetchone()

        if watermark_row is None:
            raise RuntimeError(
                f"Watermark not initialized for {PIPELINE_NAME}"
            )

        last_loaded_at = watermark_row[0]
        lower_bound = last_loaded_at - timedelta(
            minutes=OVERLAP_MINUTES
        )

        # Capture an upper boundary for this run.
        cursor.execute("SELECT clock_timestamp();")
        upper_bound = cursor.fetchone()[0]

        logger.info(
            "Incremental load started: lower_bound=%s, upper_bound=%s",
            lower_bound,
            upper_bound,
        )

        # Fetch only records updated within this window.
        cursor.execute("""
            SELECT employee_id, name, department, salary
            FROM employees
            WHERE updated_at >= %s
              AND updated_at <= %s
            ORDER BY employee_id;
        """, (lower_bound, upper_bound))

        source_rows = cursor.fetchall()

        for employee_id, name, department, salary in source_rows:
            cursor.execute("""
                SELECT name, department, salary
                FROM employees_scd
                WHERE employee_id = %s
                  AND is_current = TRUE;
            """, (employee_id,))

            current_row = cursor.fetchone()

            # Insert employees that have no current version.
            if current_row is None:
                cursor.execute("""
                    INSERT INTO employees_scd (
                        employee_id, name, department, salary,
                        effective_from, effective_to, is_current
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        CURRENT_TIMESTAMP, NULL, TRUE
                    );
                """, (employee_id, name, department, salary))

                inserted_count += 1
                continue

            # Skip employees whose tracked attributes are unchanged.
            if current_row == (name, department, salary):
                continue

            # Expire the old version.
            cursor.execute("""
                UPDATE employees_scd
                SET effective_to = CURRENT_TIMESTAMP,
                    is_current = FALSE
                WHERE employee_id = %s
                  AND is_current = TRUE;
            """, (employee_id,))

            # Insert the new current version.
            cursor.execute("""
                INSERT INTO employees_scd (
                    employee_id, name, department, salary,
                    effective_from, effective_to, is_current
                )
                VALUES (
                    %s, %s, %s, %s,
                    CURRENT_TIMESTAMP, NULL, TRUE
                );
            """, (employee_id, name, department, salary))

            changed_count += 1

        # Advance the watermark in the same transaction as the SCD changes.
        cursor.execute("""
            UPDATE etl_watermark
            SET last_loaded_at = %s
            WHERE pipeline_name = %s;
        """, (upper_bound, PIPELINE_NAME))

    logger.info(
        "Incremental load completed: inserted=%d, changed=%d",
        inserted_count,
        changed_count,
    )

    return inserted_count, changed_count