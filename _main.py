#WORKING VERSION OF FREQ SEARCHED TERMS (STATIC)
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

# Function to handle user input from suggestion buttons
def handle_suggestion(suggestion):
    """Process the suggestion and update the main chat with the response."""
    # Show the selected suggestion in the main chat
    st.session_state.messages.append({"role": "user", "content": suggestion})
    # Process the user input
    response_msg = process_user_input(suggestion)
    st.session_state.messages.append({"role": "assistant", "content": response_msg})

# Function to process user input
def process_user_input(prompt):
    data_chunks = chunk_data(data, chunk_size=5)
    query_field = "Details of Query"
    reply_field = "Reply"
    additional_field = "Additional Comments"

    # Search for relevant replies
    relevant_replies = search_chunks(prompt, data_chunks, query_field, reply_field, additional_field)

    if relevant_replies:
        search_summary = "\n".join([f"Reply: {r[0]}\nAdditional Comments: {r[1]}" for r in relevant_replies[:5]])
    else:
        search_summary = "Sorry, I couldn't find any relevant information based on your query."

    ai_prompt = f"""
    You are a helpful AI chatbot assistant. Here's a user's query and the corresponding search results from the data:

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
            temperature=0
        )
        msg = response.choices[0].message.content.strip()
    except Exception as e:
        msg = f"An error occurred: {str(e)}"

    return msg

# Sidebar Navigation
with st.sidebar:
    st.markdown("### Navigation")
    page = st.selectbox("Choose a page:", ["Ask DGP", "About Us", "Methodology"])
    
    st.write("""
         """) 
    
    # Suggestions for the user
    st.markdown("### Frequently Asked Questions")
    suggestions = [
        "I am having issue accessing DGP modules / dashboards",
        "I want to find out about billing for the subscription to DGP",
        "I would like to know how to acknowledge the Agency Monthly Access Control Report (ACR)",
        "I would like to find out how to remove User / User Access to DGP"
    ]
    
    # Display suggestion buttons in the sidebar
    for suggestion in suggestions:
        if st.button(suggestion):
            handle_suggestion(suggestion)

# Display chat messages for Ask DGP page
if page == "Ask DGP":
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Gather user input
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        response_msg = process_user_input(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response_msg})

# Content for About Us
elif page == "About Us":
    st.title("About Us")
    st.write("""
             
**1) Background**
       """)   
    st.write("""           
The Digital Governance Platform (DGP) is designed to transform Whole-of-Government ICT and SS Governance, with the goal of effectively managing ICT risks and enhancing the delivery of digital services.
The IT Service Management (ITSM) platform serves as the central system for agency users to report DGP-related issues or submit inquiries. Currently, a lean DGP Operations team manages initial ticket resolution by leveraging their expertise, historical responses, and available resources. Complex issues are escalated to Subject Matter Experts (SMEs), including Product Teams, Process Owners, Module Owners, and Technical Teams.
This process heavily relies on manual intervention to review historical responses to similar inquiries. Additionally, it may require referencing relevant resources (e.g., manuals, user guides, forms, notices, and announcements) available on the DGP Portal, which can be time-consuming and inefficient.
    """)    
    st.write("""
         """)       
    st.write("""   
                      
**2) Problem Statement**
                 """)  
    st.write(""" 
How can we streamline the ITSM inquiry process to:
                 """) 
    st.write(""" 
    a) Provide prompt and accurate responses to inquiries.
                 """)         
    st.write(""" 
    b) Reduce manual workload and enhance operational efficiency.
    """)      
    st.write("""
         """)    
    st.write("""   
                       
**3) Proposed Solution**
                 """)        
    st.write(""" 
By implementing a Large Language Model (LLM) to handle inquiries, we believe that the proof of concept (POC) can address repetitive ITSM queries, which constitute at least 60% of the ITSM tickets received. This initiative will enable:
                 """)       
    st.write(""" 
    a) Agency users to quickly resolve their concerns.
                 """)        
    st.write(""" 
    b) The Operations Team to focus on more complex and critical queries and tasks.
    """)   
    st.write("""
         """)       
    st.write(""" 
                        
**4) Role of the LLM in the Solution**
                 """)        
    st.write(""" 
Utilizing the capabilities of the LLM, it can replicate the Operations Team's ability to provide clarity and address agency users' inquiries based on relevant resources (e.g., advisories, circulars, user guides, functional specifications, and FAQs). For unresolved and complex queries, the LLM can recommend logging a ticket at the end of the session, ensuring that the Operations Team and SMEs follow up on these issues. Continuous enhancement can be achieved by updating the LLM with data from resolved complex issues, thereby reducing the need for manual intervention by the Operations Team and SMEs.
     """) 
    st.write("""
         """)        
    st.write("""  
                     
**5) Relevant Data Collected**
                 """)          
    st.write(""" 
The data utilized for this POC primarily originates from the ITSM. It has been anonymized and desensitized using the Cloak.
    """)  
    st.write("""
         """)      
    st.write("""            
             
**6) Features**
                 """)          
    st.write(""" 
The chatbot will include the following features:
                 """)          
    st.write(""" 
    a) Natural Language Processing (NLP): The ability to understand, interpret, and communicate in human language.
                 """)         
    st.write(""" 
    b) Clarity of Issues and Problems: The capability to delve deeper into users' questions by asking follow-up queries.
                 """)       
    st.write(""" 
    c) Contextualized Resolution: The ability to identify the user's intent and respond based on the interaction, providing tailored replies to resolve inquiries.
                 """)       
    st.write(""" 
    d) Augmentation for the Operations Team: The capacity to handle basic repetitive queries by filtering through past responses of similar nature.
    """)

# Content for Methodology
elif page == "Methodology":
    st.title("Methodology")
    st.image('Flow1.PNG')

    st.write('''
             
**Use Case 1**
    ''')

    st.write(''' 
Scenario: Users encounter difficulties in updating a record within Digital Governance Platform (DGP) and seek clarification on the update process. They turn to the DGP chatbot for assistance.
    ''')

    st.write(''' 
User Intent: Users want to understand how to carry out updates but encounter uncertainty regarding the inability to perform the update.
    ''')

    st.write(''' 
Chatbot Response: Within the sidebar, the chatbot offers a section titled "Frequently Asked Questions." Users can easily select their specific query from a predefined list, streamlining the process of obtaining assistance.
    ''')

    st.write(''' 
Outcome: Users receive immediate and relevant information regarding their inquiry, without the need to type out the query. This efficient interaction reduces frustration and improves user satisfaction, while also minimizing the need for further clarifications or escalation.
    ''')
    st.write("""
         """) 
    st.write('''  
                                    
**Use Case 2**
                 ''')

    st.write(''' 
Scenario: Users encounter difficulties in updating a record within DGP and seek clarification on the update process. They turn to the DGP chatbot for assistance.
                 ''')

    st.write(''' 
User Intent: Users want to understand how to carry out updates but encounter uncertainty regarding the inability to perform the update.
                 ''')

    st.write(''' 
Chatbot Response: The chatbot effectively addresses the user's inquiry by informing them that the system is currently locked for updates due to an ongoing exercise. This response not only clarifies the situation but also manages user expectations by explaining the reason for the system's unavailability.
                 ''')

    st.write(''' 
Outcome: Users gain a clear understanding of the constraints affecting their ability to perform updates, thereby reducing frustration and enhancing their overall experience with the system.
    ''')
    st.write("""
         """) 
    st.write(''' 
                     
**Use Case 3**
                 ''')

    st.write(''' 
Scenario: Users encounter difficulties in updating a record within DGP and seek clarification on the update process. They turn to the DGP chatbot for assistance.
                 ''')

    st.write(''' 
User Intent: Users want to understand how to carry out updates but encounter uncertainty regarding the inability to perform the update.
                 ''')

    st.write(''' 
Chatbot Response: After several rounds of clarifications, the chatbot is unable to provide a satisfactory answer to the user's inquiry. In response, it offers to assist the user in logging a case with the helpdesk, ensuring that their issue is escalated for further resolution.
                 ''')

    st.write(''' 
Outcome: The chatbot  redirected Users to the helpdesk for personalized support by logging a ticket on behalf of the user based on the conversation. This approach not only enhances user satisfaction but also maintains the chatbot's role as a facilitator for more complex issues, ultimately improving the overall user experience with the DGP system. 
    ''')
