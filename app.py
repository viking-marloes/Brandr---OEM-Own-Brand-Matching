import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import re
import io
import json
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor

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
    }

    button[kind="secondary"] {
        background-color: #ff4b4b !important;
    }
    button[kind="primary"] {
        background-color: #4CAF50 !important;
    }

    .match-buttons {
        display: flex;
        justify-content: center;
        gap: 80px;
        margin: 20px 0;
    }
    
    .product-card {
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        background: white;
        margin: 10px;
    }

    /* Fixed size image container */
    .product-image-container {
        width: 100%;
        height: 80px;  /* Fixed small height */
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 5px 0;
        background: #f8f9fa;
        border-radius: 8px;
    }

    /* Force consistent image size */
    .product-image-container img {
        max-height: 60px !important;  /* Very small fixed height */
        width: auto !important;
        object-fit: contain !important;
    }

    .product-info {
        margin-top: 10px;
    }

    .stSpinner > div {
        position: relative;
        top: 10px;
    }

    /* Hide default Streamlit elements */
    .stDeployButton, footer {
        display: none !important;
    }

    /* Compact layout */
    .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Keyboard shortcuts display */
    .shortcuts {
        background: #f0f2f6;
        padding: 8px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 0.9em;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for keyboard handling
if 'key_handled' not in st.session_state:
    st.session_state.key_handled = False

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

def load_and_resize_image(img_bytes, max_size=(60, 60)):
    if img_bytes:
        try:
            img = Image.open(BytesIO(img_bytes))
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return img
        except Exception:
            return None
    return None

@st.cache_data(ttl=3600)
def get_product_image(sku, country_code='nl'):
    if not sku or pd.isna(sku):
        return None
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Try direct product page first
        product_url = f"https://www.vikingdirect.nl/nl/-p-{sku}"
        response = requests.get(product_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            image_url = extract_sku_image_url(response.text)
            if image_url:
                img_response = requests.get(image_url, headers=headers, timeout=5)
                if img_response.status_code == 200:
                    return load_and_resize_image(img_response.content)
                    
    except Exception:
        pass
        
    return None

def handle_decision(is_match):
    if st.session_state.current_index < len(st.session_state.data):
        current_row = st.session_state.data.iloc[st.session_state.current_index].to_dict()
        st.session_state.matches.append({
            'index': st.session_state.current_index,
            'is_match': is_match,
            'data': current_row
        })
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
        
        left_col, center_col, right_col = st.columns([4,3,4])
        
        # Preload both images
        with st.spinner('Loading images...'):
            own_image = get_product_image(str(current_row['Own SKU']))
            oem_image = get_product_image(str(current_row['OEM SKU']))
        
        with left_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("Own Product")
            st.markdown('<div class="product-image-container">', unsafe_allow_html=True)
            if own_image:
                st.image(own_image)
            st.markdown('</div>', unsafe_allow_html=True)
            with st.container():
                st.markdown(f"**SKU:** {current_row['Own SKU']}")
                st.markdown(f"**Title:** {current_row['Own Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

        with center_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.markdown("### AI Reasoning")
            st.markdown(f"**Score:** {current_row['Certainty Score']}")
            st.markdown("---")
            st.markdown(current_row['Reasoning'])
            
            # Match buttons
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
            st.markdown('<div class="shortcuts">', unsafe_allow_html=True)
            st.markdown("""
            **Keyboard Shortcuts:**
            - Press 'Y' or '→' for Match
            - Press 'N' or '←' for No Match
            """)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("OEM Product")
            st.markdown('<div class="product-image-container">', unsafe_allow_html=True)
            if oem_image:
                st.image(oem_image)
            st.markdown('</div>', unsafe_allow_html=True)
            with st.container():
                st.markdown(f"**SKU:** {current_row['OEM SKU']}")
                st.markdown(f"**Title:** {current_row['OEM Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.success("You've reviewed all products! Don't forget to save your progress.")

# Add keyboard listener
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'y' || e.key === 'Y' || e.key === 'ArrowRight') {
        document.querySelector('button[kind="primary"]').click();
    } else if (e.key === 'n' || e.key === 'N' || e.key === 'ArrowLeft') {
        document.querySelector('button[kind="secondary"]').click();
    }
});
</script>
""", unsafe_allow_html=True)
