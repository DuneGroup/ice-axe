from snowflake.snowpark.functions import col
from snowflake.snowpark.context import get_active_session

import streamlit as st

@st.cache_data
def get():
    session = get_active_session()
    users_table = session.table("snowflake.account_usage.users")
    users_df = users_table.filter(
        col("NAME").is_not_null()
    )
    
    return users_df.to_pandas()['NAME'].to_list()

@st.cache_data
def load_data(start_date, end_date, user_search):
    session = get_active_session()

    # Load login history
    login_history_table = session.table("snowflake.account_usage.login_history")
    login_df = login_history_table.filter(
        (col("EVENT_TIMESTAMP").cast("date") >= start_date) &
        (col("EVENT_TIMESTAMP").cast("date") <= end_date)
    )

    if user_search is not None:
        login_df = login_df.filter(col("USER_NAME").like(f'%{user_search}%'))

    return login_df.to_pandas()