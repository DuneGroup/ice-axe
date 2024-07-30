import streamlit as st

from snowflake.snowpark.context import get_active_session


@st.cache_data
def get_for_dates(start_date, end_date):
    session = get_active_session()

    query_history_df = session.sql("""select START_TIME
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
                , QUERY_ID
                , QUERY_TYPE
                , QUERY_TEXT
                , execution_status
                , ROWS_PRODUCED
                , BYTES_WRITTEN
                , ROWS_INSERTED
                , ROWS_UPDATED
                , ROWS_DELETED
            from SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY h
            left JOIN SNOWFLAKE.ACCOUNT_USAGE.SESSIONS s on h.SESSION_ID = s.SESSION_ID
            left join SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY l on s.LOGIN_EVENT_ID = l.EVENT_ID
            where h.user_name not in ('WORKSHEETS_APP_USER') // internal snowflake user
            and LOGIN_IP != '0.0.0.0' // internal snowflake activity
            and session_auth is not null // filter out snow generate sql queries that don't have a session id present in ACCOUNT_USAGE.SESSIONS
            and START_TIME BETWEEN ? and ?
            order by START_TIME DESC""", 
            params=[start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        ).to_pandas(block=True)

    typed_df = query_history_df.astype({'EXECUTION_STATUS': 'string'})

    return typed_df
