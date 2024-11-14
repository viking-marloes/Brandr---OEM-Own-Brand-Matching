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
    /* Main card styles */
    .product-card {
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        background: white;
        margin: 10px;
        transition: transform 0.3s;
        height: 100%;
    }

    /* GIANT matching buttons */
    .stButton > button {
        border-radius: 50% !important;
        width: 180px !important;
        height: 180px !important;
        font-size: 80px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    }

    /* Button hover effects */
    .stButton > button:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3) !important;
    }

    /* Button colors */
    button[kind="secondary"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    button[kind="primary"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }

    /* Layout improvements */
    .match-buttons {
        display: flex;
        justify-content: center;
        gap: 60px;
        margin-top: 40px;
        padding: 20px;
    }
    
    .keyboard-shortcuts {
        margin-top: 20px;
        padding: 10px;
        background: #f0f2f6;
        border-radius: 10px;
        text-align: center;
    }
    
    .top-controls {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    .progress-section {
        padding: 10px;
        background: #f0f2f6;
        border-radius: 10px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Keyboard handler JavaScript
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowLeft' || e.key === 'n' || e.key === 'N') {
        document.querySelector('button[kind="secondary"]').click();
    } else if (e.key === 'ArrowRight' || e.key === 'y' || e.key === 'Y') {
        document.querySelector('button[kind="primary"]').click();
    }
});
</script>
""", unsafe_allow_html=True)

def get_product_image(sku):
    try:
        # Direct image URL construction (faster than scraping)
        image_url = f"https://www.vikingdirect.nl/catalogsearch/result/image?q={sku}"
        
        # Try to fetch the image
        response = requests.get(image_url, timeout=5)
        if response.status_code == 200:
            try:
                img = Image.open(BytesIO(response.content))
                return img
            except:
                pass
                
        # Fallback to detailed scraping if direct URL fails
        base_url = f"https://www.vikingdirect.nl/nl/-p-{sku}"
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            pattern = r'datalayerInitialObject\s*=\s*({.*?});'
            match = re.search(pattern, response.text, re.DOTALL)
            if match:
                json_text = match.group(1).replace("'", '"')
                data = json.loads(json_text)
                image_url = data.get("skuInfo", {}).get("skuImageURL", "")
                if image_url:
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url
                    response = requests.get(image_url, timeout=5)
                    if response.status_code == 200:
                        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error fetching image for SKU {sku}: {str(e)}")
    return None

@st.cache_data
def load_images_for_row(own_sku, oem_sku):
    own_image = get_product_image(str(own_sku))
    oem_image = get_product_image(str(oem_sku))
    return own_image, oem_image

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

# Rest of your code remains the same, but with these modifications for image loading:
if st.session_state.data is not None and st.session_state.current_index < len(st.session_state.data):
    current_row = st.session_state.data.iloc[st.session_state.current_index]
    
    with st.spinner('Loading product images...'):
        own_image, oem_image = load_images_for_row(
            current_row['Own SKU'],
            current_row['OEM SKU']
        )

    # Update the image display code:
    left_col, center_col, right_col = st.columns([4,3,4])
    
    with left_col:
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        st.subheader("Own Product")
        if own_image:
            st.image(own_image, use_column_width=True)
        else:
            st.image("https://via.placeholder.com/400x400.png?text=No+Image", use_column_width=True)
        st.markdown(f"**SKU:** {current_row['Own SKU']}")
        st.markdown(f"**Title:** {current_row['Own Title']}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        st.subheader("OEM Product")
        if oem_image:
            st.image(oem_image, use_column_width=True)
        else:
            st.image("https://via.placeholder.com/400x400.png?text=No+Image", use_column_width=True)
        st.markdown(f"**SKU:** {current_row['OEM SKU']}")
        st.markdown(f"**Title:** {current_row['OEM Title']}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Center column with GIANT buttons
    with center_col:
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        st.markdown("### AI Reasoning")
        st.markdown(f"**Score:** {current_row['Certainty Score']}")
        st.markdown("---")
        st.markdown(current_row['Reasoning'])
        
        st.markdown('<div class="match-buttons">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌", key="no_match", help="Not a match (N)", type="secondary"):
                handle_decision(False)
        with col2:
            if st.button("❤️", key="match", help="It's a match! (Y)", type="primary"):
                handle_decision(True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Keyboard shortcuts info
        st.markdown('<div class="keyboard-shortcuts">', unsafe_allow_html=True)
        st.markdown("""
        **Keyboard Shortcuts:**
        - Press 'Y' or '→' for Match
        - Press 'N' or '←' for No Match
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
