#This file gave customer_features.csv

import pandas as pd
from pathlib import Path
from customer_cleaner import CustomerCleaner

# 26. Start from the cleaned DataFrame (CustomerCleaner output)
data_path = Path("../customer_churn.csv")
df = pd.read_csv(data_path)

cleaner = CustomerCleaner(df)
clean_df = cleaner.clean()

# Convert service columns from Yes/No to 1/0 for feature engineering
service_columns = [
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies"
]

for col in service_columns:
    clean_df[col] = clean_df[col].replace({
        "Yes": 1,
        "No": 0,
        "No internet service": 0
    })

# 27. Feature 1 — tenure_bucket: pd.cut() with bins [0,12,24,48,72] as in CP3
clean_df["tenure_bucket"] = pd.cut(
    clean_df["tenure"],
    bins=[0, 12, 24, 48, 72],
    labels=["0-12", "13-24", "25-48", "49-72"],
    include_lowest=True
)

# 28. Feature 2 — high_charge_flag: 1 if monthly_charges > median monthly_charges, else 0
median_charge = clean_df["monthly_charges"].median()

clean_df["high_charge_flag"] = (
    clean_df["monthly_charges"] > median_charge
).astype(int)

# 29. Feature 3 — service_count: count how many of these 6 service columns equal 1: online_security, online_backup, device_protection, tech_support, streaming_tv, streaming_movies
clean_df["service_count"] = clean_df[service_columns].sum(axis=1)

# 30. Feature 4 — is_long_term_customer: 1 if tenure >= 24, else 0
clean_df["is_long_term_customer"] = (
    clean_df["tenure"] >= 24
).astype(int)

# 31. Feature 5 — has_streaming_bundle: 1 if both streaming_tv=1 AND streaming_movies=1, else 0
clean_df["has_streaming_bundle"] = (
    (clean_df["streaming_tv"] == 1) &
    (clean_df["streaming_movies"] == 1)
).astype(int)

# 32. Feature 6 — auto_pay_flag: 1 if payment_method contains "automatic", else 0 (use str.contains())
clean_df["auto_pay_flag"] = (
    clean_df["payment_method"]
    .str.contains("automatic", case=False, na=False)
    .astype(int)
)

# 33. Print the correlation of each new feature with the churn column
print("\nCorrelation of New Features with Churn")

correlation_features = [
    "high_charge_flag",
    "service_count",
    "is_long_term_customer",
    "has_streaming_bundle",
    "auto_pay_flag"
]

correlations = clean_df[correlation_features].corrwith(clean_df["churn"])

print(correlations)

# 34. Save to customer_features.csv — include all original cleaned columns plus the 6 new ones
output_path = "customer_features.csv"
clean_df.to_csv(output_path, index=False)

print(f"\nFeature engineered dataset saved as: {output_path}")

print("\nNew Feature Columns Added:")
print([
    "tenure_bucket",
    "high_charge_flag",
    "service_count",
    "is_long_term_customer",
    "has_streaming_bundle",
    "auto_pay_flag"
])

print("\nFinal Shape:")
print(clean_df.shape)