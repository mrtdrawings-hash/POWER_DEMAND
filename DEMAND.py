import streamlit as st
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime, timedelta, timezone  # Added timezone here
from PIL import Image, ImageDraw, ImageFont

# 1. Page Configuration
st.set_page_config(
    page_title="Grid Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Inject Mobile-First Responsive CSS Styles
st.markdown("""
    <style>
    @media (max-width: 640px) {
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 0.4rem !important;
            padding-right: 0.4rem !important;
        }
        h1 {
            font-size: 1.4rem !important;
            text-align: center;
        }
        h3 {
            font-size: 1.1rem !important;
            text-align: center;
            margin-top: 5px !important;
            margin-bottom: 5px !important;
        }
        [data-testid="stMetric"] {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 5px 0px !important;
        }
    }
    .stImage > img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("National & State Grid Monitoring Dashboard")

# Core layout paths
current_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(current_dir, "GAUGE.jpg")
font_path = os.path.join(current_dir, "font.ttf")

# Define India Standard Time (IST) Zone object globally
IST = timezone(timedelta(hours=5, minutes=30))

# 3. Simulated Telemetry Engine for State & National Trends
def generate_24hr_grid_data():
    # Force current time to be in IST
    current_time = datetime.now(IST)
    time_slots = []
    state_vals = []
    national_vals = []
    
    for i in range(96, 0, -1):
        slot_time = current_time - timedelta(minutes=i * 15)
        time_slots.append(slot_time.strftime("%H:%M"))
        hour = slot_time.hour
        
        if 18 <= hour <= 22:
            s_demand = 16200 + np.random.randint(-150, 150)
            n_demand = 225000 + np.random.randint(-1500, 1500)
        elif 2 <= hour <= 6:
            s_demand = 13100 + np.random.randint(-200, 200)
            n_demand = 175000 + np.random.randint(-2000, 2000)
        else:
            s_demand = 14800 + np.random.randint(-250, 250)
            n_demand = 205000 + np.random.randint(-2500, 2500)
            
        state_vals.append(s_demand)
        national_vals.append(n_demand)
        
    return pd.DataFrame({
        "Time": time_slots, 
        "State Demand (MW)": state_vals,
        "National Demand (MW)": national_vals
    })

# Initialize data vectors
grid_df = generate_24hr_grid_data()

# Separate the numeric value and the unit for independent line rendering
live_state_val = grid_df["State Demand (MW)"].iloc[-1] 
state_lines = [f"{live_state_val:,}", "MW"]
live_state_metric_str = f"{live_state_val:,} MW"

live_national_val = grid_df["National Demand (MW)"].iloc[-1]
national_lines = [f"{live_national_val:,}", "MW"]
live_national_metric_str = f"{live_national_val:,} MW"

# Size Control Widget
gauge_size = st.slider("Adjust Gauge Size for View:", min_value=150, max_value=400, value=220, step=10)

# Force the last refresh indicator to also display in IST
st.markdown(
    f"<div style='text-align: center; font-size: 0.85rem; opacity: 0.8; margin-bottom: 15px; font-weight: bold;'>"
    f"Last Live Auto-Refresh: {datetime.now(IST).strftime('%H:%M:%S')} (Interval: 1 Min)</div>", 
    unsafe_allow_html=True
)

# Function to draw two lines of text perfectly stacked and centered in the optical area
def draw_two_lines_on_gauge(img_path, lines, font_size=55, line_spacing=12):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    font_loaded = False
    
    # 1. First choice: Local repository file match
    if os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, font_size)
            font_loaded = True
        except Exception:
            pass

    # 2. Second choice: Direct repository file name fall-through
    if not font_loaded:
        try:
            font = ImageFont.truetype("font.ttf", font_size)
            font_loaded = True
        except IOError:
            pass

    # 3. Streamlit Cloud Master Choice: Programmatically force sizing on the native internal engine
    if not font_loaded:
        base_font = ImageFont.load_default()
        try:
            font = base_font.font_variant(size=font_size)
        except AttributeError:
            font = base_font
        
    img_w, img_h = img.size
    
    bbox_line1 = draw.textbbox((0, 0), lines[0], font=font)
    bbox_line2 = draw.textbbox((0, 0), lines[1], font=font)
    
    h1 = bbox_line1[3] - bbox_line1[1]
    h2 = bbox_line2[3] - bbox_line2[1]
    total_text_height = h1 + line_spacing + h2
    
    start_y = (img_h - total_text_height) // 2 + 10
    
    w1 = bbox_line1[2] - bbox_line1[0]
    x1 = (img_w - w1) // 2
    draw.text((x1, start_y), lines[0], fill=(255, 255, 255), font=font)
    
    w2 = bbox_line2[2] - bbox_line2[0]
    x2 = (img_w - w2) // 2
    draw.text((x2, start_y + h1 + line_spacing), lines[1], fill=(255, 255, 255), font=font)
    
    return img

# 4. Main Layout Columns
col_state, col_national = st.columns(2)

# --- STATE DEMAND PANEL ---
with col_state:
    st.markdown("### Tamil Nadu State Demand")
    st.metric(label="Live TN Demand", value=live_state_metric_str, delta="-142 MW vs Last Hour")
    
    try:
        img_state = draw_two_lines_on_gauge(image_path, state_lines, font_size=55)
        st.image(img_state, width=gauge_size)
    except FileNotFoundError:
        st.error("State gauge image missing.")

# --- NATIONAL DEMAND PANEL ---
with col_national:
    st.markdown("### All India National Demand")
    st.metric(label="Live National Demand", value=live_national_metric_str, delta="+1,850 MW vs Last Hour")
    
    try:
        img_nat = draw_two_lines_on_gauge(image_path, national_lines, font_size=55)
        st.image(img_nat, width=gauge_size)
    except FileNotFoundError:
        st.error("National gauge image missing.")

st.markdown("---")

# 5. Bottom Section: Comparative Trend Chart
st.markdown("### Grid Load Curves (Trailing 24 Hours)")
trend_df_indexed = grid_df.set_index("Time")

chart_view = st.radio("Select Trend Line View:", ["Both", "State Only", "National Only"], horizontal=True)

if chart_view == "Both":
    st.line_chart(trend_df_indexed, y=["State Demand (MW)", "National Demand (MW)"], color=["#00d2ff", "#ffaa00"])
elif chart_view == "State Only":
    st.line_chart(trend_df_indexed, y="State Demand (MW)", color="#00d2ff")
else:
    st.line_chart(trend_df_indexed, y="National Demand (MW)", color="#ffaa00")

# 6. Native Auto-Refresh Loop
time.sleep(60)
st.rerun()
