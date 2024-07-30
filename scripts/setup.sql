-- Setup script for the Hello Snowflake! application.
CREATE APPLICATION ROLE app_public;
CREATE SCHEMA IF NOT EXISTS core;
GRANT USAGE ON SCHEMA core TO APPLICATION ROLE app_public;

CREATE OR ALTER VERSIONED SCHEMA code_schema;
GRANT USAGE ON SCHEMA code_schema TO APPLICATION ROLE app_public;


CREATE STREAMLIT code_schema.ICE_AXE_streamlit
  FROM '/streamlit'
  MAIN_FILE = '/app.py'
;

GRANT USAGE ON STREAMLIT code_schema.ICE_AXE_streamlit TO APPLICATION ROLE app_public;
