# Customer Churn Schema Design

Questions 45-51 for `customer_churn.csv`.

## 45. Column Classification

**Question:** List all 21 columns from the dataset and categorise each as: stable identity, service subscription, billing/charges, or churn outcome.

### Stable Identity

- `customerID`
- `gender`
- `SeniorCitizen`
- `Partner`
- `Dependents`

### Service Subscription

- `PhoneService`
- `MultipleLines`
- `InternetService`
- `OnlineSecurity`
- `OnlineBackup`
- `DeviceProtection`
- `TechSupport`
- `StreamingTV`
- `StreamingMovies`

### Billing/Charges

- `Contract`
- `PaperlessBilling`
- `PaymentMethod`
- `MonthlyCharges`
- `TotalCharges`

### Churn Outcome

- `Churn`

All 21 source columns are listed above exactly once.

## 46. Entity Definitions

**Question:** Define the entities: customers (identity), contracts (subscription terms), services (what they subscribe to), billing (charges), customer_status (churn).

- **customers:** Stable customer identity and demographic attributes.
- **contracts:** Subscription term for the customer.
- **services:** Phone, internet, and optional service subscriptions.
- **billing:** Billing preferences, payment method, and charge measures.
- **customer_status:** Customer churn outcome.

## 47. Entity-Relationship Diagram

**Question:** Draw the entity-relationship diagram: which tables have foreign keys to which?

```text
customers (1) -------- (1) contracts
    |                       |
    |                       +-- customer_id FK -> customers.customer_id
    |
    +------------------- (1) services
    |                       +-- customer_id FK -> customers.customer_id
    |
    +------------------- (1) billing
    |                       +-- customer_id FK -> customers.customer_id
    |
    +------------------- (1) customer_status
                            +-- customer_id FK -> customers.customer_id
```

Every child table has one row per customer. The `customer_id` foreign keys are
also primary keys, enforcing a one-to-one relationship with `customers`.

## 48. Primary Keys

**Question:** Define the primary key for each table (`customer_id` is the natural key throughout).

| Table | Primary key | Foreign key |
|---|---|---|
| `customers` | `customer_id` | None |
| `contracts` | `customer_id` | `customers.customer_id` |
| `services` | `customer_id` | `customers.customer_id` |
| `billing` | `customer_id` | `customers.customer_id` |
| `customer_status` | `customer_id` | `customers.customer_id` |

`customer_id` is the natural key throughout because it uniquely identifies each
customer in the source dataset.

## 49. Dimension-Like and Measure-Like Columns

**Question:** Identify which columns are dimension-like (contract type, payment method, internet service) vs measure-like (tenure, monthly_charges, total_charges).

### Dimension-like categorical attributes

`gender`, `senior_citizen`, `partner`, `dependents`, `phone_service`,
`multiple_lines`, `internet_service`, `online_security`, `online_backup`,
`device_protection`, `tech_support`, `streaming_tv`, `streaming_movies`,
`contract`, `paperless_billing`, `payment_method`, `churn`

### Measure-like numeric attributes

`tenure`, `monthly_charges`, `total_charges`

`tenure` is a numeric duration measure. `MonthlyCharges` and `TotalCharges` are
numeric monetary measures. `Churn` is retained as a status dimension in the
`customer_status` table, despite being encoded as a numeric flag in the DDL.

## 50. Create Table DDL

**Question:** Write a `CREATE TABLE` DDL statement for each of the 4-5 tables.

The DDL answer is provided in [LAB_SQL1.sql](LAB_SQL1.sql).

## 51. Trainer Discussion: OLTP or Analytics Schema?

**Question:** Discuss with trainer: should this be a normalised OLTP schema or a denormalised analytics schema? Why?

Recommendation: use this normalised schema as an OLTP-style source model.
Each customer attribute has one authoritative location, which reduces update
anomalies and enforces referential integrity through foreign keys. For
analytics, create a separate denormalised star schema or reporting view from
these tables. Denormalisation is useful for read-heavy dashboards and simpler
queries, but it duplicates data and is less suitable as the operational source
of truth.
