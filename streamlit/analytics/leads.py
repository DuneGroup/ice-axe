import streamlit
import logging

st_logger = logging.getLogger(streamlit.__name__)

def select_all_flt(query_history_df):
    return (
        query_history_df['QUERY_TEXT'].str.contains('select *', False, regex=False) &
        (~(query_history_df['QUERY_TEXT'].str.contains('where', False)))
    )


def show_tables(query_history_df):
    return (
        query_history_df['QUERY_TEXT'].str.contains('SHOW TABLES', False)
    )


def create_temp_storage(query_history_df):
    return (
        query_history_df['QUERY_TEXT'].str.contains('^SHOW TABLES', False) & 
        query_history_df['QUERY_TEXT'].str.contains('STORAGE', False)
    )


def ten_largest_queries(query_history_df):
    return (
        query_history_df['ROWS_PRODUCED'] > 2000
    )


def accountadmin_changes(query_history_df):
    return (
        (query_history_df['EXECUTION_STATUS'] == 'SUCCESS') & 
        (query_history_df['QUERY_TYPE'] == 'GRANT') 
    )


def copy_http(query_history_df):
    return (
        query_history_df['QUERY_TEXT'].str.contains('COPY INTO') & 
        query_history_df['QUERY_TEXT'].str.contains('http')
    )


def get_file(query_history_df):
    return (
        query_history_df['QUERY_TEXT'].str.contains('GET', False) & 
        query_history_df['QUERY_TEXT'].str.contains('file:')
    )


def copy_into_select_all(query_history_df):
    return (
        query_history_df['QUERY_TEXT'].str.contains('^COPY INTO', False) & 
        query_history_df['QUERY_TEXT'].str.contains('^SELECT *', False)
    )


def impactful_modifications(query_history_df):
    modifications_keywords = [
        'create role', 'manage grants', 'create integration','alter integration', 'create share','create account'
        ,'monitor usage', 'ownership', 'drop table', 'drop database', 'create stage'
        ,'drop stage', 'alter stage', 'create user', 'alter user', 'drop user'
        ,'create_network_policy', 'alter_network_policy', 'drop_network_policy', 'copy'
    ]
    
    return (
        (query_history_df['EXECUTION_STATUS'] == 'SUCCESS') & 
        ~(query_history_df['QUERY_TYPE'].isin(['SELECT', 'SHOW', 'DESCRIBE']).any()) &
        (query_history_df['QUERY_TEXT'].str.contains('.*' + '|'.join(modifications_keywords) + '.*', False))
    )


def least_common_app(query_history_df):
    rare_apps = query_history_df.groupby('CLIENT_APPLICATION')['SESSION_ID'].nunique().reset_index(name='Session Count')
    app_names = rare_apps['CLIENT_APPLICATION'].tolist()
    return (
        query_history_df['CLIENT_APPLICATION'].isin(app_names)
    )


def frostbite_used(query_history_df):
    return (
        query_history_df['CLIENT_APPLICATION'] == 'rapeflake'
    )


def dbeaver_used(query_history_df):
    return (
        query_history_df['CLIENT_APPLICATION'] == 'DBeaver_DBeaverUltimate'
    )


all_threat_leads = [
    {
        "name": "select_all_without_where",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "select * queries that do not contain a WHERE clause",
        "df_filter": select_all_flt
    },
    {
        "name": "copy_into_select_all",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "COPY INTO and select * in a single query.",
        "df_filter": copy_into_select_all
    },
    {
        "name": "show_tables",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Performing a show tables query",
        "df_filter": show_tables
    },
    {
        "name": "create_temp_storage",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Creation of temporary storage",
        "df_filter": create_temp_storage
    },
    {
        "name": "10_largest_queries",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Top 10 largest queries by rows_produced",
        "df_filter": ten_largest_queries
    },
    {
        "name": "dbeaver_used",
        "mitre_technique_id": "T1199",
        "mitre_technique_description": "Trusted Relationship",
        "description": "DBEAVER Usage",
        "df_filter": dbeaver_used
    },
    {
        "name": "accountadmin_changes",
        "mitre_technique_id": "T1098",
        "mitre_technique_description": "Account Manipulation",
        "description": "Role grants",
        "df_filter": accountadmin_changes
    },
    {
        "name": "impactful_modifications",
        "mitre_technique_id": "T1484",
        "mitre_technique_description": "Domain or Tenant Policy Modification",
        "description": "Impactful modifications",
        "df_filter": impactful_modifications
    },
    {
        "name": "least_common_applications_used",
        "mitre_technique_id": "",
        "mitre_technique_description": "Other",
        "description": "Applications by prevelance",
        "df_filter": least_common_app
    },
    {
        "name": "copy_http",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "A Query containing COPY INTO and http keyword",
        "df_filter": copy_http
    },
    {
        "name": "get_file",
        "mitre_technique_id": "T1567",
        "mitre_technique_description": "Exfiltration Over Web Service",
        "description": "Get file contents",
        "df_filter": get_file
  },
    {
        "name": "session_usage",
        "mitre_technique_id": "T1199",
        "mitre_technique_description": "Trusted Relationship",
        "description": "Session usage",
        "df_filter": least_common_app
    },
    {
        "name": "frostbite_used",
        "mitre_technique_id": "T1199",
        "mitre_technique_description": "Trusted Relationship",
        "description": "FROSTBITE usage",
        "df_filter": frostbite_used
    }
]


def get_all_leads_names():
    return [lead['name'] for lead in all_threat_leads]


def get_all_leads_techniques():
    techniques = [lead['mitre_technique_description'] for lead in all_threat_leads]
    return list(set(techniques))


def get_all_leads(query_history_df):
    results = []
    idx = 0
    for lead in all_threat_leads:
        st_logger.info(f'{idx}: {lead["name"]}')
        results.append(
            {
                'name': lead['name'],
                'technique': lead['mitre_technique_description'],
                'description': lead['description'],
                'mask': lead['df_filter'](query_history_df)
            }
        )
        idx += 1

    return results