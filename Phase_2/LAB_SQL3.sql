-- 59. Create dim_contract with rows for each unique contract type (Month-to-month, One year, Two year)

CREATE TABLE dim_contract (
    contract_id INT AUTO_INCREMENT PRIMARY KEY,
    contract_type VARCHAR(50) UNIQUE
);

INSERT INTO dim_contract (contract_type)
SELECT DISTINCT Contract
FROM stg_customer_raw;


-- 60. Create dim_payment with rows for each payment method

CREATE TABLE dim_payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_method VARCHAR(100) UNIQUE
);

INSERT INTO dim_payment (payment_method)
SELECT DISTINCT PaymentMethod
FROM stg_customer_raw;


-- 61. Create the customers table: INSERT from staging, standardising gender, casting senior_citizen, binary-encoding partner/dependents

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    gender VARCHAR(20),
    senior_citizen INT,
    partner INT,
    dependents INT
);

INSERT INTO customers
(
    customer_id,
    gender,
    senior_citizen,
    partner,
    dependents
)
SELECT
    customerID,
    UPPER(gender),
    SeniorCitizen,
    CASE WHEN Partner = 'Yes' THEN 1 ELSE 0 END,
    CASE WHEN Dependents = 'Yes' THEN 1 ELSE 0 END
FROM stg_customer_raw;


-- 62. Create fact_customer_account: INSERT tenure, charges, churn — cast TotalCharges with NULLIF to handle blanks, join to dim tables for foreign keys

CREATE TABLE fact_customer_account (
    customer_id VARCHAR(20) PRIMARY KEY,
    contract_id INT,
    payment_id INT,
    tenure INT,
    monthly_charges DECIMAL(10,2),
    total_charges DECIMAL(10,2),
    churn INT,
    FOREIGN KEY (contract_id) REFERENCES dim_contract(contract_id),
    FOREIGN KEY (payment_id) REFERENCES dim_payment(payment_id)
);

INSERT INTO fact_customer_account
(
    customer_id,
    contract_id,
    payment_id,
    tenure,
    monthly_charges,
    total_charges,
    churn
)
SELECT
    s.customerID,
    dc.contract_id,
    dp.payment_id,
    s.tenure,
    s.MonthlyCharges,
    CAST(NULLIF(s.TotalCharges, '') AS DECIMAL(10,2)),
    CASE WHEN s.Churn = 'Yes' THEN 1 ELSE 0 END
FROM stg_customer_raw s
JOIN dim_contract dc
    ON s.Contract = dc.contract_type
JOIN dim_payment dp
    ON s.PaymentMethod = dp.payment_method;


-- 63. Verify counts: each curated table row count should match expectations

SELECT COUNT(*) AS contract_rows
FROM dim_contract;

SELECT COUNT(*) AS payment_rows
FROM dim_payment;

SELECT COUNT(*) AS customer_rows
FROM customers;

SELECT COUNT(*) AS fact_rows
FROM fact_customer_account;


-- 64. Run a JOIN query across customers + fact_customer_account + dim_contract to confirm the relationships work

SELECT
    c.customer_id,
    c.gender,
    dc.contract_type,
    f.tenure,
    f.monthly_charges,
    f.churn
FROM customers c
JOIN fact_customer_account f
    ON c.customer_id = f.customer_id
JOIN dim_contract dc
    ON f.contract_id = dc.contract_id
LIMIT 10;