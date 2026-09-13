-- 83. Define the business rules for "high risk": month-to-month contract AND tenure < 12 AND monthly_charges > dataset average

-- Business Rule:
-- High Risk = Month-to-month contract
--             AND tenure < 12
--             AND monthly_charges > dataset average


-- 84. Write a SELECT query that returns matching customers with a risk_reason string column explaining why each was flagged

SELECT
    f.customer_id,
    dc.contract_type,
    f.tenure,
    f.monthly_charges,
    'Month-to-month contract, tenure below 12 months, and monthly charges above average' AS risk_reason
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


-- 85. Test the query — verify count and inspect sample rows

SELECT COUNT(*) AS high_risk_customer_count
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
      )
LIMIT 10;


-- 86. Create the view: CREATE VIEW v_high_risk_customers AS ...

CREATE VIEW v_high_risk_customers AS

SELECT
    f.customer_id,
    dc.contract_type,
    f.tenure,
    f.monthly_charges,
    'Month-to-month contract, tenure below 12 months, and monthly charges above average' AS risk_reason
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


-- 87. Query the view: SELECT * FROM v_high_risk_customers LIMIT 10

SELECT *
FROM v_high_risk_customers
LIMIT 10;


-- 88. Count how many customers the view flags — what percentage of the total is this?

SELECT
    COUNT(*) AS flagged_customers,
    ROUND(
        COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM fact_customer_account),
        2
    ) AS percentage_of_total
FROM v_high_risk_customers;


-- 89. Discuss: what are the limitations of rule-based risk scoring vs ML-based scoring? What does ML add?

-- Rule-based risk scoring is simple, transparent and easy to deploy because every flagged customer satisfies predefined business rules.
-- Rule-based approaches cannot discover hidden relationships, interactions or changing customer behaviour patterns.
-- ML-based scoring learns from historical data, identifies complex patterns automatically and generally provides more accurate risk predictions.