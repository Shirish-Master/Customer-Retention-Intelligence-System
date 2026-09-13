from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

print(
    spark.sparkContext._jvm.org.apache.hadoop.util.VersionInfo.getVersion()
)