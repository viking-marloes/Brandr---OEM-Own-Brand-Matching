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
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        background: white;
        margin: 10px;
        transition: transform 0.3s;
        height: 100%;
    }
    .product-card:hover {
        transform: translateY(-5px);
    }
    .stButton > button {
        border-radius: 50% !important;
        width: 120px !important;
        height: 120px !important;
        font-size: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important;
        transition: transform 0.2s !important;
    }
    .stButton > button:hover {
        transform: scale(1.1) !important;
    }
    .match-buttons {
        display: flex;
        justify-content: center;
        gap: 40px;
        margin-top: 30px;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    .progress-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background: #f0f2f6;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .download-section {
        padding: 10px;
        border-radius: 10px;
        background: #f0f2f6;
        margin-top: 10px;
    }
    .top-controls {
        display: flex;
        gap: 20px;
        align-items: center;
        margin-bottom: 20px;
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton > button[kind="secondary"] {
        background-color: red !important;
        color: white !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Image loading functions
@st.cache_data(ttl=3600)
def fetch_image(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
    except:
        return None
    return None

def generate_product_page_url(sku, country_code='nl'):
    base_urls = {
        "nl": "https://www.vikingdirect.nl/nl/-p-",
        "uk": "https://www.viking-direct.co.uk/en/-p-",
        "de": "https://www.viking.de/de/-p-"
    }
    base_url = base_urls.get(country_code.lower())
    if base_url:
        return f"{base_url}{sku}"
    return None

def get_product_image(sku):
    try:
        # Try multiple country codes if one fails
        for country in ['nl', 'uk', 'de']:
            product_url = generate_product_page_url(sku, country)
            if not product_url:
                continue
            
            response = requests.get(product_url, timeout=10)
            if response.status_code != 200:
                continue
                
            pattern = r'datalayerInitialObject\s*=\s*({.*?});'
            match = re.search(pattern, response.text, re.DOTALL)
            if not match:
                continue
                
            json_text = match.group(1).replace("'", '"')
            try:
                data = json.loads(json_text)
                image_url = data.get("skuInfo", {}).get("skuImageURL", "")
                if image_url:
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url
                    elif image_url.startswith("/"):
                        image_url = f"https://www.vikingdirect.{country}" + image_url
                    elif not image_url.startswith("http"):
                        image_url = "https://" + image_url
                        
                    img_data = fetch_image(image_url)
                    if img_data:
                        return Image.open(BytesIO(img_data))
            except:
                continue
    except Exception as e:
        print(f"Error fetching image for SKU {sku}: {str(e)}")
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
    # Top controls section
    st.markdown('<div class="top-controls">', unsafe_allow_html=True)
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
        st.markdown(f"### {st.session_state.current_index + 1} / {len(st.session_state.data)}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Main content
    if st.session_state.current_index < len(st.session_state.data):
        current_row = st.session_state.data.iloc[st.session_state.current_index]
        
        # Product displays
        left_col, center_col, right_col = st.columns([4,3,4])
        
        with left_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("Own Product")
            
            # Try to load image
            own_image = get_product_image(str(current_row['Own SKU']))
            if own_image:
                st.image(own_image, use_column_width=True)
            else:
                st.image("https://via.placeholder.com/400x400.png?text=No+Image", use_column_width=True)
            
            st.markdown(f"**SKU:** {current_row['Own SKU']}")
            st.markdown(f"**Title:** {current_row['Own Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

        with center_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.markdown("### AI Reasoning")
            st.markdown(f"**Score:** {current_row['Certainty Score']}")
            st.markdown("---")
            st.markdown(current_row['Reasoning'])
            
            # Larger matching buttons
            st.markdown('<div class="match-buttons">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌", key="no_match", help="Not a match", type="secondary"):
                    handle_decision(False)
            with col2:
                if st.button("❤️", key="match", help="It's a match!", type="primary"):
                    handle_decision(True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with right_col:
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            st.subheader("OEM Product")
            
            # Try to load image
            oem_image = get_product_image(str(current_row['OEM SKU']))
            if oem_image:
                st.image(oem_image, use_column_width=True)
            else:
                st.image("https://via.placeholder.com/400x400.png?text=No+Image", use_column_width=True)
            
            st.markdown(f"**SKU:** {current_row['OEM SKU']}")
            st.markdown(f"**Title:** {current_row['OEM Title']}")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.success("You've reviewed all products! Don't forget to save your progress.")
