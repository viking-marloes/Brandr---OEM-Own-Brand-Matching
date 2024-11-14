import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
import json
import os
from datetime import datetime

def main():
    st.set_page_config(layout="wide")
    
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
        st.session_state.data = pd.read_excel(uploaded_file)
        st.session_state.current_index = 0
        st.session_state.matches = []

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
                st.image(current_row['Own SKU Image'] if pd.notna(current_row['Own SKU Image']) else "placeholder.png", 
                        use_column_width=True)
                st.write(f"**SKU:** {current_row['Own SKU']}")
                st.write(f"**Title:** {current_row['Own Title']}")

            # Center column - Reasoning and Buttons
            with center_col:
                st.markdown("### AI Reasoning")
                st.write(f"**Certainty Score:** {current_row['Certainty Score']}")
                st.write(current_row['Reasoning'])
                
                # Like/Dislike buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("❌ No Match", use_container_width=True):
                        handle_decision(False)
                with col2:
                    if st.button("❤️ Match", use_container_width=True):
                        handle_decision(True)

            # Right column - OEM Product
            with right_col:
                st.subheader("OEM Product")
                st.image(current_row['OEM SKU Image'] if pd.notna(current_row['OEM SKU Image']) else "placeholder.png", 
                        use_container_width=True)
                st.write(f"**SKU:** {current_row['OEM SKU']}")
                st.write(f"**Title:** {current_row['OEM Title']}")

        else:
            st.success("You've reviewed all products! Don't forget to save your progress.")

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
        
        # Save to Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matched_products_{timestamp}.xlsx"
        df.to_excel(filename, index=False)
        
        # Create download button
        with open(filename, 'rb') as f:
            bytes_data = f.read()
        st.download_button(
            label="Download Matched Products",
            data=bytes_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Clean up the temporary file
        os.remove(filename)
        
        st.success(f"Saved {len(matched_data)} matches!")
    else:
        st.warning("No matched products to save!")

if __name__ == "__main__":
    main()
