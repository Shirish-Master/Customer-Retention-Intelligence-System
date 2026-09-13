import os

os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["hadoop.home.dir"] = r"C:\hadoop"
os.environ["PATH"] += os.pathsep + r"C:\hadoop\bin"

from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("ParquetTest")
    .getOrCreate()
)

df = spark.range(10)

df.write.mode("overwrite").parquet("test_parquet")

print("PARQUET WRITE SUCCESS")

spark.stop()
