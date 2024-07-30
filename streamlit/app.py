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
        start_date = st.date_input('Start date', value=pd.to_datetime('today')-datetime.timedelta(days=7))

        end_date = st.date_input('End date', value=pd.to_datetime('today'))

    summary_tab, leads_tab, user_activity_tab = st.tabs(['Summary', 'Leads Details', 'User Activity Details'])

    query_history_df = metrics.query_history.get_for_dates(start_date=start_date, end_date=end_date)
    
    all_threat_leads = analytics.leads.get_all_leads(query_history_df)
    all_threats_masks = [lead['mask'] for lead in all_threat_leads]
    all_threats_df = query_history_df[np.logical_or.reduce(all_threats_masks)]

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
            unusual_apps = query_history_df.groupby('CLIENT_APPLICATION')['SESSION_ID'].nunique().reset_index(name='Session Count').sort_values('Session Count').head(10).reset_index(drop=True)
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

        with st.expander("Query History", expanded=True):
            if user_search is not None:
                query_data_display = query_history_df[query_history_df['USER_NAME'] == user_search]
            else:
                query_data_display = query_history_df
            query_data_display.sort_values('START_TIME', ascending=False, inplace=True)
            st.dataframe(query_data_display)

    with leads_tab:
        # Level 3: Details for investigation
        technique_names = analytics.leads.get_all_leads_techniques()
        techniques_selected = st.multiselect('Show Technique Leads', options=technique_names, default=technique_names)
        
        for lead_result in all_threat_leads:
            if lead_result['technique'] not in techniques_selected:
                continue
            
            threat_mask = lead_result['mask']
            threat_df = query_history_df[threat_mask]

            has_threats = False
            if threat_df.shape[0] > 0:
                icon = "❗"
                expanded = True
                has_threats = True
            else:
                icon = "✅"
                expanded = False
            
            #TODO: Native Apps does not support latest streamlit APIs yet, so store icon in the name
            #with st.expander(lead_result['name'], expanded=expanded, icon=icon):
            with st.expander("{} {}".format(icon, lead_result['name']), expanded=expanded):
                st.write(lead_result['description'])
                if has_threats:
                    st.dataframe(threat_df)
                else:
                    st.write("_None found_")

        st.header('All Threats')
        st.dataframe(all_threats_df)

    st.write("Made with ❤️ in California by [Dune Group](https://dunegroup.xyz)")


main()
