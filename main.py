import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
import pandas as pd

from login import login_gate
login_gate()

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

st.set_page_config(page_title="All Demands", layout="wide")
st.title("Welcome to the Hayleys Group Digital Transformation Demand Dashboard")

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
