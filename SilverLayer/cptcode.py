from pyspark.sql import SparkSession, functions as f

# Read the CSV file
cptcodes_df = spark.read.csv("/mnt/landing/cptcodes/*.csv", header=True)

# Replace whitespaces in column names with underscores and convert to lowercase
for col in cptcodes_df.columns:
    new_col = col.replace(" ", "_").lower()
    cptcodes_df = cptcodes_df.withColumnRenamed(col, new_col)
cptcodes_df.createOrReplaceTempView("cptcodes")
display(cptcodes_df)

# COMMAND ----------

# DBTITLE 1,Parquet file creation
cptcodes_df.write.format("parquet").mode("overwrite").save("/mnt/bronze/cpt_codes")
