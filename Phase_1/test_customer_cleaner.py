import pandas as pd
from pathlib import Path
from customer_cleaner import CustomerCleaner

# 17. Test: instantiate CustomerCleaner, call .clean(), print shape and dtypes before/after

data_path = Path("../customer_churn.csv")
df = pd.read_csv(data_path)

print("Before Cleaning")
print("Shape:", df.shape)
print(df.dtypes)

cleaner = CustomerCleaner(df)
clean_df = cleaner.clean()

print("\nAfter Cleaning")
print("Shape:", clean_df.shape)
print(clean_df.dtypes)