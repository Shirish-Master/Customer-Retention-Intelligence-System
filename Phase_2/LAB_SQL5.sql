-- 74. Design the customer_ml_features table schema: all features from CP4 + original numeric columns + churn label

-- 75. Create the table in SQL with appropriate types (INT for flags/counts, FLOAT for charges, VARCHAR for buckets)

CREATE TABLE customer_ml_features (

    customer_id VARCHAR(20) PRIMARY KEY,

    tenure INT,

    monthly_charges FLOAT,

    total_charges FLOAT,

    churn INT,

    tenure_bucket VARCHAR(20),

    high_charge_flag INT,

    service_count INT,

    is_long_term_customer INT,

    has_streaming_bundle INT,

    auto_pay_flag INT

);


-- 76. Populate it using INSERT ... SELECT from fact_customer_account + dim tables, computing engineered features in SQL:

-- 77. — service_count: SUM of 6 service binary columns

-- 78. — high_charge_flag: CASE WHEN monthly_charges > (SELECT AVG...) THEN 1 ELSE 0 END

-- 79. — is_long_term_customer: CASE WHEN tenure >= 24 THEN 1 ELSE 0 END

-- 80. — auto_pay_flag: CASE WHEN payment_method LIKE "%automatic%" THEN 1 ELSE 0 END

INSERT INTO customer_ml_features
(
    customer_id,
    tenure,
    monthly_charges,
    total_charges,
    churn,
    tenure_bucket,
    high_charge_flag,
    service_count,
    is_long_term_customer,
    has_streaming_bundle,
    auto_pay_flag
)

SELECT

    f.customer_id,

    f.tenure,

    f.monthly_charges,

    COALESCE(f.total_charges, f.monthly_charges),

    f.churn,

    CASE
        WHEN f.tenure <= 12 THEN '0-12'
        WHEN f.tenure <= 24 THEN '13-24'
        WHEN f.tenure <= 48 THEN '25-48'
        ELSE '49-72'
    END AS tenure_bucket,

    CASE
        WHEN f.monthly_charges >
            (
                SELECT AVG(monthly_charges)
                FROM fact_customer_account
            )
        THEN 1
        ELSE 0
    END AS high_charge_flag,

    (
        CASE WHEN s.OnlineSecurity = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN s.OnlineBackup = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN s.DeviceProtection = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN s.TechSupport = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN s.StreamingTV = 'Yes' THEN 1 ELSE 0 END +
        CASE WHEN s.StreamingMovies = 'Yes' THEN 1 ELSE 0 END
    ) AS service_count,

    CASE
        WHEN f.tenure >= 24 THEN 1
        ELSE 0
    END AS is_long_term_customer,

    CASE
        WHEN s.StreamingTV = 'Yes'
         AND s.StreamingMovies = 'Yes'
        THEN 1
        ELSE 0
    END AS has_streaming_bundle,

    CASE
        WHEN dp.payment_method LIKE '%automatic%'
        THEN 1
        ELSE 0
    END AS auto_pay_flag

FROM fact_customer_account f

JOIN dim_payment dp
    ON f.payment_id = dp.payment_id

JOIN stg_customer_raw s
    ON f.customer_id = s.customerID;


-- 81. Verify: SELECT COUNT(*) should be 7043; SELECT COUNT(*) WHERE monthly_charges IS NULL should be 0

SELECT COUNT(*) AS total_rows
FROM customer_ml_features;

SELECT COUNT(*) AS null_monthly_charges
FROM customer_ml_features
WHERE monthly_charges IS NULL;


-- 82. Run a final check: SELECT churn, COUNT(*) FROM customer_ml_features GROUP BY churn — confirm class distribution

SELECT
    churn,
    COUNT(*) AS customer_count
FROM customer_ml_features
GROUP BY churn;


-- Schema printed from DESCRIBE customer_ml_features

DESCRIBE customer_ml_features;