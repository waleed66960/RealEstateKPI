import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import components
from components.sidebar_language import setup_language_sidebar
from components.file_upload import file_upload_component
from components.manual_input import manual_input_component
from components.metric_selector import metric_selector_component
from components.analysis_display import analysis_display_component
from components.currency_selector import currency_selector_component
from components.analysis_history import analysis_history_component, save_analysis_history
from auth.login import login_component
from auth.signup import signup_component
from auth.subscription import subscription_component
from utils.localization import get_text
from core.analyzer import RealEstateAnalyzer
from database.init_db import initialize_database

def main():
    """Main application function"""
    
    # Initialize session state
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'subscribed' not in st.session_state:
        st.session_state.subscribed = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'selected_kpis' not in st.session_state:
        st.session_state.selected_kpis = []
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
    # Initialize database safely
    if 'database_initialized' not in st.session_state:
        try:
            st.session_state.database_initialized = initialize_database()
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
            st.session_state.database_initialized = False
    
    # Setup language sidebar and currency selector
    setup_language_sidebar()
    currency_selector_component()
    
    # Page configuration
    st.set_page_config(
        page_title=get_text("app_title"),
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for RTL support
    if st.session_state.language == 'ar':
        st.markdown("""
        <style>
        .main > div {
            direction: rtl;
            text-align: right;
        }
        .stSelectbox > div > div {
            direction: ltr;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Main title
    st.title(get_text("app_title"))
    st.markdown(get_text("app_description"))
    
    # Authentication flow
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs([get_text("login"), get_text("signup")])
        
        with tab1:
            login_component()
        
        with tab2:
            signup_component()
    
    elif not st.session_state.subscribed:
        st.warning(get_text("subscription_required"))
        subscription_component()
    
    else:
        # Main application interface
        st.success(get_text("welcome_message"))
        
        # Create main tabs
        tab1, tab2 = st.tabs([get_text("new_analysis"), get_text("analysis_history")])
        
        with tab2:
            analysis_history_component()
        
        with tab1:
            # Data input section
            st.header(get_text("data_input_header"))
        
        input_method = st.radio(
            get_text("choose_input_method"),
            [get_text("file_upload"), get_text("manual_input")]
        )
        
        if input_method == get_text("file_upload"):
            data = file_upload_component()
        else:
            # First show metric selector to determine required fields
            selected_kpis = metric_selector_component()
            if selected_kpis:
                data = manual_input_component(selected_kpis)
            else:
                st.info(get_text("select_kpis_first"))
                data = None
        
        # Analysis section
        if data is not None and not data.empty:
            st.header(get_text("analysis_header"))
            
            # Metric selector (if not already shown)
            if input_method == get_text("file_upload"):
                selected_kpis = metric_selector_component()
            else:
                # Use the selected_kpis from manual input
                selected_kpis = st.session_state.get('selected_kpis', [])
            
            if selected_kpis:
                # Perform analysis
                analyzer = RealEstateAnalyzer()
                results = analyzer.analyze(data, selected_kpis)
                st.session_state.analysis_results = results
                
                # Display results
                analysis_display_component(results, selected_kpis)
                
                # Save analysis to history
                if st.button(get_text("save_analysis")):
                    analysis_name = st.text_input(
                        get_text("analysis_name"),
                        value=f"Analysis {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                    if save_analysis_history(results, selected_kpis, analysis_name):
                        st.success(get_text("analysis_saved"))
            else:
                st.warning(get_text("no_kpis_selected"))

if __name__ == "__main__":
    main()
