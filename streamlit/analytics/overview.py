import streamlit as st
 
def plot_login_frequency(login_data):
    login_frequency = login_data['USER_NAME'].value_counts().reset_index()
    login_frequency.columns = ['User', 'Frequency']

    st.bar_chart(login_frequency.set_index('User'))