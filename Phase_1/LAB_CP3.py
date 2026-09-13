import pandas as pd
from pathlib import Path
from customer_cleaner import CustomerCleaner

# 18. Load and clean the data using CustomerCleaner
data_path = Path("../customer_churn.csv")
df = pd.read_csv(data_path)

cleaner = CustomerCleaner(df)
clean_df = cleaner.clean()

# 19. Compute churn rate by contract type — sort descending. Which contract has the highest churn?
print("\nChurn Rate by Contract Type")

contract_churn = (
    clean_df.groupby("contract")["churn"]
    .mean()
    .sort_values(ascending=False)
    * 100
)

print(contract_churn)

print("\nHighest Churn Contract:")
print(contract_churn.idxmax())

# 20. Compute churn rate by internet service type
print("\nChurn Rate by Internet Service Type")

internet_churn = (
    clean_df.groupby("internet_service")["churn"]
    .mean()
    .sort_values(ascending=False)
    * 100
)

print(internet_churn)

# 21. Compute churn rate by payment method
print("\nChurn Rate by Payment Method")

payment_churn = (
    clean_df.groupby("payment_method")["churn"]
    .mean()
    .sort_values(ascending=False)
    * 100
)

print(payment_churn)

# 22. Create a tenure_bucket column using pd.cut() with bins [0,12,24,48,72] and labels ["0-12","13-24","25-48","49-72"]. Compute churn rate per bucket.
clean_df["tenure_bucket"] = pd.cut(
    clean_df["tenure"],
    bins=[0, 12, 24, 48, 72],
    labels=["0-12", "13-24", "25-48", "49-72"],
    include_lowest=True
)

print("\nChurn Rate by Tenure Bucket")

tenure_churn = (
    clean_df.groupby("tenure_bucket")["churn"]
    .mean()
    .sort_values(ascending=False)
    * 100
)

print(tenure_churn)

# 23. Compute average monthly_charges for churned vs non-churned customers
print("\nAverage Monthly Charges by Churn Status")

avg_monthly_charges = (
    clean_df.groupby("churn")["monthly_charges"]
    .mean()
)

print(avg_monthly_charges)

# 24. Find the combination (contract + internet_service) with the highest churn rate using groupby on two columns
print("\nChurn Rate by Contract and Internet Service")

combo_churn = (
    clean_df.groupby(["contract", "internet_service"])["churn"]
    .mean()
    .sort_values(ascending=False)
    * 100
)

print(combo_churn)

print("\nHighest Risk Combination:")
print(combo_churn.head(1))

# 25. Write a 3-sentence business summary: which segments are highest risk and what that means for the retention team
print("\nBusiness Summary")

print(
    "Month-to-month customers have the highest churn rate, making them the highest-risk contract segment."
)

print(
    "Customers using Fiber optic internet and Electronic Check payment methods also show elevated churn compared to other groups."
)

print(
    "The retention team should focus on new customers and high-risk segments with proactive engagement, targeted offers, and service improvement initiatives."
)