from openai import OpenAI
import streamlit as st

from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("OPENAI_API_KEY")
password = os.getenv("password")


#SIDEBAR
with st.sidebar:
    st.image("https://www.timeshighereducation.com/sites/default/files/sponsor-logo/white-gif-400px.gif")
    "[Ask DGP](https://askdgp.streamlit.app/)"
    "[About Us](https://askdgp.streamlit.app/)"
    "[Methodology](https://askdgp.streamlit.app/)"

#MAIN AREA - TITLE AND DISCLAIMER
st.title("Digital Governance Platform (DGP) Chatbot - Proof Of Concept")
st.caption("Powered by Govtech")
with st.expander("Disclaimer",expanded=False,icon="🚨"):
    st.write('''
    IMPORTANT NOTICE: This web application is developed as a proof-of-concept prototype. The information provided here is NOT intended for actual usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

    Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

    Always consult with qualified professionals for accurate and personalized advice.
    ''')


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello there! Please enter your password to continue."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not password:
        st.info("Please enter the CORRECT password to continue.")
        st.stop()
    
    client = OpenAI(api_key=key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
