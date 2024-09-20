import streamlit as st

from snowflake.snowpark.context import get_active_session


@st.cache_data
def max_analysis_end_time():
    """
    SNOWFLAKE.ACCOUNT_USAGE tables are updated at different frequency, we
    can't analyze events for which we don't have data in all three tables.
    """
    session = get_active_session()

    res = session.sql('''
            WITH dataset_watermark as (
                select 'SESSIONS' as DATASET_NAME
                    , max(CREATED_ON) as LAST_TS
                from SNOWFLAKE.ACCOUNT_USAGE.SESSIONS
                UNION
                select 'QUERY_HISTORY' as DATASET_NAME
                    , max(START_TIME) as LAST_TS
                from SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
                UNION
                select 'LOGIN_HISTORY' as DATASET_NAME
                    , max(EVENT_TIMESTAMP) as LAST_TS
                from SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY l
            )
            select min(LAST_TS) as MAX_ALLOWED_TS from dataset_watermark;
    ''').collect()

    return res[0]['MAX_ALLOWED_TS']

@st.cache_data
def least_common_app(start_date, end_date):
    session = get_active_session()

    df = session.sql('''
        select PARSE_JSON(CLIENT_ENVIRONMENT):APPLICATION::STRING AS CLIENT_APPLICATION
            , count(DISTINCT SESSION_ID) as SESSION_COUNT
        from SNOWFLAKE.ACCOUNT_USAGE.SESSIONS
        where USER_NAME not in ('WORKSHEETS_APP_USER', 'SNOWFLAKE', 'SYSTEM')
        and CREATED_ON >= ? and CREATED_ON <= ?
        group by 1;
    ''', params=[
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d %H:%M:%S %Z')]
    ).to_pandas(block=True)

    return df