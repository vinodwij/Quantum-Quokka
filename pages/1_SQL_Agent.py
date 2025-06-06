import streamlit as st
from utils.llm import call_llm
from utils.db import run_sql
from utils.helpers import extract_sql_from_response
import pandas as pd
import os
from login import login_gate, check_permission, logout
from utils.utils import load_css_once

load_css_once()



# Set page title
st.title("🧠 SQL Agent for Demand Management")

# Enforce login
login_gate()

# Get current page name
page_name = os.path.basename(__file__).replace(".py", "")

# Check permissions
check_permission(page_name)

# Sidebar content
with st.sidebar:
    name_display = st.session_state.name if st.session_state.name else "Unknown User"
    st.write(f"Logged in as: {name_display}")
    if st.button("Logout"):
        logout()

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message:
            st.code(message["sql"], language="sql")
        if "dataframe" in message:
            st.dataframe(message["dataframe"])

# Chat input
user_input = st.chat_input("Ask a question about the database (e.g., 'Show me all active demands')")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Process LLM response
    with st.spinner("Thinking..."):
        llm_response = call_llm(user_input)
        
        # Prepare assistant message
        assistant_message = {"role": "assistant", "content": f"#### 🧠 LLM Response:\n{llm_response}"}
        
        # Extract and execute SQL if present
        sql_query = extract_sql_from_response(llm_response)
        if sql_query:
            assistant_message["sql"] = sql_query
            columns, result = run_sql(sql_query)
            if columns:
                df = pd.DataFrame(result, columns=columns)
                assistant_message["dataframe"] = df
            else:
                assistant_message["content"] += f"\n\n#### ⚠️ Database Error:\n{result}"
        else:
            assistant_message["content"] += "\n\n#### ⚠️ No valid SQL found in the response."
        
        # Add assistant message to chat history
        st.session_state.messages.append(assistant_message)
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(assistant_message["content"])
            if "sql" in assistant_message:
                st.code(assistant_message["sql"], language="sql")
            if "dataframe" in assistant_message:
                st.markdown("#### 📊 Results:")
                st.dataframe(assistant_message["dataframe"])