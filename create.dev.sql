-- Setup script for the ice axe application.
CREATE database iceaxe;
CREATE SCHEMA IF NOT EXISTS core;
GRANT USAGE ON SCHEMA core TO ROLE accountadmin;

CREATE SCHEMA code_schema;
GRANT USAGE ON SCHEMA code_schema TO ROLE accountadmin;

-- creating dev stage for udf python filewas
CREATE SCHEMA STAGE_CONTENT;
CREATE OR REPLACE STAGE STAGE_CONTENT.ICE_AXE_stage
  FILE_FORMAT = (TYPE = 'csv' FIELD_DELIMITER = '|' SKIP_HEADER = 1);

-- creating Python UDFT
create or replace function code_schema.detector(query_id varchar, query_type varchar, query_text varchar)
returns table (query_id varchar, lead_name varchar)
language python
runtime_version=3.11
IMPORTS = ('@STAGE_CONTENT.ICE_AXE_STAGE/streamlit/analytics/udf.py')
handler='udf.LeadsDetector'
;

GRANT USAGE ON FUNCTION code_schema.detector(VARCHAR, VARCHAR, VARCHAR) TO ROLE accountadmin;


CREATE SCHEMA IF NOT EXISTS results;
GRANT USAGE ON SCHEMA results TO ROLE accountadmin;

CREATE TABLE IF NOT EXISTS results.leads (
  QUERY_ID varchar, 
  user_name varchar,
  lead_name varchar
); 