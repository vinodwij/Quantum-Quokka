import streamlit as st
import os

def load_css(file_name="style.css"):
    """Load custom CSS from a file located in the project root."""
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_name)
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def load_css_once(file_name="style.css"):
    """Load CSS only once per user session."""
    if not st.session_state.get("css_loaded"):
        load_css(file_name)
        st.session_state["css_loaded"] = True
