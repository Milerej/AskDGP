# app.py
import os
import pandas as pd
import openai
import boto3
import streamlit as st
from dotenv import load_dotenv
from io import StringIO
from fuzzywuzzy import process
from collections import Counter

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("REGION_NAME")
AWS_BUCKET = os.getenv("BUCKET_NAME")
CORRECT_PASSWORD = os.getenv("PASSWORD")  # Make sure this is set in your environment

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize the S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Initialize Streamlit app
st.set_page_config(page_title="DGP Chatbot", page_icon="🤖")

# Automatically clear cache/session state on start
if 'initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state['initialized'] = True

# Sidebar Navigation
with st.sidebar:
    st.image("https://www.timeshighereducation.com/sites/default/files/sponsor-logo/white-gif-400px.gif")

# Main Page
st.title("Digital Governance Platform (DGP) Chatbot")
st.caption("A Streamlit chatbot powered by Govtech")
with st.expander("Disclaimer", expanded=False, icon="🚨"):
    st.write('''IMPORTANT NOTICE: This web application is developed as a proof-of-concept prototype. The information provided here is NOT intended for actual usage and should not be relied upon for making any decisions...''')

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
    """Returns True if the user has the correct password."""
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    user_password = st.text_input("Password", type="password", key="password", on_change=check_password_submit)

    return st.session_state.password_correct

def check_password_submit():
    """Function to handle password submission."""
    if st.session_state.password.strip() == CORRECT_PASSWORD.strip():
        st.session_state.password_correct = True
        st.success("Password correct!")
    else:
        st.error("😕 Password incorrect")

# Main application flow
if not check_password():
    st.stop()

# Load data from S3
file_key = 'Good_copy_fixed_anonymised_data.csv'
data = read_data_from_s3(AWS_BUCKET, file_key)

# Check if data was successfully loaded
if data is None or data.empty:
    st.error("Failed to load data from S3 or the data is empty. Please check your bucket name and file key.")
    st.stop()

# Check for necessary columns
required_columns = ["Details of Query", "Subject", "Reply", "Additional Comments"]
if not all(col in data.columns for col in required_columns):
    st.error(f"Missing required columns in the data: {set(required_columns) - set(data.columns)}")
    st.stop()

# Initialize messages and query counter in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello there! Please enter your query to continue."}]
if "query_counter" not in st.session_state:
    st.session_state.query_counter = Counter()

# Function to chunk data into manageable pieces
def chunk_data(data, chunk_size=5):
    """Chunk a DataFrame into smaller DataFrames."""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

# Function to process user input
def process_user_input(prompt):
    data_chunks = chunk_data(data)
    relevant_replies = []

    for chunk in data_chunks:
        if chunk is None or chunk.empty:
            st.error("Chunk is None or empty.")
            continue
        
        chunk["Details of Query"] = chunk["Details of Query"].fillna('').astype(str)
        chunk["Subject"] = chunk["Subject"].fillna('').astype(str)
        chunk["Reply"] = chunk["Reply"].fillna('').astype(str)
        chunk["Additional Comments"] = chunk["Additional Comments"].fillna('').astype(str)

        combined_str = ' '.join(chunk["Details of Query"].tolist() + chunk["Subject"].tolist())
        
        if prompt.lower() in combined_str.lower():
            for idx in chunk.index:
                relevant_replies.append((chunk.loc[idx, "Reply"], chunk.loc[idx, "Additional Comments"]))

    if not relevant_replies:
        queries = data["Details of Query"].fillna('').astype(str).tolist() + data["Subject"].fillna('').astype(str).tolist()
        responses = data[["Reply", "Additional Comments"]].fillna('')

        # Use a try-except to avoid IndexError
        try:
            matches = process.extract(prompt, queries, limit=None)

            for match in matches:
                index = queries.index(match[0])
                if index < len(responses):
                    relevant_replies.append((responses["Reply"].iloc[index], responses["Additional Comments"].iloc[index]))
        except Exception as e:
            st.error(f"Error processing matches: {str(e)}")

    if relevant_replies:
        search_summary = "\n".join([f"Reply: {r[0]}\nAdditional Comments: {r[1]}" for r in relevant_replies[:5]])
    else:
        search_summary = "Sorry, I couldn't find any relevant information based on your query."

    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-5:]])
    
    ai_prompt = f"""
    You are a helpful and professional AI chatbot assistant. 
    Your task is to provide clear, concise, and accurate responses to retrieve the data from the database to provide a relevant answer based on the user's query. 
    Please ensure your tone is friendly and supportive.
    Always check if you have addressed the issue. if it is not resolved after a few attempts to clarify, please offer to log a ticket.

    Here's the recent conversation context:
    {context}

    User's Query: {prompt}

    Here are some relevant replies extracted from the data:
    {search_summary}

    Based on the provided information, please formulate a response that:
    - Directly addresses the user's query.
    - Avoids unnecessary details.
    - Is structured clearly for easy understanding.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": ai_prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        msg = response.choices[0].message.content.strip()
    except Exception as e:
        msg = f"An error occurred: {str(e)}"

    return msg

# Function to generate a question from a term
def generate_question(term):
    prompt = f"Transform the following term into a clear question: '{term}'"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.3
        )
        question = response.choices[0].message.content.strip()
        return question
    except Exception as e:
        st.error(f"Error generating question: {str(e)}")
        return term  # Fallback to the term itself if there's an error

# Function to group similar subjects using fuzzy matching
def group_similar_subjects(subjects, threshold=80):
    """Group similar subjects based on a similarity threshold."""
    unique_subjects = []
    
    for subject in subjects:
        matches = process.extract(subject, unique_subjects, limit=None)
        if not matches or max([match[1] for match in matches]) < threshold:
            unique_subjects.append(subject)  # Add as a new unique subject
    
    return unique_subjects

# Sidebar Navigation
with st.sidebar:
    st.markdown("### Navigation")
    page = st.selectbox("Choose a page:", ["Ask DGP", "About Us", "Methodology"])

    st.write("") 

    # Get top searched terms from "Subject" only
    top_subjects = data["Subject"].dropna().value_counts().nlargest(20).index.tolist()
    
    # Combine and group the list
    combined_terms = top_subjects
    grouped_terms = group_similar_subjects(combined_terms)

    # Display suggestion buttons in the sidebar
    st.markdown("### Frequently Asked Questions")
    for term in grouped_terms:
        question = generate_question(term)  # Generate a question for each term
        if st.button(question):  # Use the generated question as the button label
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.query_counter[question] += 1
            response_msg = process_user_input(question)
            st.session_state.messages.append({"role": "assistant", "content": response_msg})

# Display chat messages for Ask DGP page
if page == "Ask DGP":
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Gather user input
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        st.session_state.query_counter[prompt] += 1
        
        with st.spinner("Processing your request..."):
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
