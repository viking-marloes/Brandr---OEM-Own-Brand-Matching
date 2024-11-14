import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import re
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
    .product-card {
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background: white;
        margin: 10px;
        transition: transform 0.3s;
    }
    .product-card:hover {
        transform: translateY(-5px);
    }
    .stButton > button {
        border-radius: 50% !important;
        width: 80px !important;
        height: 80px !important;
        font-size: 30px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important;
    }
    .match-button {
        background-color: #4CAF50 !important;
    }
    .no-match-button {
        background-color: #f44336 !important;
    }
    .centered-content {
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

def generate_product_page_url(sku, country_code='nl'):
    base_urls = {
        "nl": "https://www.vikingdirect.nl/nl/-p-"
    }
    base_url = base_urls.get(country_code.lower())
    if base_url:
        return f"{base_url}{sku}"
    return None

def extract_sku_image_url(html_content):
    pattern = r'datalayerInitialObject\s*=\s*({.*?});'
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        json_text = match.group(1).replace("'", '"')
        try:
            import json
            data = json.loads(json_text)
            sku_image_url = data.get("skuInfo", {}).get("skuImageURL", "")
            if sku_image_url.startswith("//"):
                sku_image_url = "https:" + sku_image_url
            elif sku_image_url.startswith("/"):
                sku_image_url = "https://www.viking-direct.co.uk" + sku_image_url
            elif not sku_image_url.startswith("http"):
                sku_image_url = "https://" + sku_image_url
            return sku_image_url
        except json.JSONDecodeError:
            return None
    return None

def get_product_image(sku):
    try:
        product_url = generate_product_page_url(sku)
        if not product_url:
            return None
        
        response = requests.get(product_url)
        if response.status_code != 200:
            return None
            
        image_url = extract_sku_image_url(response.text)
        if not image_url:
            return None
            
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            return Image.open(BytesIO(img_response.content))
        return None
    except Exception as e:
        st.error(f"Error fetching image for SKU {sku}: {str(e)}")
        return None

def handle_decision(is_match):
    current_row = st.session_state.data.iloc[st.session_state.current_index].to_dict()
    st.session_state.matches.append({
        'index': st.session_state.current_index,
        'is_match': is_match,
        'data': current_row
    })
    if st.session_state.current_index < len(st.session_state.data) - 1:
        st.session_state.current_index += 1
        st.rerun()

def save_matches():
    if not st.session_state.matches:
        # Include all unmatched products as potential matches
        matched_indices = {match['index'] for match in st.session_state.matches}
        all_data = []
        
        for idx in range(len(st.session_state.data)):
            if idx not in matched_indices:
                all_data.append(st.session_state.data.iloc[idx].to_dict())
            else:
                match = next((m for m in st.session_state.matches if m['index'] == idx), None)
                if match and match['is_match']:
                    all_data.append(match['data'])
        
        if all_data:
            df = pd.DataFrame(all_data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button(
                label="Download Products",
                data=output.getvalue(),
                file_name=f"product_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success(f"Ready to download {len(all_data)} products!")
        else:
            st.warning("No products to save!")

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'matches' not in st.session_state:
    st.session_state.matches = []

st.title("Product Matcher 💘")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        if st.session_state.data is None:
            st.session_state.data = pd.read_excel(uploaded_file)
            st.session_state.current_index = 0
            st.session_state.matches = []
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")

if st.session_state.data is not None:
    # Progress and controls
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
        
        # Product displays
        left_col, center_col, right_col = st.columns([4,3,4])
        
        with left_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("Own Product")
            
            # Fetch and display image
            own_image = get_product_image(current_row['Own SKU'])
            if own_image:
                st.image(own_image, use_column_width=True)
            
            st.markdown(f"**SKU:** {current_row['Own SKU']}")
            st.markdown(f"**Title:** {current_row['Own Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

        with center_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.markdown("### AI Reasoning")
            st.markdown(f"**Certainty Score:** {current_row['Certainty Score']}")
            st.markdown("---")
            st.markdown(current_row['Reasoning'])
            
            # Tinder-style buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌", key="no_match", help="Not a match"):
                    handle_decision(False)
            with col2:
                if st.button("❤️", key="match", help="It's a match!"):
                    handle_decision(True)
            st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("OEM Product")
            
            # Fetch and display image
            oem_image = get_product_image(current_row['OEM SKU'])
            if oem_image:
                st.image(oem_image, use_column_width=True)
            
            st.markdown(f"**SKU:** {current_row['OEM SKU']}")
            st.markdown(f"**Title:** {current_row['OEM Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.success("You've reviewed all products! Don't forget to save your progress.")
