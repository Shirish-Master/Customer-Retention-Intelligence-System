-- 54. Verify row count

SELECT COUNT(*) AS total_rows
FROM stg_customer_raw;

-- 55. Inspect TotalCharges in the staging table

SELECT
    customerID,
    TotalCharges
FROM stg_customer_raw
WHERE TotalCharges = ''
LIMIT 5;

-- 56. Inspect data types: confirm TotalCharges is stored as text in staging

DESCRIBE stg_customer_raw;

-- 57. Record the load time and row count in a simple ingestion_log table

CREATE TABLE IF NOT EXISTS ingestion_log (

    id INT AUTO_INCREMENT PRIMARY KEY,

    file_name VARCHAR(255),

    row_count INT,

    load_timestamp DATETIME,

    status VARCHAR(20)

);

INSERT INTO ingestion_log
(
    file_name,
    row_count,
    load_timestamp,
    status
)
VALUES
(
    'customer_churn.csv',
    7043,
    NOW(),
    'SUCCESS'
);

SELECT *
FROM ingestion_log;

-- 58. Run a basic validation: count distinct customerIDs — should equal row count (no duplicates)

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT customerID) AS unique_customers
FROM stg_customer_raw;