import streamlit as st
import mysql.connector
import os
import pandas as pd
from utils.utils import load_css_once

load_css_once()

st.set_page_config(page_title="All Demands", layout="wide")
st.title("Welcome to the Hayleys Group Digital Transformation Demand Dashboard")

from login import login_gate, check_permission, logout
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

# Load DB credentials from secrets.toml
DB_HOST = st.secrets["db"]["host"]
DB_NAME = st.secrets["db"]["name"]
DB_USER = st.secrets["db"]["user"]
DB_PASS = st.secrets["db"]["pass"]


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def fetch_all_demands():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            d.ID,
            d.Name AS DemandName,
            d.Description,
            d.ReceivedDate,
            d.Status,
            d.GoLiveDate,
            d.AbandonmentReason,
            d.Phase,
            d.DeliveryDomain,
            d.ServiceCategory,
            d.CompanyPriority,
            d.CompanyValueDescription,
            d.CompanyValueClassification,
            d.ImplementationComplexity,
            d.ImplementationCostEstimate,
            d.ImplementationDuration,

            c.Name AS Company,
            pm.Name AS ProjectManager,
            ow.Name AS Owner,
            v.Description AS Vendor,
            dto.Name AS DTOwner

        FROM Demand d
        LEFT JOIN Company c ON d.CompanyID = c.ID
        LEFT JOIN Employee pm ON d.ProjectManagerID = pm.ID
        LEFT JOIN Employee ow ON d.OwnerID = ow.ID
        LEFT JOIN Vendor v ON d.VendorID = v.ID
        LEFT JOIN Employee dto ON d.DTOwnerID = dto.ID
        ORDER BY d.ReceivedDate DESC
        """
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        st.error(f"❌ Error loading demand records: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# --- Fetch and display all demands ---
demands = fetch_all_demands()
if demands:
    df = pd.DataFrame(demands)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No demands found.")
