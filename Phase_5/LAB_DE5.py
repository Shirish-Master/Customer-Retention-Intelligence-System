# 202. Create a SparkSession: local[2], 4g driver memory (7K rows is tiny — this config is intentionally minimal)

import os

os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["hadoop.home.dir"] = r"C:\hadoop"
os.environ["PATH"] += os.pathsep + r"C:\hadoop\bin"

from math import isclose
from pathlib import Path
import sys

import pandas as pd
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_DIR / "customer_churn.csv"
PARQUET_PATH = PROJECT_DIR / "Phase_5" / "data" / "spark_output" / "contract_summary"


schema = StructType(
    [
        StructField("customerID", StringType(), True),
        StructField("gender", StringType(), True),
        StructField("SeniorCitizen", IntegerType(), True),
        StructField("Partner", StringType(), True),
        StructField("Dependents", StringType(), True),
        StructField("tenure", IntegerType(), True),
        StructField("PhoneService", StringType(), True),
        StructField("MultipleLines", StringType(), True),
        StructField("InternetService", StringType(), True),
        StructField("OnlineSecurity", StringType(), True),
        StructField("OnlineBackup", StringType(), True),
        StructField("DeviceProtection", StringType(), True),
        StructField("TechSupport", StringType(), True),
        StructField("StreamingTV", StringType(), True),
        StructField("StreamingMovies", StringType(), True),
        StructField("Contract", StringType(), True),
        StructField("PaperlessBilling", StringType(), True),
        StructField("PaymentMethod", StringType(), True),
        StructField("MonthlyCharges", DoubleType(), True),
        StructField("TotalCharges", StringType(), True),
        StructField("Churn", StringType(), True),
    ]
)


# 203. Define a manual schema (StructType) for the CSV — all correct types including StringType for TotalCharges


def create_spark_session():
    return (
        SparkSession.builder
        .master("local[2]")
        .appName("CustomerChurnDataEngineering")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )


# 204. Read customer_churn.csv with the defined schema — print printSchema() and compare to pandas dtypes

def read_customer_csv(spark):
    spark_df = (
        spark.read
        .option("header", True)
        .schema(schema)
        .csv(str(CSV_PATH))
    )
    print("Spark schema:")
    spark_df.printSchema()

    pandas_df = pd.read_csv(CSV_PATH)
    print("Pandas dtypes:")
    print(pandas_df.dtypes)
    return spark_df


# 205. Fix TotalCharges blanks: use F.regexp_replace() to replace blank strings, then cast to DoubleType

def clean_spark_columns(spark_df):
    return (
        spark_df
        .withColumn(
            "TotalCharges",
            F.regexp_replace(F.col("TotalCharges"), r"^\s*$", "")
            .cast(DoubleType()),
        )
        # 206. Encode the Churn column: use F.when(F.col("Churn")=="Yes", 1).otherwise(0) — Spark equivalent of map()
        .withColumn(
            "churn_encoded",
            F.when(F.col("Churn") == "Yes", 1).otherwise(0).cast(IntegerType()),
        )
    )


# 207. GroupBy Contract: compute COUNT(*) as customer_count and AVG(churn_encoded) as churn_rate — show results

def build_contract_summary(spark_df):
    contract_summary = (
        spark_df.groupBy("Contract")
        .agg(
            F.count("*").alias("customer_count"),
            F.avg("churn_encoded").alias("churn_rate"),
        )
        .orderBy(F.col("churn_rate").desc())
    )
    print("Churn summary by Contract:")
    contract_summary.show()
    return contract_summary


# 208. GroupBy InternetService: compute AVG(MonthlyCharges) and AVG(churn_encoded) — show results

def build_internet_summary(spark_df):
    internet_summary = (
        spark_df.groupBy("InternetService")
        .agg(
            F.avg("MonthlyCharges").alias("avg_monthly_charges"),
            F.avg("churn_encoded").alias("churn_rate"),
        )
        .orderBy(F.col("churn_rate").desc())
    )
    print("Summary by InternetService:")
    internet_summary.show()
    return internet_summary


# 209. Cross-validate: Spark churn rates must exactly match your CP3 pandas groupby results

def cross_validate_with_cp3(spark_df, contract_summary, internet_summary):
    pandas_df = pd.read_csv(CSV_PATH)
    pandas_df["Churn"] = pandas_df["Churn"].map({"Yes": 1, "No": 0})

    pandas_contract = pandas_df.groupby("Contract")["Churn"].mean().to_dict()
    spark_contract = {
        row["Contract"]: row["churn_rate"]
        for row in contract_summary.collect()
    }
    pandas_internet = pandas_df.groupby("InternetService")["Churn"].mean().to_dict()
    spark_internet = {
        row["InternetService"]: row["churn_rate"]
        for row in internet_summary.collect()
    }

    for group_name, pandas_rates, spark_rates in [
        ("Contract", pandas_contract, spark_contract),
        ("InternetService", pandas_internet, spark_internet),
    ]:
        assert pandas_rates.keys() == spark_rates.keys()
        for category, pandas_rate in pandas_rates.items():
            assert isclose(
                pandas_rate,
                spark_rates[category],
                rel_tol=0,
                abs_tol=1e-12,
            ), f"{group_name} churn mismatch for {category}"

    print("PASS - Spark churn rates exactly match CP3 pandas groupby results")


# 210. Write the contract-level summary as Parquet: data/spark_output/contract_summary/ partitioned by Contract

def write_contract_parquet(contract_summary):
    (
        contract_summary.write
        .mode("overwrite")
        .partitionBy("Contract")
        .parquet(str(PARQUET_PATH))
    )
    print(f"Wrote Parquet output to {PARQUET_PATH}")


# 211. Read the Parquet back, print schema and count — confirm round-trip is clean

def verify_parquet_round_trip(spark):
    round_trip_df = spark.read.parquet(str(PARQUET_PATH))
    print("Parquet schema:")
    round_trip_df.printSchema()
    round_trip_count = round_trip_df.count()
    print(f"Parquet row count: {round_trip_count}")
    assert round_trip_count == 3, "Expected three contract summary rows"
    print("PASS - Parquet round-trip is clean")


def main():
    spark = create_spark_session()
    try:
        raw_df = read_customer_csv(spark)
        cleaned_df = clean_spark_columns(raw_df)
        contract_summary = build_contract_summary(cleaned_df)
        internet_summary = build_internet_summary(cleaned_df)
        cross_validate_with_cp3(cleaned_df, contract_summary, internet_summary)
        write_contract_parquet(contract_summary)
        verify_parquet_round_trip(spark)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
