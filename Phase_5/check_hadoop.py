from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

print("Spark:", spark.version)

print(
    "Hadoop:",
    spark.sparkContext._jvm.org.apache.hadoop.util.VersionInfo.getVersion()
)

spark.stop()