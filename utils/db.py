import mysql.connector
import streamlit as st
import re

def run_sql(query):
    # Check for potentially dangerous operations
    lowered = query.strip().lower()
    if re.search(r"\b(delete|drop|alter|truncate|insert|update)\b", lowered):
        return None, "🚫 Unsafe SQL command detected. Only read-only SELECT queries are allowed."

    try:
        conn = mysql.connector.connect(
            host=st.secrets["db"]["host"],
            user=st.secrets["db"]["user"],
            password=st.secrets["db"]["pass"],
            database=st.secrets["db"]["name"]
        )
        cursor = conn.cursor()
        cursor.execute(query)

        # Fetch results
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        return columns, rows

    except mysql.connector.ProgrammingError as pe:
        return None, f"❌ SQL Syntax Error: {pe}"

    except mysql.connector.Error as e:
        return None, f"❌ Database Error: {e}"

    except Exception as e:
        return None, f"❌ Unexpected Error: {e}"

    finally:
        try:
            if cursor: cursor.close()
            if conn: conn.close()
        except:
            pass
