#This should be LAB_CP5.py

# 35. Create customer_pipeline.py

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

# 36. Import CustomerCleaner from customer_cleaner.py and build_features() logic
from customer_cleaner import CustomerCleaner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# 37. Define load_data(filepath) — reads CSV and logs row count
def load_data(filepath):
    try:
        df = pd.read_csv(filepath)

        logger.info("Data loaded successfully")
        logger.info("Row count: %s", len(df))

        return df

    except Exception as e:
        logger.error("Error loading data: %s", str(e))
        raise


# 38. Define build_features(df) — runs all 6 feature engineering steps from CP4 and returns the enriched DataFrame
def build_features(df):
    try:
        feature_df = df.copy()

        service_columns = [
            "online_security",
            "online_backup",
            "device_protection",
            "tech_support",
            "streaming_tv",
            "streaming_movies"
        ]

        for col in service_columns:
            feature_df[col] = feature_df[col].replace(
                {
                    "Yes": 1,
                    "No": 0,
                    "No internet service": 0
                }
            )

        feature_df["tenure_bucket"] = pd.cut(
            feature_df["tenure"],
            bins=[0, 12, 24, 48, 72],
            labels=["0-12", "13-24", "25-48", "49-72"],
            include_lowest=True
        )

        median_charge = feature_df["monthly_charges"].median()

        feature_df["high_charge_flag"] = (
            feature_df["monthly_charges"] > median_charge
        ).astype(int)

        feature_df["service_count"] = feature_df[service_columns].sum(axis=1)

        feature_df["is_long_term_customer"] = (
            feature_df["tenure"] >= 24
        ).astype(int)

        feature_df["has_streaming_bundle"] = (
            (feature_df["streaming_tv"] == 1) &
            (feature_df["streaming_movies"] == 1)
        ).astype(int)

        feature_df["auto_pay_flag"] = (
            feature_df["payment_method"]
            .str.contains("automatic", case=False, na=False)
            .astype(int)
        )

        logger.info("Feature engineering completed")
        logger.info("Feature DataFrame row count: %s", len(feature_df))

        return feature_df

    except Exception as e:
        logger.error("Error during feature engineering: %s", str(e))
        raise


# 39. Define save_outputs(clean_df, feature_df, output_dir) — saves both files with timestamps in filenames
def save_outputs(clean_df, feature_df, output_dir):
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")

        clean_file = output_dir / f"customer_cleaned_{timestamp}.csv"
        feature_file = output_dir / f"customer_features_{timestamp}.csv"

        clean_df.to_csv(clean_file, index=False)
        feature_df.to_csv(feature_file, index=False)

        logger.info("Cleaned file saved to: %s", clean_file)
        logger.info("Feature file saved to: %s", feature_file)

    except Exception as e:
        logger.error("Error saving output files: %s", str(e))
        raise


# 40. Define main() — calls load → clean → build_features → save in sequence
def main():

    # 41. Add logging throughout: start time, step completion, row counts, output file paths
    logger.info("Pipeline execution started")

    try:

        # 42. Wrap each step in try/except — if any step fails, log the error and raise; do not silently continue
        raw_df = load_data("../customer_churn.csv")

        cleaner = CustomerCleaner(raw_df)
        clean_df = cleaner.clean()

        logger.info("Cleaning step completed")
        logger.info("Cleaned DataFrame row count: %s", len(clean_df))

        feature_df = build_features(clean_df)

        logger.info("Feature engineering step completed")

        # 43. Add a simple data quality check before saving: assert no nulls in monthly_charges, assert churn column has only 0/1 values
        assert clean_df["monthly_charges"].isnull().sum() == 0, \
            "monthly_charges contains null values"

        assert set(clean_df["churn"].unique()).issubset({0, 1}), \
            "churn contains values other than 0 and 1"

        logger.info("Data quality checks passed")

        save_outputs(
            clean_df,
            feature_df,
            "output"
        )

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error("Pipeline failed: %s", str(e))
        raise


# 44. Run the script end-to-end: python customer_pipeline.py
if __name__ == "__main__":
    main()