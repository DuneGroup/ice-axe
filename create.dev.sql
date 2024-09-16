-- Setup script for the ice axe application.
USE DATABASE iceaxe;

CREATE SCHEMA IF NOT EXISTS core;
GRANT USAGE ON SCHEMA core TO ROLE accountadmin;

CREATE SCHEMA code_schema;
GRANT USAGE ON SCHEMA code_schema TO ROLE accountadmin;

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

-- TODO, add start and end time params and filter this down further using that
CREATE OR REPLACE PROCEDURE code_schema.refresh_and_cluster_tables()
RETURNS STRING
LANGUAGE JAVASCRIPT
EXECUTE AS CALLER
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
$$;