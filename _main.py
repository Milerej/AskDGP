# Imports
import streamlit as st
import hmac
import os
import pandas as pd
import openai
import boto3
from dotenv import load_dotenv
from io import StringIO

# Initialize Streamlit app
st.set_page_config(page_title="DGP Chatbot", page_icon="🤖")

# SIDEBAR
with st.sidebar:
    st.image("https://www.timeshighereducation.com/sites/default/files/sponsor-logo/white-gif-400px.gif")
 

# Main Page
st.title("Digital Governance Platform (DGP) Chatbot")
st.caption("A Streamlit chatbot powered by Govtech")
with st.expander("Disclaimer",expanded=False,icon="🚨"):
    st.write('''
    IMPORTANT NOTICE: This web application is developed as a proof-of-concept prototype. The information provided here is NOT intended for actual usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

    Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.

    Always consult with qualified professionals for accurate and personalized advice.
    ''')

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("REGION_NAME")
AWS_BUCKET = os.getenv("bucket_name")

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize the S3 client with the loaded credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Function to read data from S3
def read_data_from_s3(bucket_name, file_key):
    """Read CSV data from an S3 bucket and return as a DataFrame."""
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        csv_content = response['Body'].read().decode('utf-8')
        return pd.read_csv(StringIO(csv_content))
    except Exception as e:
        print(f"Error reading data from S3: {e}")
        return None

# Function to check password
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

# Main application flow
if not check_password():
    st.stop()  # Do not continue if password validation fails.

# Load data from S3
file_key = 'Good_copy_fixed_anonymised_data.csv'
data = read_data_from_s3(AWS_BUCKET, file_key)

# Check if data was successfully loaded
if data is None:
    st.error("Failed to load data from S3. Please check your bucket name and file key.")
    st.stop()  # Stop execution if data loading fails

# SIDEBAR
with st.sidebar:
    st.markdown("[Ask DGP](_main.py)")
    st.markdown("[About Us](_aboutus.py)")
    st.markdown("[Methodology](_methodology.py)")

# Initialize messages in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello there! Please enter your query to continue."}]

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Function to chunk data into manageable pieces
def chunk_data(data, chunk_size=5):
    """Chunk a DataFrame into smaller DataFrames."""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

# Function to search for answers in the chunks using fuzzy matching
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

# Create chunks of the DataFrame
data_chunks = chunk_data(data, chunk_size=5)

# Specify the fields to filter by
query_field = "Details of Query"
reply_field = "Reply"
additional_field = "Additional Comments"

# Gather user input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Search for relevant replies based on the user's query
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