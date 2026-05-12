from pyspark.sql import SparkSession, functions as f

#Reading Hospital A departments data 
df_hosa=spark.read.parquet("/mnt/bronze/hosa/providers")

#Reading Hospital B departments data 
df_hosb=spark.read.parquet("/mnt/bronze/hosb/providers")

#union two departments dataframes
df_merged = df_hosa.unionByName(df_hosb)
display(df_merged)

df_merged.createOrReplaceTempView("providers")
