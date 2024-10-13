#Imports
import streamlit as st

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

st.write('''About Us

1) Background

​
The Digital Governance Platform (DGP) is designed to transform Whole-of-Government ICT & SS Governance, aiming to manage ICT risks more effectively and deliver improved digital services.​

​
The ITSM platform serves as the central system for agency users to report DGP-related issues or submit queries. Currently, a lean DGP Ops team handles initial ticket resolution, using their knowledge, past responses, and available resources. Complex issues are escalated to the Subject Matter Experts (SMEs) such as Product teams, Process Owners, Module Owners and/or Technical Teams.​

​
This process is heavily reliant on manual human intervention to look back at historical responses of similar nature to address some of the queries. It may also be required to reference to relevant source (e.g. Manuals, User Guides, Forms, Notices and Announcements) that are available on the DGP Portal, which is time-consuming and inefficient.​

​

2) Problem Statement
         
​
How may we streamline the ITSM inquiry process to:​

​
    a) Provide prompt and accurate responses to queries​

​
    b) Reduce manual workload and enhance efficiency    

​

3) How would you try to solve this problem?
         
​
By implementing a Large Language Model (LLM) to handle queries, we believe that the POC is able to address repeated ITSM queries which forms at least 60% of the ITSM Tickets received​
This will help to:​

​
    a) Enable Agency Users to quickly resolve their concerns and

​
    b) Free up the capacity of the Ops Team to focus on more complex and/or critical queries and tasks.​

​

4) How would you think LLM can be used to support your solution?

​
Using the LLM's library and features, it is able to mimic the Ops Team's ability to provide clarity and address Agency Users' issues and queries based on relevant sources (e.g., Advisories, Circulars, User Guides, Functional Spects and FAQs).​
For unresolved issues and queries that are complex, the LLM may request that a ticket be logged at the end of the session. The Ops Team and SMEs will follow up to address the remaining complex queries.​
For continuous enhancement, data from resolved complex issues and queries can be updated to the LLM to further reduce manual intervention by the Ops Team and SMEs.

​

5) What are the relevant data do you currently collect and already have?
         
​
The data in use for this POC are mainly from ITSM​. The data has been anonymised and desensitised using Cloak.

​

6) Features

​
​The Chatbot will incude the following features

​
    a) Natural Language Process (NLP) - Ability to understand, inteprete and commmunicate to Users in human language

​
    b) Clarity of issues and problems - Ability to deep dive into the User's questions by asking follow up questions

​
    c) Contexualise resolution - Ability to identify User's purpose and ask based on the interactions and provide contextualised reply to resolve User's queries

​
    d) Augmentation to Ops Team - Ability to handle basic repeated queries by sieving through past responses of similar nature       
''')