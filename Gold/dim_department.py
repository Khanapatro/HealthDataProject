-- Create dimension table
CREATE TABLE IF NOT EXISTS gold.dim_department
(
    Dept_Id STRING,
    SRC_Dept_Id STRING,
    Name STRING,
    datasource STRING
);

-- Remove old data
TRUNCATE TABLE gold.dim_department;

-- Load latest valid department records
INSERT INTO gold.dim_department
SELECT DISTINCT
    Dept_Id,
    SRC_Dept_Id,
    Name,
    datasource
FROM silver.departments
WHERE is_quarantined = false;

-- Validate output
SELECT *
FROM gold.dim_department;
