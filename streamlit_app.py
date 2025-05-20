import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
import requests
import pandas as pd
import re

# Load environment variables from .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
LLM_API_URL = os.getenv("LLM_API_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

# Function to extract SQL code from LLM response
def extract_sql_from_response(response_text):
    match = re.search(r"```sql\n(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

# Function to call the LLM
def call_llm(user_query):
    schema_info = """
The database contains the following tables and columns:

- Employee(ID, Name, Title, Email, PhoneNumber, Status)
- Company(ID, Name, SectorCategory, OwnerID, Description)
- Vendor(ID, Description, ServiceCategory, ContactPersonName, ContactPersonPhoneNumber, ContactPersonEmail)
- Demand(ID, Name, Description, ReceivedDate, Status, GoLiveDate, AbandonmentReason, Phase, CompanyID, DeliveryDomain, ServiceCategory, CompanyPriority, CompanyValueDescription, CompanyValueClassification, ImplementationComplexity, ImplementationCostEstimate, ImplementationDuration, ProjectManagerID, OwnerID, VendorID, DTOwnerID)
- DAB(DemandID, Date, Status, Notes)
- Milestone(DemandID, Date, Description, AchievedOrNot)
- Status(DemandID, Date, Description, UpdatedBy)
- Proposal(DemandID, DateReceived, ProposalURL, ProposalStatus)
- Material(DemandID, URL, MaterialDescription, DateAdded)
- Meeting(DemandID, Date, Notes, RecordingURL)
- Issues(EmployeeID, DemandID, TimeRaised, IssueDescription, Status, ResolutionDescription, ResolutionTime)

Use these exact table and column names when generating SQL queries.
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful SQL assistant. "
                + schema_info +
                " Given a user's question, generate only the SQL query inside a Markdown SQL code block like this:\n```sql\nSELECT ...\n```"
            )
        },
        {"role": "user", "content": user_query}
    ]

    response = requests.post(
        LLM_API_URL,
        headers={"Content-Type": "application/json"},
        json={
            "model": LLM_MODEL,
            "messages": messages
        }
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"LLM Error: {response.status_code}"


# Function to run SQL query
def run_sql(query):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
        return columns, rows
    except Exception as e:
        return None, str(e)

# Streamlit UI
st.set_page_config(page_title="SQL Chatbot", layout="centered")
st.title("🧠 SQL Chatbot for Demand Management")

user_input = st.text_input("Ask a question about the database:", placeholder="E.g. Show me all active demands")

if st.button("Submit") and user_input:
    with st.spinner("Thinking..."):
        llm_response = call_llm(user_input)
        st.markdown("#### 🧠 LLM Response:")
        st.code(llm_response, language="markdown")

        sql_query = extract_sql_from_response(llm_response)
        if sql_query:
            st.markdown("#### 📝 SQL Query:")
            st.code(sql_query, language="sql")
            
            columns, result = run_sql(sql_query)
            if columns:
                st.markdown("#### 📊 Results:")
                df = pd.DataFrame(result, columns=columns)
                st.dataframe(df)

            else:
                st.error(f"Database Error: {result}")
        else:
            st.warning("No valid SQL found in the response.")
