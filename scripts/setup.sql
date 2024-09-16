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

CREATE OR REPLACE PROCEDURE code_schema.refresh_and_cluster_tables()
RETURNS STRING
LANGUAGE JAVASCRIPT
EXECUTE AS OWNER
AS
$$
try {
    var sql_commands = [
        `CREATE OR REPLACE TABLE query_history AS
        SELECT *
        FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY;`,

        `CREATE OR REPLACE TABLE sessions AS
        SELECT *
        FROM SNOWFLAKE.ACCOUNT_USAGE.SESSIONS;`,

        `CREATE OR REPLACE TABLE login_history AS
        SELECT *
        FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY;`,

        `ALTER TABLE query_history
        CLUSTER BY (QUERY_ID, SESSION_ID, START_TIME);`,

        `ALTER TABLE sessions
        CLUSTER BY (SESSION_ID, LOGIN_EVENT_ID);`,

        `ALTER TABLE login_history
        CLUSTER BY (EVENT_ID);`,

        `CREATE OR REPLACE VIEW view_query_history AS
        SELECT *
        FROM query_history;`,

        `CREATE OR REPLACE VIEW view_sessions AS
        SELECT *
        FROM sessions;`,

        `CREATE OR REPLACE VIEW view_login_history AS
        SELECT *
        FROM login_history;`
    ];

    for (var i = 0; i < sql_commands.length; i++) {
        snowflake.execute({sqlText: sql_commands[i]});
    }

    return "Tables and views refreshed and clustered successfully.";
} catch (err) {
    return "Failed: " + err;
}
$$
;

GRANT USAGE ON PROCEDURE code_schema.refresh_and_cluster_tables() TO APPLICATION ROLE app_public;

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
