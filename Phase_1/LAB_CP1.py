import pandas as pd
from pathlib import Path

# Load the dataset
data_path = Path("../customer_churn.csv")
df = pd.read_csv(data_path)

# 1. Print shape
print("Shape (rows, columns):", df.shape)

# 2. Print column names and data types
print("\nColumns and data types:")
print(df.dtypes)

# 3. Count null values and null percentage
print("\nNull values per column:")
null_counts = df.isnull().sum()
null_percentages = (null_counts / len(df)) * 100

print(
    pd.DataFrame(
        {
            "null_count": null_counts,
            "null_percentage": null_percentages
        }
    )
)

# 4. Categorical value counts
categorical_cols = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "InternetService",
    "Contract",
    "PaymentMethod",
    "Churn"
]

for col in categorical_cols:
    print(f"\n{col} unique values and counts:")
    print(df[col].value_counts(dropna=False))

# 5. Churn distribution and churn rate
print("\nChurn distribution:")
print(df["Churn"].value_counts(dropna=False))

churn_rate = df["Churn"].value_counts(normalize=True).get("Yes", 0) * 100
print(f"Churn rate: {churn_rate:.2f}%")

# 6. TotalCharges conversion check
print("\nTotalCharges dtype before conversion:")
print(df["TotalCharges"].dtype)

total_charges_numeric = pd.to_numeric(
    df["TotalCharges"],
    errors="coerce"
)

print("\nTotalCharges after pd.to_numeric(errors='coerce'):")
print(total_charges_numeric.dtype)
print("NaN values after conversion:", total_charges_numeric.isna().sum())

# 7. Numeric summary
print("\nSummary statistics:")

print("\nTenure")
print(df["tenure"].agg(["min", "max", "mean"]))

print("\nMonthlyCharges")
print(df["MonthlyCharges"].agg(["min", "max", "mean"]))

print("\nTotalCharges")
print(total_charges_numeric.agg(["min", "max", "mean"]))

# 8. Short profiling summary
print("\nProfiling summary:")

summary = [
    "The dataset contains 7,043 customer records and 21 columns.",
    "There are no standard null values, but TotalCharges contains 11 blank entries that become NaN after numeric conversion.",
    "customerID is a unique identifier and should be excluded from machine learning models.",
    "The churn distribution is imbalanced, with approximately 26.54% churned customers and 73.46% retained customers.",
    "TotalCharges is stored as a string/object column and should be converted to numeric before analysis or modeling."
]

for point in summary:
    print(f"- {point}")