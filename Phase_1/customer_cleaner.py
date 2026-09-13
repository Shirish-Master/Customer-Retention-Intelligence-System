#This file is LAB_CP2.py


# 9. Created customer_cleaner.py with a CustomerCleaner class that accepts a DataFrame in __init__

import pandas as pd
import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class CustomerCleaner:

    def __init__(self, df):
        self.df = df.copy()
        logger.info("CustomerCleaner initialized with DataFrame shape: %s", self.df.shape)

    # 10. Implement standardize_column_names() — convert all column names to lowercase snake_case
    def standardize_column_names(self):

        self.df.columns = (
            self.df.columns
            .str.replace(r'([a-z])([A-Z])', r'\1_\2', regex=True)
            .str.lower()
        )

        logger.info("Column names standardized to snake_case")
        return self

    # 11. Implement fix_total_charges() — replace blank strings with NaN, then convert to float using pd.to_numeric(errors='coerce'); log how many rows were affected
    
    # 16. Add try/except around fix_total_charges() and log any unexpected errors
    def fix_total_charges(self):

        try:
            affected_rows = (
                self.df["total_charges"]
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            self.df["total_charges"] = self.df["total_charges"].replace(
                r"^\s*$",
                np.nan,
                regex=True
            )

            self.df["total_charges"] = pd.to_numeric(
                self.df["total_charges"],
                errors="coerce"
            )

            logger.info(
                "total_charges converted to float. Rows affected: %s",
                affected_rows
            )

        except Exception as e:
            logger.error("Error while fixing total_charges: %s", str(e))

        return self

    # 12. Implement normalize_binary_columns() — map Yes→1 and No→0 for: partner, dependents, phone_service, paperless_billing, churn
    def normalize_binary_columns(self):

        binary_columns = [
            "partner",
            "dependents",
            "phone_service",
            "paperless_billing",
            "churn"
        ]

        mapping = {
            "Yes": 1,
            "No": 0
        }

        for col in binary_columns:
            self.df[col] = self.df[col].map(mapping)

        logger.info("Binary columns normalized")
        return self

    # 13. Implement handle_nulls() — for total_charges nulls, fill with monthly_charges value
    def handle_nulls(self):

        null_count = self.df["total_charges"].isna().sum()

        self.df["total_charges"] = self.df["total_charges"].fillna(
            self.df["monthly_charges"]
        )

        logger.info(
            "Filled %s null values in total_charges using monthly_charges",
            null_count
        )

        return self

    # 14. Implement clean() — calls all methods in sequence and returns the cleaned DataFrame
    
    # 15. Add Python logging statements at each step
    def clean(self):

        logger.info("Starting cleaning pipeline")

        self.standardize_column_names()
        self.fix_total_charges()
        self.normalize_binary_columns()
        self.handle_nulls()

        logger.info("Cleaning pipeline completed")

        return self.df