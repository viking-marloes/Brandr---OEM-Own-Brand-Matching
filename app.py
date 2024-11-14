```python
# Update just the CSS portion - the rest of the code stays the same
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
        margin: 20px 0;
        padding: 20px;
    }
    
    /* Compact product cards */
    .product-card {
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        background: white;
        margin: 10px;
    }

    /* Fix image container */
    .product-image-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 10px 0;
        max-height: 300px;
        overflow: hidden;
    }

    /* Control image size */
    .product-image-container img {
        max-height: 250px !important;
        width: auto !important;
        object-fit: contain !important;
    }

    /* Compact headings */
    .product-card h2, .product-card h3 {
        margin: 0 !important;
        padding: 5px 0 !important;
    }

    /* Remove extra paragraph spacing */
    .product-card p {
        margin: 5px 0 !important;
        padding: 0 !important;
    }

    /* Streamlit element spacing fixes */
    div.stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Top controls area */
    .top-controls {
        background: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 15px;
    }

    /* Hide Streamlit defaults */
    div[data-testid="stToolbar"] {
        display: none;
    }

    .main > div {
        padding: 10px !important;
    }

    /* More compact info messages */
    .stAlert {
        padding: 10px !important;
        margin: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# And update the image display code in the main content section:
# (just these sections, rest remains the same)

with left_col:
    st.markdown('<div class="product-card">', unsafe_allow_html=True)
    st.subheader("Own Product")
    st.markdown('<div class="product-image-container">', unsafe_allow_html=True)
    own_image = get_product_image(str(current_row['Own SKU']))
    if own_image:
        st.image(own_image)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f"**SKU:** {current_row['Own SKU']}")
    st.markdown(f"**Title:** {current_row['Own Title']}")
    st.markdown('</div>', unsafe_allow_html=True)

# ... center column stays the same ...

with right_col:
    st.markdown('<div class="product-card">', unsafe_allow_html=True)
    st.subheader("OEM Product")
    st.markdown('<div class="product-image-container">', unsafe_allow_html=True)
    oem_image = get_product_image(str(current_row['OEM SKU']))
    if oem_image:
        st.image(oem_image)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f"**SKU:** {current_row['OEM SKU']}")
    st.markdown(f"**Title:** {current_row['OEM Title']}")
    st.markdown('</div>', unsafe_allow_html=True)
```
