import streamlit as st
from utils.llm import call_llm
from utils.db import run_sql
from utils.helpers import extract_sql_from_response
import pandas as pd

import os
from login import login_gate, check_permission, logout

st.title("🧠 SQL Chatbot for Demand Management")

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
                df = pd.DataFrame(result, columns=columns)
                st.markdown("#### 📊 Results:")
                st.dataframe(df)
            else:
                st.error(f"Database Error: {result}")
        else:
            st.warning("No valid SQL found in the response.")
