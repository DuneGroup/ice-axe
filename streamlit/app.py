import streamlit as st
import pandas as pd
import logging as log
import argparse
import datetime
import numpy as np

from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.exceptions import SnowparkSessionException

import helpers
import analytics
import metrics

log.basicConfig(level=log.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--dev', type=bool, default=False, help='Run in local developer mode')
args = parser.parse_args()

development_mode = args.dev

try:
    get_active_session()

    if not development_mode:
        
        helpers.request_permissions()

except SnowparkSessionException:
    log.info("No active session found")
    
    if development_mode:
        log.info("Running in local developer mode")
        helpers.create_local_session()
    else:
        raise


def main():

    st.set_page_config(layout="wide")

    st.title("⛏️ Ice Axe")
    st.write("Investigate security threats in your Snowflake accounts, natively.") 

    with st.sidebar:

        st.header("Filters")
        max_ts = metrics.query_history.max_analysis_end_time()
        start_date = st.date_input('Start date', value=max_ts-datetime.timedelta(days=7))
        end_date = st.date_input('End date', value=max_ts, max_value=max_ts)

    analytics.leads.generate_leads_results(start_date, end_date)
    all_threats_df = analytics.leads.get_results()

    summary_tab, leads_tab, user_activity_tab = st.tabs(['Summary', 'Leads Details', 'User Activity Details'])

    with summary_tab:
        
        # Level 1: Top level KPIs
        user_threats_df = all_threats_df.groupby(['USER_NAME']).size().reset_index(name='Threat Leads Count')

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="Threat Leads Count",
                value=all_threats_df.shape[0],
                delta_color="off"
                )

            st.header('Users at Risk')
            st.dataframe(user_threats_df)

        with col2:
            st.metric(
                label="Users at Risk Count", 
                value=user_threats_df.shape[0],
                delta_color="off"
            )

            st.header('Unusual Apps')
            unusual_apps = metrics.query_history.least_common_app(start_date, end_date)
            st.dataframe(unusual_apps)

    with user_activity_tab:
        # Level 2: Trends & Patterns

        #TODO: Native Apps does not support latest streamlit APIs yet, so inject 'None' as the first option
        #user_search = st.selectbox('Search by username', metrics.users.get(), index=None)
        user_search = st.selectbox('Search by username', [None] + metrics.users.get())

        col1, col2 = st.columns(2)

        login_data = metrics.users.load_data(start_date, end_date, user_search)
        login_data.sort_values('EVENT_TIMESTAMP', ascending=False, inplace=True)

        with st.expander('Login Frequency by User', expanded=True):
            analytics.overview.plot_login_frequency(login_data)

        # Level 3: Details for investigation  
        with st.expander('Login History', expanded=True):
            st.dataframe(login_data)

        # TODO: rewrite
        #with st.expander("Query History", expanded=True):
        #    if user_search is not None:
        #        query_data_display = query_history_df[query_history_df['USER_NAME'] == user_search]
        #    else:
        #        query_data_display = query_history_df
        #    query_data_display.sort_values('START_TIME', ascending=False, inplace=True)
        #    st.dataframe(query_data_display)

    with leads_tab:
        # Level 3: Details for investigation
        technique_names = analytics.leads.get_all_leads_techniques()
        techniques_selected = st.multiselect('Show Technique Leads', options=technique_names, default=technique_names)
        
        for technique in techniques_selected:
            lead_names = analytics.leads.get_lead_names_by_technique(technique)

            # TODO: probably can be done in one step
            technique_mask = all_threats_df['LEAD_NAME'].isin(lead_names)
            threats_df = all_threats_df[technique_mask]

            has_threats = False
            if threats_df.shape[0] > 0:
                icon = "❗"
                expanded = True
                has_threats = True
            else:
                icon = "✅"
                expanded = False
            
            #TODO: Native Apps does not support latest streamlit APIs yet, so store icon in the name
            #with st.expander(lead_result['name'], expanded=expanded, icon=icon):
            with st.expander("{} {}".format(icon, technique), expanded=expanded):
                #st.write(lead_result['description'])
                if has_threats:
                    st.dataframe(threats_df)
                else:
                    st.write("_None found_")

        st.header('All Threats')
        st.dataframe(all_threats_df)

    st.write("Made with ❤️ in California by [Dune Group](https://dunegroup.xyz)")


main()
