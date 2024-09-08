-- Setup script for the Hello Snowflake! application.
CREATE APPLICATION ROLE app_public;
CREATE SCHEMA IF NOT EXISTS core;
GRANT USAGE ON SCHEMA core TO APPLICATION ROLE app_public;

CREATE OR ALTER VERSIONED SCHEMA code_schema;
GRANT USAGE ON SCHEMA code_schema TO APPLICATION ROLE app_public;


-- creating Python UDFT
create or replace function code_schema.detector(query_id varchar, query_type varchar, query_text varchar)
returns table (query_id varchar, lead_name varchar)
language python
runtime_version=3.11
IMPORTS = ('/streamlit/analytics/udf.py')
handler='udf.LeadsDetector'
;

GRANT USAGE ON FUNCTION code_schema.detector(VARCHAR, VARCHAR, VARCHAR) TO APPLICATION ROLE app_public;

CREATE SCHEMA IF NOT EXISTS results;
CREATE TABLE IF NOT EXISTS results.leads (
  QUERY_ID varchar, 
  user_name varchar,
  lead_name varchar
); 

CREATE STREAMLIT code_schema.ICE_AXE_streamlit
  FROM '/streamlit'
  MAIN_FILE = '/app.py'
;

GRANT USAGE ON STREAMLIT code_schema.ICE_AXE_streamlit TO APPLICATION ROLE app_public;
