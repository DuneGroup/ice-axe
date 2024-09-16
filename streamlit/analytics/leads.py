from snowflake.snowpark.context import get_active_session
from analytics.udf import UDF_THREAT_LEADS
import streamlit as st


# SQL LEADS
def ioc_apps(start_date, end_date):
    session = get_active_session()

    session.sql('''
        INSERT INTO results.leads
            select  h.query_id, 
                    h.user_name,
                    'ioc_apps' as lead_name
            from SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY h
            left JOIN SNOWFLAKE.ACCOUNT_USAGE.SESSIONS s on h.SESSION_ID = s.SESSION_ID
            where h.user_name not in ('WORKSHEETS_APP_USER', 'SNOWFLAKE', 'SYSTEM')
            and s.authentication_method is not null
            and PARSE_JSON(s.CLIENT_ENVIRONMENT):APPLICATION::STRING  IN ('rapeflake', 'DBeaver_DBeaverUltimate')
            and h.start_time >= ? and h.start_time <= ?;
    ''', params=[
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d %H:%M:%S %Z')]
    ).collect()


def ten_largest_queries(start_date, end_date):
    session = get_active_session()

    session.sql('''
        INSERT INTO results.leads
            SELECT QUERY_ID
                , USER_NAME
                , '10_largest_queries' AS lead_name
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            where ROWS_PRODUCED is not NULL
            and start_time >= ? and start_time <= ?
            ORDER BY ROWS_PRODUCED DESC
            limit 10;
    ''', params=[
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d %H:%M:%S %Z')]
    ).collect()


def ten_largest_unloads(start_date, end_date):
    session = get_active_session()

    session.sql('''
        INSERT INTO results.leads
            SELECT QUERY_ID
                , USER_NAME
                , '10_largest_unloads' AS lead_name
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            where ROWS_UNLOADED is not NULL
            and ROWS_UNLOADED > 0
            and user_name not in ('WORKSHEETS_APP_USER', 'SNOWFLAKE', 'SYSTEM')
            and start_time >= ? and start_time <= ?
            ORDER BY ROWS_UNLOADED DESC
            limit 10;
    ''', params=[
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d %H:%M:%S %Z')]
    ).collect()


SQL_THREAT_LEADS = [
    {
        "type": "sql",
        "name": "10_largest_queries",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Top 10 largest queries by rows_produced",
        "detect_fn": ten_largest_queries
    },
    {
        "type": "sql",
        "name": "10_largest_unloads",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Top 10 largest queries by rows_unloaded",
        "detect_fn": ten_largest_unloads
    },
    {
        "type": "sql",
        "name": "ioc_apps",
        "mitre_technique_id": "T1199",
        "mitre_technique_description": "Trusted Relationship",
        "description": "IOC Application Usage",
        "detect_fn": ioc_apps
    }
]

THREAT_LEADS = SQL_THREAT_LEADS + UDF_THREAT_LEADS


def generate_leads_results(start_date, end_date):
    session = get_active_session()

    # TODO: we don't want to insert duplicate when start-end time are changed
    # or we need to change the logic to not insert duplicates
    #session.sql()
    session.sql('USE DATABASE ICEAXE').collect()
    session.sql('TRUNCATE TABLE results.leads').collect()

    session.sql('''
    INSERT INTO results.leads
        select h.QUERY_ID
               , h.user_name
               , detector.lead_name
        from SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY h
            , table(code_schema.detector(QUERY_ID, QUERY_TYPE, QUERY_TEXT))
        WHERE START_TIME >= ? AND START_TIME <= ?
        AND h.user_name not in ('WORKSHEETS_APP_USER', 'SNOWFLAKE', 'SYSTEM');
    ''', params=[start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d %H:%M:%S %Z')]).collect()

    for lead in SQL_THREAT_LEADS:
        detect_fn = lead['detect_fn']
        detect_fn(start_date, end_date)

@st.cache_data
def get_results():
    session = get_active_session()

    leads_df = session.sql('''
            select r.lead_name
                , START_TIME
                , h.USER_NAME
                , s.authentication_method as SESSION_AUTH
                , s.session_id
                , l.reported_client_type as LOGIN_CLIENT_TYPE
                , s.CLIENT_APPLICATION_ID AS SESSION_CLIENT_APP
                , s.CLIENT_APPLICATION_VERSION AS SESSION_CLIENT_VERSION
                , l.reported_client_version as LOGIN_CLIENT_VERSION
                , s.CLIENT_ENVIRONMENT AS RAW_CLIENT_ENV
                , PARSE_JSON(RAW_CLIENT_ENV) as CLIENT_ENV
                , CLIENT_ENV:APPLICATION::STRING AS client_application
                , CLIENT_ENV:OS::STRING AS client_os
                , CLIENT_ENV:OS_VERSION::STRING AS client_os_version
                , l.CLIENT_IP as LOGIN_IP
                , l.event_timestamp as LOGIN_TIMESTAMP
                , ROLE_NAME
                , r.QUERY_ID
                , QUERY_TYPE
                , QUERY_TEXT
                , execution_status
            from results.leads r
            left join SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY h on r.query_id = h.query_id
            left JOIN SNOWFLAKE.ACCOUNT_USAGE.SESSIONS s on h.SESSION_ID = s.SESSION_ID
            left join SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY l on s.LOGIN_EVENT_ID = l.EVENT_ID
            and session_auth is not null // filter out snow generate sql queries that don't have a session id present in ACCOUNT_USAGE.SESSIONS
            order by START_TIME DESC''').to_pandas(block=True)

    return leads_df


def get_all_leads_names():
    return [lead['name'] for lead in THREAT_LEADS]


def get_lead_names_by_technique(technique_name):
    return [lead['name'] for lead in THREAT_LEADS if lead['mitre_technique_description'] == technique_name]


def get_all_leads_techniques():
    techniques = [lead['mitre_technique_description'] for lead in THREAT_LEADS]
    return list(set(techniques))