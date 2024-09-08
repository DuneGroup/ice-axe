from snowflake.snowpark.context import get_active_session
#from udf import UDF_THREAT_LEADS

# SQL LEADS
def ioc_apps():
    query = '''
        select  h.query_id, 
                h.user_name,
                'ioc_app_name' as lead_name
        from SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY h
        left JOIN SNOWFLAKE.ACCOUNT_USAGE.SESSIONS s on h.SESSION_ID = s.SESSION_ID
        where h.user_name not in ('WORKSHEETS_APP_USER', 'SNOWFLAKE')
        and s.authentication_method is not null
        and PARSE_JSON(s.CLIENT_ENVIRONMENT):APPLICATION::STRING  IN ('rapeflake', 'DBeaver_DBeaverUltimate');
    '''

def least_common_app():
    query = '''
        select PARSE_JSON(CLIENT_ENVIRONMENT):APPLICATION::STRING AS CLIENT_APPLICATION
            , count(DISTINCT SESSION_ID) as SESSION_COUNT
        from SNOWFLAKE.ACCOUNT_USAGE.SESSIONS
        where USER_NAME != 'SNOWFLAKE'
        group by 1
        order by SESSION_COUNT asc
    '''

def ten_largest_queries():
    query = '''
        SELECT QUERY_ID
            , USER_NAME
            , 'ten_largest_queries' AS lead_name
        FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
        where ROWS_PRODUCED is not NULL
        ORDER BY ROWS_PRODUCED DESC
        limit 10;
    '''

def ten_largest_unloads():
    query = '''
        SELECT QUERY_ID
            , USER_NAME
            , QUERY_TEXT
            , ROWS_UNLOADED
            , 'top_10_rows_unloaded' AS lead_name
        FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
        where ROWS_UNLOADED is not NULL
        and ROWS_UNLOADED > 0
        and user_name not in ('SYSTEM', 'SNOWFLAKE' )
        ORDER BY ROWS_UNLOADED DESC
        limit 10;
    '''

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
    },
    {
        "type": "sql",
        "name": "least_common_applications_used",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Applications by prevelance",
        "detect_fn": least_common_app
    }
]

THREAT_LEADS = SQL_THREAT_LEADS #+ UDF_THREAT_LEADS

# TODO: fix table location 
# probably this table needs to be create by the native app
def generate_leads_results(start_date, end_date):
    session = get_active_session()

    res = session.sql('''
    INSERT INTO results.leads
        select h.QUERY_ID
        , detector.lead_name
        from SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY h
            , table(results.detector(QUERY_ID, QUERY_TYPE, QUERY_TEXT))
        WHERE START_TIME >= ? AND START_TIME <= ?;
    ''', params=[start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d %H:%M:%S %Z')]).collect()


def get_results():
    session = get_active_session()

    leads_df = session.sql('SELECT QUERY_ID, lead_name FROM results.leads').to_pandas(block=True)

    return leads_df


def get_all_leads_names():
    return [lead['name'] for lead in THREAT_LEADS]


def get_all_leads_techniques():
    techniques = [lead['mitre_technique_description'] for lead in THREAT_LEADS]
    return list(set(techniques))