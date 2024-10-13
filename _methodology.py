import streamlit as st
from PIL import Image
import cv2
import numpy as np

# SIDEBAR
with st.sidebar:
    st.image("https://www.timeshighereducation.com/sites/default/files/sponsor-logo/white-gif-400px.gif")
    st.markdown("[Ask DGP](https://chatdgp.streamlit.app/)")
    st.markdown("[About Us](https://chatdgp.streamlit.app/)")
    st.markdown("[Methodology](https://chatdgp.streamlit.app/)")
    
# Initialize Streamlit app
st.set_page_config(page_title="DGP Chatbot", page_icon="🤖")
st.title("Digital Governance Platform (DGP) Chatbot")
st.caption("A Streamlit chatbot powered by Govtech")
with st.expander("Disclaimer",expanded=False,icon="🚨"):
    st.write('''
    IMPORTANT NOTICE: This web application is developed as a proof-of-concept prototype. The information provided here is NOT intended for actual usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

    Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

    Always consult with qualified professionals for accurate and personalized advice.
    ''')

st.write('''Methodology''')

st.image('C:/Users/jerel/Desktop/AI Bootcamp POC - DGP Chatbot/venv/Flow1.PNG')

st.write('''
Use Case 1 : 
    Users entered difficulties in updating a record in DGP and the User would like to seek clarifications on how they are able to perform the update. 
    The Chatbot is able to address the user's query by citing that the system is currently locked for updating due to an ongoing exercise. 
​
         
​
       
Use Case 2 : 
    Users would like to enquire about <to insert a use case> and the User would like to seek clarifications on how to <insert action>. 
    The Chatbot is unable to address the user's query, hence <insert chatbot action>. 
''')


