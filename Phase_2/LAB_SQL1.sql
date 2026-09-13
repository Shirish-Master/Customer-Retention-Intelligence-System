/*
50. Write a CREATE TABLE DDL statement for each of the 4-5 tables.
*/

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    gender VARCHAR(20),
    senior_citizen BOOLEAN,
    partner BOOLEAN,
    dependents BOOLEAN
);

CREATE TABLE contracts (
    customer_id VARCHAR(20) PRIMARY KEY,
    contract_type VARCHAR(30) NOT NULL,
    tenure INT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE services (
    customer_id VARCHAR(20) PRIMARY KEY,
    phone_service VARCHAR(10) NOT NULL,
    multiple_lines VARCHAR(30) NOT NULL,
    internet_service VARCHAR(20) NOT NULL,
    online_security VARCHAR(20) NOT NULL,
    online_backup VARCHAR(20) NOT NULL,
    device_protection VARCHAR(20) NOT NULL,
    tech_support VARCHAR(20) NOT NULL,
    streaming_tv VARCHAR(20) NOT NULL,
    streaming_movies VARCHAR(20) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE billing (
    customer_id VARCHAR(20) PRIMARY KEY,
    paperless_billing BOOLEAN NOT NULL,
    payment_method VARCHAR(40) NOT NULL,
    monthly_charges DECIMAL(10,2) NOT NULL,
    total_charges DECIMAL(12,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE customer_status (
    customer_id VARCHAR(20) PRIMARY KEY,
    churn BOOLEAN NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
