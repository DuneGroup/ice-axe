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

    session.sql(
        '''
        CALL code_schema.refresh_and_cluster_tables();
        '''
    ).collect()


    #TODO to really paginate this we have to query each lead type separately, otherwise we are 
    # truncating a table that contains results for all lead types which is not what we want to show
    # the user. So, we should have something like:
    # for lead in SQL_THREAT_LEADS:
    # ... get a paginated lead df ....
    # now the issue that will come up is how do you get the next page for each df ... in that scenario it might
    # make sense to move this logic into the app, and just provide APIs here that let it do something like:
    #   fetch_paginated_lead_df(lead_name, page_number)
    leads_df = session.sql(
        '''
        WITH filtered_query_history AS (
            SELECT query_id, user_name, session_id, query_type, query_text, execution_status, start_time
            FROM view_query_history
            WHERE query_id IN (SELECT query_id FROM results.leads)
        ),
        filtered_sessions AS (
            SELECT session_id, authentication_method, client_application_id, client_application_version, client_environment, login_event_id
            FROM view_sessions
            WHERE authentication_method IS NOT NULL
        ),
        filtered_login_history AS (
            SELECT event_id, reported_client_type, reported_client_version, client_ip, event_timestamp
            FROM view_login_history
            WHERE event_id IN (SELECT login_event_id FROM filtered_sessions)
        )
        SELECT r.lead_name
            , h.start_time
            , h.user_name
            , s.authentication_method AS session_auth
            , s.session_id
            , l.reported_client_type AS login_client_type
            , s.client_application_id AS session_client_app
            , s.client_application_version AS session_client_version
            , l.reported_client_version AS login_client_version
            , s.client_environment AS raw_client_env
            , PARSE_JSON(s.client_environment) AS client_env
            , client_env:application::STRING AS client_application
            , client_env:os::STRING AS client_os
            , client_env:os_version::STRING AS client_os_version
            , l.client_ip AS login_ip
            , l.event_timestamp AS login_timestamp
            , r.query_id
            , h.query_type
            , h.query_text
            , h.execution_status
        FROM results.leads r
        LEFT JOIN filtered_query_history h 
            ON r.query_id = h.query_id
        LEFT JOIN filtered_sessions s 
            ON h.session_id = s.session_id
        LEFT JOIN filtered_login_history l
            ON s.login_event_id = l.event_id
        ORDER BY h.start_time DESC
        LIMIT 3000;
        '''
        ).to_pandas(block=True)

    return leads_df


def get_all_leads_names():
    return [lead['name'] for lead in THREAT_LEADS]


def get_lead_names_by_technique(technique_name):
    return [lead['name'] for lead in THREAT_LEADS if lead['mitre_technique_description'] == technique_name]


def get_all_leads_techniques():
    techniques = [lead['mitre_technique_description'] for lead in THREAT_LEADS]
    return list(set(techniques))