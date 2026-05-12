-- Create table if not exists
CREATE TABLE IF NOT EXISTS gold.dim_cpt_code
(
    cpt_codes STRING,
    procedure_code_category STRING,
    procedure_code_descriptions STRING,
    code_status STRING,
    refreshed_at TIMESTAMP
);

-- Remove old data
TRUNCATE TABLE gold.dim_cpt_code;

-- Insert latest records
INSERT INTO gold.dim_cpt_code
SELECT
    cpt_codes,
    procedure_code_category,
    procedure_code_descriptions,
    code_status,
    current_timestamp() AS refreshed_at
FROM silver.cptcodes
WHERE is_quarantined = false
  AND is_current = true;

-- Validate data
SELECT * 
FROM gold.dim_cpt_code;
