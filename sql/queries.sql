SELECT *
FROM employees_backup
ORDER BY employee_id;

SELECT *
FROM employees
ORDER BY employee_id;


UPDATE employees
SET salary=200000
where name='Uday';

delete from employees
where employee_id=3;


SELECT employee_id, name, department, salary
FROM employees_backup
ORDER BY employee_id;

-- Queries for SCD
CREATE TABLE IF NOT EXISTS employees_scd (
    employee_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    name VARCHAR(100),
    department VARCHAR(100),
    salary NUMERIC,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT valid_effective_dates
        CHECK (
            effective_to IS NULL
            OR effective_to > effective_from
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS
    unique_current_employee
ON employees_scd (employee_id)
WHERE is_current = TRUE;

INSERT INTO employees_scd (
    employee_id,
    name,
    department,
    salary,
    effective_from,
    effective_to,
    is_current
)
SELECT
    employee_id,
    name,
    department,
    salary,
    CURRENT_TIMESTAMP,
    NULL,
    TRUE
FROM employees_backup;


SELECT *
FROM employees_scd
ORDER BY employee_id;

SELECT
    employee_key,
    employee_id,
    name,
    department,
    salary,
    effective_from,
    effective_to,
    is_current
FROM employees_scd
ORDER BY employee_id, effective_from;



UPDATE employees
SET department = 'Analytics'
WHERE employee_id = 1;


--Queries for incremental loading


ALTER TABLE employees
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP
DEFAULT CURRENT_TIMESTAMP;


CREATE OR REPLACE FUNCTION set_employee_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE TRIGGER trg_employee_updated_at
BEFORE UPDATE ON employees
FOR EACH ROW
EXECUTE FUNCTION set_employee_updated_at();

UPDATE employees
SET department = 'Analytics'
WHERE employee_id = 1;


SELECT employee_id, department, updated_at
FROM employees
WHERE employee_id = 1;


CREATE TABLE IF NOT EXISTS etl_watermark (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    last_loaded_at TIMESTAMP NOT NULL
);

SELECT * FROM etl_watermark;


INSERT INTO etl_watermark (pipeline_name, last_loaded_at)
VALUES ('employees_scd', TIMESTAMP '1970-01-01 00:00:00')
ON CONFLICT (pipeline_name) DO NOTHING;

UPDATE employees
SET department = 'Analytics'
WHERE employee_id = 2;


SELECT *
FROM employees_scd
WHERE employee_id = 2
ORDER BY effective_from;


--Queries for SDC Type 4

CREATE TABLE IF NOT EXISTS employees_current (
    employee_id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(100),
    salary NUMERIC
);

CREATE TABLE IF NOT EXISTS employees_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    name VARCHAR(100),
    department VARCHAR(100),
    salary NUMERIC,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_employees_history_employee
ON employees_history (employee_id, effective_from);

INSERT INTO employees_current (
    employee_id,
    name,
    department,
    salary
)
SELECT
    employee_id,
    name,
    department,
    salary
FROM employees
ON CONFLICT (employee_id) DO NOTHING;

SELECT *
FROM employees_current
ORDER BY employee_id;

SELECT COUNT(*) AS current_employee_count
FROM employees_current;

SELECT pipeline_name, last_loaded_at
FROM etl_watermark
ORDER BY pipeline_name;

INSERT INTO etl_watermark (pipeline_name, last_loaded_at)
VALUES (
    'employees_scd_type4',
    CURRENT_TIMESTAMP
)
ON CONFLICT (pipeline_name) DO NOTHING;

SELECT *
FROM employees_history
ORDER BY employee_id, effective_from;

Update employees
set department='Cybersecurity'
where employee_id=4;

select * from employees;

SELECT *
FROM employees_history
ORDER BY employee_id, effective_from;


ALTER TABLE employees_current
ADD COLUMN IF NOT EXISTS effective_from TIMESTAMP;


UPDATE employees_current
SET effective_from = CURRENT_TIMESTAMP
WHERE effective_from IS NULL;


SELECT
    employee_id,
    name,
    department,
    salary,
    effective_from
FROM employees_current
ORDER BY employee_id;


