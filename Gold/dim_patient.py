-- Create patient dimension table
CREATE TABLE IF NOT EXISTS gold.dim_patient
(
    patient_key STRING,
    src_patientid STRING,
    firstname STRING,
    lastname STRING,
    middlename STRING,
    ssn STRING,
    phonenumber STRING,
    gender STRING,
    dob DATE,
    address STRING,
    datasource STRING
);

-- Remove existing data
TRUNCATE TABLE gold.dim_patient;

-- Load current valid patient records
INSERT INTO gold.dim_patient
SELECT
    patient_key,
    src_patientid,
    firstname,
    lastname,
    middlename,
    ssn,
    phonenumber,
    gender,
    dob,
    address,
    datasource
FROM silver.patients
WHERE is_current = true
  AND is_quarantined = false;

-- Validate output
SELECT *
FROM gold.dim_patient;
