import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import re
import io
import json
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
    /* MASSIVE matching buttons */
    .stButton > button {
        border-radius: 50% !important;
        width: 250px !important;
        height: 250px !important;
        font-size: 120px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important;
        transition: all 0.3s !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2) !important;
    }

    .stButton > button:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3) !important;
    }

    button[kind="secondary"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    button[kind="primary"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }

    .match-buttons {
        display: flex;
        justify-content: center;
        gap: 80px;
        margin: 40px 0;
        padding: 30px;
    }
    
    .product-card {
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        background: white;
        margin: 10px;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .product-image {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 300px;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def extract_sku_image_url(html_content):
    pattern = r'datalayerInitialObject\s*=\s*({.*?});'
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        json_text = match.group(1).replace("'", '"')
        try:
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

def generate_product_page_url(sku, country_code='nl'):
    base_urls = {
        "uk": "https://www.viking-direct.co.uk/en/-p-", 
        "gb": "https://www.viking-direct.co.uk/en/-p-",
        "ie": "https://www.vikingdirect.ie/en/-p-",
        "de": "https://www.viking.de/de/-p-",
        "at": "https://www.vikingdirekt.at/de/-p-",
        "nl": "https://www.vikingdirect.nl/nl/-p-",
        "benl": "https://www.vikingdirect.be/nl/-p-",
        "befr": "https://www.vikingdirect.be/fr/-p-",
        "bewa": "https://www.vikingdirect.be/fr/-p-",
        "chde": "https://www.vikingdirekt.ch/de/-p-",
        "chfr": "https://www.vikingdirekt.ch/fr/-p-",
        "lu": "https://www.viking-direct.lu/fr/-p-"
    }
    base_url = base_urls.get(country_code.lower())
    if base_url:
        return f"{base_url}{sku}"
    return None

@st.cache_data(ttl=3600)
def get_product_image(sku):
    if not sku or pd.isna(sku):
        return None
        
    for country in ['nl', 'uk', 'de']:
        try:
            product_url = generate_product_page_url(sku, country)
            if not product_url:
                continue
                
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            with st.spinner(f'Loading image for SKU {sku}...'):
                response = requests.get(product_url, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                    
                image_url = extract_sku_image_url(response.text)
                if not image_url:
                    continue
                    
                img_response = requests.get(image_url, headers=headers, timeout=10)
                if img_response.status_code == 200:
                    return Image.open(BytesIO(img_response.content))
                    
        except Exception as e:
            st.warning(f"Error loading image for SKU {sku}: {str(e)}")
            continue
            
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
    matched_indices = {match['index'] for match in st.session_state.matches if match['is_match'] is False}
    all_data = []
    
    for idx in range(len(st.session_state.data)):
        if idx not in matched_indices:
            all_data.append(st.session_state.data.iloc[idx].to_dict())
    
    if all_data:
        df = pd.DataFrame(all_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue(), len(all_data)
    return None, 0

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
    # Controls
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        jump_to = st.number_input("Jump to row", 
                                min_value=0, 
                                max_value=len(st.session_state.data)-1, 
                                value=st.session_state.current_index)
        if jump_to != st.session_state.current_index:
            st.session_state.current_index = jump_to

    with col2:
        excel_data, count = save_matches()
        if excel_data:
            st.download_button(
                label=f"💾 Save ({count} products)",
                data=excel_data,
                file_name=f"product_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with col3:
        st.write(f"Product {st.session_state.current_index + 1} of {len(st.session_state.data)}")

    # Main content
    if st.session_state.current_index < len(st.session_state.data):
        current_row = st.session_state.data.iloc[st.session_state.current_index]
        
        # Load images for current pair of SKUs
        left_col, center_col, right_col = st.columns([4,3,4])
        
        with left_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("Own Product")
            own_image = get_product_image(str(current_row['Own SKU']))
            st.markdown('<div class="product-image">', unsafe_allow_html=True)
            if own_image:
                st.image(own_image, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"**SKU:** {current_row['Own SKU']}")
            st.markdown(f"**Title:** {current_row['Own Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

        with center_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.markdown("### AI Reasoning")
            st.markdown(f"**Score:** {current_row['Certainty Score']}")
            st.markdown("---")
            st.markdown(current_row['Reasoning'])
            
            # MASSIVE buttons
            st.markdown('<div class="match-buttons">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌", key="no_match", help="Not a match (N)", type="secondary"):
                    handle_decision(False)
            with col2:
                if st.button("❤️", key="match", help="It's a match! (Y)", type="primary"):
                    handle_decision(True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Keyboard shortcuts
            st.info("""
            **Keyboard Shortcuts:**
            - Press 'Y' or '→' for Match
            - Press 'N' or '←' for No Match
            """)
            st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("OEM Product")
            oem_image = get_product_image(str(current_row['OEM SKU']))
            st.markdown('<div class="product-image">', unsafe_allow_html=True)
            if oem_image:
                st.image(oem_image, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"**SKU:** {current_row['OEM SKU']}")
            st.markdown(f"**Title:** {current_row['OEM Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.success("You've reviewed all products! Don't forget to save your progress.")
