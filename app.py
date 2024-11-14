import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Must be the first Streamlit command
st.set_page_config(
    page_title="Product Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for styling
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 20px;
    }
    .markdown-text-container {
        max-height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

def handle_decision(is_match):
    current_row = st.session_state.data.iloc[st.session_state.current_index].to_dict()
    st.session_state.matches.append({
        'index': st.session_state.current_index,
        'is_match': is_match,
        'data': current_row
    })
    if st.session_state.current_index < len(st.session_state.data) - 1:
        st.session_state.current_index += 1
        st.experimental_rerun()

def save_matches():
    if not st.session_state.matches:
        st.warning("No matches to save!")
        return

    # Create a DataFrame with only the matched products
    matched_data = [match['data'] for match in st.session_state.matches if match['is_match']]
    if matched_data:
        df = pd.DataFrame(matched_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Create download button
        st.download_button(
            label="Download Matched Products",
            data=output.getvalue(),
            file_name=f"matched_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success(f"Ready to download {len(matched_data)} matches!")
    else:
        st.warning("No matched products to save!")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'matches' not in st.session_state:
    st.session_state.matches = []

st.title("Product Matcher")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx', 'xls'])

if uploaded_file is not None and st.session_state.data is None:
    try:
        st.session_state.data = pd.read_excel(uploaded_file)
        st.session_state.current_index = 0
        st.session_state.matches = []
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")

if st.session_state.data is not None:
    # Jump to specific row
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        jump_to = st.number_input("Jump to row", 
                                min_value=0, 
                                max_value=len(st.session_state.data)-1, 
                                value=st.session_state.current_index)
        if jump_to != st.session_state.current_index:
            st.session_state.current_index = jump_to

    with col2:
        if st.button("Save Progress"):
            save_matches()

    with col3:
        st.write(f"Product {st.session_state.current_index + 1} of {len(st.session_state.data)}")

    # Main content
    if st.session_state.current_index < len(st.session_state.data):
        current_row = st.session_state.data.iloc[st.session_state.current_index]
        
        # Create three columns for the main content
        left_col, center_col, right_col = st.columns([4,3,4])
        
        # Left column - Own Product
        with left_col:
            st.subheader("Own Product")
            st.markdown("---")
            st.markdown(f"**SKU:** {current_row['Own SKU']}")
            st.markdown(f"**Title:** {current_row['Own Title']}")
            st.markdown(f"**Category:** {current_row['Category']}")

        # Center column - Reasoning and Buttons
        with center_col:
            st.markdown("### AI Reasoning")
            st.markdown(f"**Certainty Score:** {current_row['Certainty Score']}")
            st.markdown("---")
            st.markdown(current_row['Reasoning'])
            
            # Like/Dislike buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ No Match", use_container_width=True, key="no_match"):
                    handle_decision(False)
            with col2:
                if st.button("❤️ Match", use_container_width=True, key="match"):
                    handle_decision(True)

        # Right column - OEM Product
        with right_col:
            st.subheader("OEM Product")
            st.markdown("---")
            st.markdown(f"**SKU:** {current_row['OEM SKU']}")
            st.markdown(f"**Title:** {current_row['OEM Title']}")

        # Keyboard shortcuts info
        st.markdown("---")
        st.markdown("""
        **Keyboard shortcuts:**
        - Press 'Y' or '→' for Match
        - Press 'N' or '←' for No Match
        """)

    else:
        st.success("You've reviewed all products! Don't forget to save your progress.")
