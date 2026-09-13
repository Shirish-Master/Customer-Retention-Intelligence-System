-- 67. Query 1 — Churn rate by contract: SELECT contract_type, AVG(churn) AS churn_rate FROM fact_customer_account JOIN dim_contract GROUP BY contract_type ORDER BY churn_rate DESC

-- Business Question:
-- Which contract type has the highest churn rate?

SELECT
    dc.contract_type,
    AVG(f.churn) AS churn_rate
FROM fact_customer_account f
JOIN dim_contract dc
    ON f.contract_id = dc.contract_id
GROUP BY dc.contract_type
ORDER BY churn_rate DESC;

-- Interpretation:
-- The contract type with the highest churn rate represents the highest-risk customer segment.


-- 68. Query 2 — Churn rate by payment method: similar pattern, join with dim_payment

-- Business Question:
-- Which payment method has the highest churn rate?

SELECT
    dp.payment_method,
    AVG(f.churn) AS churn_rate
FROM fact_customer_account f
JOIN dim_payment dp
    ON f.payment_id = dp.payment_id
GROUP BY dp.payment_method
ORDER BY churn_rate DESC;

-- Interpretation:
-- The payment method with the highest churn rate indicates customers who are more likely to leave.


-- 69. Query 3 — Average monthly charges by churn status: GROUP BY churn, return avg(monthly_charges)

-- Business Question:
-- What is the average monthly charge for churned and non-churned customers?

SELECT
    churn,
    AVG(monthly_charges) AS avg_monthly_charges
FROM fact_customer_account
GROUP BY churn;

-- Interpretation:
-- Comparing average monthly charges helps identify whether higher charges are associated with churn.


-- 70. Query 4 — Top risky segments: customers with month-to-month contract AND tenure < 12 AND monthly_charges > average — count and list

-- Business Question:
-- How many customers belong to the highest-risk segment and who are they?

SELECT
    COUNT(*) AS risky_customer_count
FROM fact_customer_account f
JOIN dim_contract dc
    ON f.contract_id = dc.contract_id
WHERE dc.contract_type = 'Month-to-month'
  AND f.tenure < 12
  AND f.monthly_charges >
      (
          SELECT AVG(monthly_charges)
          FROM fact_customer_account
      );

SELECT
    f.customer_id,
    dc.contract_type,
    f.tenure,
    f.monthly_charges
FROM fact_customer_account f
JOIN dim_contract dc
    ON f.contract_id = dc.contract_id
WHERE dc.contract_type = 'Month-to-month'
  AND f.tenure < 12
  AND f.monthly_charges >
      (
          SELECT AVG(monthly_charges)
          FROM fact_customer_account
      );

-- Interpretation:
-- Customers meeting all three risk conditions should be prioritised for retention efforts.


-- 71. Query 5 — High-value churned customers: churned customers with total_charges > 2000 — how many and what is their average tenure?

-- Business Question:
-- How many high-value churned customers are there and what is their average tenure?

SELECT
    COUNT(*) AS high_value_churned_customers,
    AVG(tenure) AS average_tenure
FROM fact_customer_account
WHERE churn = 1
  AND total_charges > 2000;

-- Interpretation:
-- These customers represent significant lost revenue and may reveal important churn patterns.


-- 72. For each query: first state the business question in plain English, then write the SQL, then interpret the result in one sentence

-- Completed above for Queries 1 through 5.


-- 73. Bonus: write a single query that returns contract type, avg monthly charges, avg tenure, and churn rate together — sorted by churn rate


SELECT
    dc.contract_type,
    AVG(f.monthly_charges) AS avg_monthly_charges,
    AVG(f.tenure) AS avg_tenure,
    AVG(f.churn) AS churn_rate
FROM fact_customer_account f
JOIN dim_contract dc
    ON f.contract_id = dc.contract_id
GROUP BY dc.contract_type
ORDER BY churn_rate DESC;

