import streamlit as st
import time
import main

st.title("📧 InboxPilot - Email Automation Tool")
st.write("Automate your email sending process with ease!")

if st.button("Send Emails"):
    st.write("Starting the email sending process...")
    
    with st.spinner('Sending emails...'):
        time.sleep(2)  # Simulate a delay for demonstration purposes
        a=main.email_data()
    st.success('Emails have been sent successfully!')