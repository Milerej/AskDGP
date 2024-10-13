# Imports
import os
import hmac
import pandas as pd
import openai
import boto3
import streamlit as st
from dotenv import load_dotenv
from io import StringIO

# Initialize Streamlit app
st.set_page_config(page_title="DGP Chatbot", page_icon="🤖")

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("REGION_NAME")
AWS_BUCKET = os.getenv("bucket_name")

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize the S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Sidebar Navigation
with st.sidebar:
    st.image("https://www.timeshighereducation.com/sites/default/files/sponsor-logo/white-gif-400px.gif")
    st.markdown("### Navigation")
    page = st.selectbox("Choose a page:", ["Ask DGP", "About Us", "Methodology"])

# Main Page
st.title("Digital Governance Platform (DGP) Chatbot")
st.caption("A Streamlit chatbot powered by Govtech")
with st.expander("Disclaimer", expanded=False, icon="🚨"):
    st.write('''IMPORTANT NOTICE: This web application is developed as a proof-of-concept prototype. The information provided here is NOT intended for actual usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters. Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output. Always consult with qualified professionals for accurate and personalized advice.''')

# Function to read data from S3
def read_data_from_s3(bucket_name, file_key):
    """Read CSV data from an S3 bucket and return as a DataFrame."""
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        csv_content = response['Body'].read().decode('utf-8')
        return pd.read_csv(StringIO(csv_content))
    except Exception as e:
        st.error(f"Error reading data from S3: {e}")
        return None

# Function to check password
def check_password():
    """Returns `True` if the user has the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False

# Main application flow
if not check_password():
    st.stop()  # Stop if password validation fails.

# Load data from S3
file_key = 'Good_copy_fixed_anonymised_data.csv'
data = read_data_from_s3(AWS_BUCKET, file_key)

# Check if data was successfully loaded
if data is None:
    st.error("Failed to load data from S3. Please check your bucket name and file key.")
    st.stop()  # Stop execution if data loading fails

# Initialize messages in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello there! Please enter your query to continue."}]

# Function to chunk data into manageable pieces
def chunk_data(data, chunk_size=5):
    """Chunk a DataFrame into smaller DataFrames."""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

# Function to search for answers in the chunks
def search_chunks(prompt, chunks, query_field, reply_field, additional_field):
    relevant_replies = []
    for chunk in chunks:
        chunk[query_field] = chunk[query_field].astype(str)
        chunk[reply_field] = chunk[reply_field].astype(str)
        chunk[additional_field] = chunk[additional_field].astype(str)
        
        chunk_str = ' '.join(chunk[query_field].tolist())
        if any(word in chunk_str.lower() for word in prompt.lower().split()):
            for idx in chunk.index:
                relevant_replies.append((chunk[reply_field][idx], chunk[additional_field][idx]))
    return relevant_replies

# Display chat messages for Ask DGP page
if page == "Ask DGP":
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    data_chunks = chunk_data(data, chunk_size=5)
    query_field = "Details of Query"
    reply_field = "Reply"
    additional_field = "Additional Comments"

    # Gather user input
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # Search for relevant replies
        relevant_replies = search_chunks(prompt, data_chunks, query_field, reply_field, additional_field)

        if relevant_replies:
            search_summary = "\n".join([f"Reply: {r[0]}\nAdditional Comments: {r[1]}" for r in relevant_replies[:5]])
        else:
            search_summary = "Sorry, I couldn't find any relevant information based on your query."

        ai_prompt = f"""
        You are an AI chatbot. Here's a user's query and the corresponding search results from the data:

        User's Query: {prompt}

        Relevant Replies:
        {search_summary}

        Please provide a concise and well-structured response based on the retrieved replies. Thank the user, and if appropriate, let them know their query is being closed.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": ai_prompt}
                ],
                max_tokens=150,
                temperature=0.5
            )
            msg = response.choices[0].message.content.strip()
        except Exception as e:
            msg = f"An error occurred: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

# Content for About Us
elif page == "About Us":
    st.title("About Us")
    st.write("""1) Background

    The Digital Governance Platform (DGP) is designed to transform Whole-of-Government ICT & SS Governance, aiming to manage ICT risks more effectively and deliver improved digital services.

    The ITSM platform serves as the central system for agency users to report DGP-related issues or submit queries. Currently, a lean DGP Ops team handles initial ticket resolution, using their knowledge, past responses, and available resources. Complex issues are escalated to the Subject Matter Experts (SMEs) such as Product teams, Process Owners, Module Owners and/or Technical Teams.

    This process is heavily reliant on manual human intervention to look back at historical responses of similar nature to address some of the queries. It may also be required to reference to relevant source (e.g. Manuals, User Guides, Forms, Notices and Announcements) that are available on the DGP Portal, which is time-consuming and inefficient.

    2) Problem Statement

    How may we streamline the ITSM inquiry process to:

    a) Provide prompt and accurate responses to queries

    b) Reduce manual workload and enhance efficiency

    3) How would you try to solve this problem?

    By implementing a Large Language Model (LLM) to handle queries, we believe that the POC is able to address repeated ITSM queries which forms at least 60% of the ITSM Tickets received. This will help to:

    a) Enable Agency Users to quickly resolve their concerns and

    b) Free up the capacity of the Ops Team to focus on more complex and/or critical queries and tasks.

    4) How would you think LLM can be used to support your solution?

    Using the LLM's library and features, it is able to mimic the Ops Team's ability to provide clarity and address Agency Users' issues and queries based on relevant sources (e.g., Advisories, Circulars, User Guides, Functional Specs and FAQs). For unresolved issues and queries that are complex, the LLM may request that a ticket be logged at the end of the session. The Ops Team and SMEs will follow up to address the remaining complex queries. For continuous enhancement, data from resolved complex issues and queries can be updated to the LLM to further reduce manual intervention by the Ops Team and SMEs.

    5) What are the relevant data do you currently collect and already have?

    The data in use for this POC are mainly from ITSM. The data has been anonymised and desensitised using Cloak.

    6) Features

    The Chatbot will include the following features:

    a) Natural Language Processing (NLP) - Ability to understand, interpret and communicate to Users in human language.

    b) Clarity of issues and problems - Ability to deep dive into the User's questions by asking follow-up questions.

    c) Contextualise resolution - Ability to identify User's purpose and ask based on the interactions and provide contextualised replies to resolve User's queries.

    d) Augmentation to Ops Team - Ability to handle basic repeated queries by sieving through past responses of similar nature.
    """)

# Content for Methodology
elif page == "Methodology":
    st.title("Methodology")
    st.image('C:/Users/jerel/Desktop/AI Bootcamp POC - DGP Chatbot/venv/Flow1.PNG')

    st.write('''
    Use Case 1:
    Users entered difficulties in updating a record in DGP and the User would like to seek clarifications on how they are able to perform the update. 
    The Chatbot is able to address the user's query by citing that the system is currently locked for updating due to an ongoing exercise.
    
    Use Case 2: 
    Users would like to enquire about <to insert a use case> and the User would like to seek clarifications on how to <insert action>. 
    The Chatbot is unable to address the user's query, hence <insert chatbot action>. 
    ''')