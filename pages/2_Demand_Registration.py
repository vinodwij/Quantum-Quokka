import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import date

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

# Function to fetch dropdown data from database
def get_dropdown_data(query):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        st.error(f"Dropdown load error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Function to extract ID from dropdown selection
def get_id(selection):
    try:
        return int(selection.split("(ID:")[1].split(")")[0])
    except:
        return None

# Set page configuration
st.set_page_config(page_title="Demand Management", layout="centered")
st.title("📋 Demand Management")

# Create tabs
tab1, tab2 = st.tabs(["Demand Registration", "Demand Update"])

# --- Demand Registration Tab ---
with tab1:
    st.header("Register New Demand")
    
    # Essential input fields
    name = st.text_input("Demand Name", key="reg_name")
    description = st.text_area("Description", key="reg_description")
    received_date = st.date_input("Received Date", value=date.today(), key="reg_received_date")
    status = st.selectbox("Status", ["Active", "Paused", "Abandoned"], key="reg_status")
    phase = st.selectbox("Phase", ["Identify", "Discovery", "Planning", "Delivery", "Live"], key="reg_phase")
    delivery_domain = st.selectbox("Delivery Domain", [
        "Workflow Automation", "Application Modernization", "IOT Driven Digitalization",
        "AI and Machine Learning", "Digital Literacy and Learning",
        "Data Intelligence & Analytics", "Agriculture Process Automation"
    ], key="reg_delivery_domain")
    service_category = st.selectbox("Service Category", ["Implementation", "Advisory"], key="reg_service_category")
    
    # Dropdowns from database
    company_list = get_dropdown_data("SELECT ID, Name FROM Company")
    employee_list = get_dropdown_data("SELECT ID, Name FROM Employee")
    
    company = st.selectbox("Company", [f"{n} (ID: {i})" for i, n in company_list], key="reg_company")
    project_manager = st.selectbox("Project Manager", [f"{n} (ID: {i})" for i, n in employee_list], key="reg_pm")
    owner = st.selectbox("Owner", [f"{n} (ID: {i})" for i, n in employee_list], key="reg_owner")
    dto = st.selectbox("DTO Owner", [f"{n} (ID: {i})" for i, n in employee_list], key="reg_dto")
    
    # Extract IDs
    company_id = get_id(company)
    pm_id = get_id(project_manager)
    owner_id = get_id(owner)
    dto_id = get_id(dto)
    
    # Submit button
    if st.button("Register Demand", key="reg_submit"):
        if not (name and description and received_date and status and phase and delivery_domain and service_category and company_id and pm_id and owner_id and dto_id):
            st.error("❌ Please fill all required fields.")
        else:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Demand (
                        Name, Description, ReceivedDate, Status, Phase, DeliveryDomain, ServiceCategory,
                        CompanyID, ProjectManagerID, OwnerID, DTOwnerID
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, description, received_date, status, phase, delivery_domain, service_category,
                    company_id, pm_id, owner_id, dto_id
                ))
                conn.commit()
                st.success(f"✅ Demand '{name}' registered successfully.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                cursor.close()
                conn.close()

# --- Demand Update Tab ---
with tab2:
    st.header("Update Demand Details")
    
    # Fetch demands for selection
    demand_list = get_dropdown_data("SELECT ID, Name FROM Demand")
    demand_options = ["Select a demand"] + [f"{n} (ID: {i})" for i, n in demand_list]
    
    # No default selection (index=0 for placeholder)
    selected_demand = st.selectbox("Select Demand to Update", demand_options, index=0, key="update_demand")
    
    if selected_demand != "Select a demand":
        demand_id = get_id(selected_demand)
        
        # Fetch current demand data
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Demand WHERE ID = %s", (demand_id,))
            demand = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"❌ Error fetching demand: {e}")
            demand = None
        
        if demand:
            # Non-essential fields for update
            go_live_date = st.date_input("Go Live Date (optional)", value=demand['GoLiveDate'] if demand['GoLiveDate'] else None, key="update_go_live")
            abandonment_reason = st.text_area("Abandonment Reason", value=demand['AbandonmentReason'] if demand['AbandonmentReason'] else "", placeholder="Only if status is 'Abandoned'", key="update_abandonment")
            priority = st.selectbox("Company Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['CompanyPriority']) if demand['CompanyPriority'] else 0, key="update_priority")
            value_description = st.text_area("Company Value Description", value=demand['CompanyValueDescription'] if demand['CompanyValueDescription'] else "", key="update_value_desc")
            value_classification = st.selectbox("Company Value Classification", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['CompanyValueClassification']) if demand['CompanyValueClassification'] else 0, key="update_value_class")
            complexity = st.selectbox("Implementation Complexity", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['ImplementationComplexity']) if demand['ImplementationComplexity'] else 0, key="update_complexity")
            cost_estimate = st.selectbox("Implementation Cost Estimate", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(demand['ImplementationCostEstimate']) if demand['ImplementationCostEstimate'] else 0, key="update_cost")
            duration = st.text_input("Implementation Duration (e.g., 3 months)", value=demand['ImplementationDuration'] if demand['ImplementationDuration'] else "", key="update_duration")
            
            # Vendor dropdown
            vendor_list = get_dropdown_data("SELECT ID, Description FROM Vendor")
            vendor_options = [f"{d} (ID: {i})" for i, d in vendor_list]
            vendor = st.selectbox("Vendor", ["No vendor selected"] + vendor_options, index=next((i + 1 for i, v in enumerate(vendor_list) if v[0] == demand['VendorID']), 0) if demand['VendorID'] else 0, key="update_vendor")
            vendor_id = get_id(vendor) if vendor != "No vendor selected" else None
            
            # Update button
            if st.button("Update Demand", key="update_submit"):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE Demand SET
                            GoLiveDate = %s,
                            AbandonmentReason = %s,
                            CompanyPriority = %s,
                            CompanyValueDescription = %s,
                            CompanyValueClassification = %s,
                            ImplementationComplexity = %s,
                            ImplementationCostEstimate = %s,
                            ImplementationDuration = %s,
                            VendorID = %s
                        WHERE ID = %s
                    """, (
                        go_live_date if demand['Status'] != "Abandoned" else None,
                        abandonment_reason if demand['Status'] == "Abandoned" else None,
                        priority, value_description, value_classification,
                        complexity, cost_estimate, duration, vendor_id, demand_id
                    ))
                    conn.commit()
                    st.success(f"✅ Demand '{selected_demand}' updated successfully.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                finally:
                    cursor.close()
                    conn.close()
    else:
        st.info("Please select a demand to view and update its details.")