# ================================================================
# WATER LEVEL CONTROL APP
# Minimal Style - Black & Orange
# ================================================================

import streamlit as st
import serial
import time
import pandas as pd
import plotly.graph_objects as go
from serial import SerialException
import threading

# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="Water Level Control",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# CUSTOM CSS - MINIMAL BLACK & ORANGE
# ================================================================
st.markdown("""
<style>
    /* MAIN BACKGROUND */
    .stApp {
        background-color: #0d0d0d;
    }
    
    /* TEXT COLOR */
    .stMarkdown, .stText, .stTitle, .stCaption, .stSubheader {
        color: #e6e6e6 !important;
    }
    
    /* METRIC CARDS */
    [data-testid="metric-container"] {
        background-color: #1a1a1a !important;
        border: 1px solid #e65c00 !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    
    [data-testid="metric-container"] label {
        color: #e65c00 !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        font-size: 12px !important;
        letter-spacing: 1px !important;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #ffffff !important;
        font-size: 28px !important;
    }
    
    /* BUTTONS */
    .stButton button {
        background-color: #e65c00 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 8px 24px !important;
        width: 100% !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        font-size: 13px !important;
    }
    
    .stButton button:hover {
        background-color: #ff751a !important;
        color: #000000 !important;
    }
    
    /* INPUT FIELDS */
    .stNumberInput input, .stTextInput input {
        background-color: #1a1a1a !important;
        border: 1px solid #333333 !important;
        border-radius: 4px !important;
        color: #ffffff !important;
    }
    
    .stNumberInput input:focus, .stTextInput input:focus {
        border-color: #e65c00 !important;
        box-shadow: 0 0 0 1px #e65c00 !important;
    }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #0d0d0d !important;
        border-right: 1px solid #1a1a1a !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e6e6e6 !important;
    }
    
    /* DIVIDER */
    hr {
        border-color: #e65c00 !important;
        opacity: 0.3 !important;
    }
    
    /* INFO BOX */
    .stAlert {
        background-color: #1a1a1a !important;
        border-left: 3px solid #e65c00 !important;
    }
    
    /* TABLES */
    .dataframe {
        background-color: #1a1a1a !important;
        color: #e6e6e6 !important;
    }
    
    .dataframe th {
        background-color: #e65c00 !important;
        color: #000000 !important;
    }
    
    /* CONTAINER BORDER */
    .element-container {
        border-color: #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

# ================================================================
# HEADER
# ================================================================
st.markdown(
    """
    <div style="
        border-bottom: 2px solid #e65c00;
        padding-bottom: 10px;
        margin-bottom: 30px;
    ">
        <h1 style="
            color: #ffffff;
            font-weight: 300;
            letter-spacing: 2px;
            margin: 0;
            font-size: 32px;
        ">
            WATER LEVEL CONTROL
        </h1>
        <p style="
            color: #e65c00;
            font-size: 14px;
            letter-spacing: 4px;
            margin: 0;
            text-transform: uppercase;
        ">
            real-time monitoring & pid tuning
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ================================================================
# SESSION STATE
# ================================================================
if 'ser' not in st.session_state:
    st.session_state.ser = None
    
if 'data' not in st.session_state:
    st.session_state.data = {
        'water_level': 0.0,
        'flow_in': 0.0,
        'flow_out': 0.0,
        'pump': 'OFF'
    }
    
if 'pid_params' not in st.session_state:
    st.session_state.pid_params = {
        'kp': 60.0,
        'ki': 0.2,
        'ff': 0.70,
        'setpoint': 7.0
    }
    
if 'running' not in st.session_state:
    st.session_state.running = False

# ================================================================
# FUNCTIONS
# ================================================================
def init_serial(port, baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        return ser
    except SerialException:
        return None

def send_command(ser, command):
    if ser and ser.is_open:
        ser.write(f"{command}\n".encode())
        return True
    return False

def read_data(ser):
    try:
        if ser and ser.in_waiting:
            line = ser.readline().decode().strip()
            if line:
                values = line.split(',')
                if len(values) == 4:
                    return {
                        'water_level': float(values[0]),
                        'flow_in': float(values[1]),
                        'flow_out': float(values[2]),
                        'pump': 'ON' if int(values[3]) == 1 else 'OFF'
                    }
    except:
        pass
    return None

# ================================================================
# SIDEBAR - CONNECTION & PID
# ================================================================
with st.sidebar:
    st.markdown(
        """
        <h3 style="
            color: #e65c00;
            font-weight: 300;
            letter-spacing: 2px;
            margin-top: 0;
            text-transform: uppercase;
            font-size: 14px;
        ">
            connection
        </h3>
        """,
        unsafe_allow_html=True
    )
    
    port = st.text_input(
        "port",
        value="/dev/cu.usbmodem1101",
        label_visibility="collapsed"
    )
    
    if st.button("connect", use_container_width=True):
        st.session_state.ser = init_serial(port)
        if st.session_state.ser:
            st.success("connected")
            st.session_state.running = True
        else:
            st.error("connection failed")
    
    if st.button("disconnect", use_container_width=True):
        if st.session_state.ser:
            st.session_state.ser.close()
            st.session_state.ser = None
            st.session_state.running = False
        st.info("disconnected")
    
    st.divider()
    
    st.markdown(
        """
        <h3 style="
            color: #e65c00;
            font-weight: 300;
            letter-spacing: 2px;
            margin-top: 0;
            text-transform: uppercase;
            font-size: 14px;
        ">
            pid tuning
        </h3>
        """,
        unsafe_allow_html=True
    )
    
    new_kp = st.number_input(
        "Kp",
        value=st.session_state.pid_params['kp'],
        step=1.0,
        format="%.1f",
        label_visibility="collapsed"
    )
    
    new_ki = st.number_input(
        "Ki",
        value=st.session_state.pid_params['ki'],
        step=0.1,
        format="%.1f",
        label_visibility="collapsed"
    )
    
    new_ff = st.number_input(
        "FF_Gain",
        value=st.session_state.pid_params['ff'],
        step=0.05,
        format="%.2f",
        label_visibility="collapsed"
    )
    
    new_setpoint = st.number_input(
        "Setpoint (cm)",
        value=st.session_state.pid_params['setpoint'],
        step=0.5,
        format="%.1f",
        label_visibility="collapsed"
    )
    
    if st.button("apply", use_container_width=True):
        st.session_state.pid_params['kp'] = new_kp
        st.session_state.pid_params['ki'] = new_ki
        st.session_state.pid_params['ff'] = new_ff
        st.session_state.pid_params['setpoint'] = new_setpoint
        
        if st.session_state.ser:
            cmd = f"P{new_kp},I{new_ki},F{new_ff},S{new_setpoint}"
            if send_command(st.session_state.ser, cmd):
                st.success("parameters sent")
            else:
                st.error("send failed")
        else:
            st.warning("not connected")

# ================================================================
# MAIN CONTENT
# ================================================================
if st.session_state.running and st.session_state.ser:
    # METRICS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "water level",
            f"{st.session_state.data['water_level']:.2f} cm",
            delta=f"{(st.session_state.data['water_level'] - st.session_state.pid_params['setpoint']):+.2f} cm"
        )
    
    with col2:
        st.metric(
            "flow in",
            f"{st.session_state.data['flow_in']:.1f} L/m"
        )
    
    with col3:
        st.metric(
            "flow out",
            f"{st.session_state.data['flow_out']:.1f} L/m"
        )
    
    with col4:
        st.metric(
            "pump",
            f"{st.session_state.data['pump']}"
        )
    
    # CHARTS
    st.divider()
    
    if 'history' not in st.session_state:
        st.session_state.history = {
            'time': [],
            'water_level': [],
            'flow_in': [],
            'flow_out': []
        }
    
    # READ DATA LOOP
    data = read_data(st.session_state.ser)
    if data:
        st.session_state.data = data
        
        # Update history
        st.session_state.history['time'].append(time.time())
        st.session_state.history['water_level'].append(data['water_level'])
        st.session_state.history['flow_in'].append(data['flow_in'])
        st.session_state.history['flow_out'].append(data['flow_out'])
        
        # Keep last 100 points
        if len(st.session_state.history['time']) > 100:
            for key in st.session_state.history:
                st.session_state.history[key] = st.session_state.history[key][-100:]
    
    # PLOT
    if len(st.session_state.history['time']) > 1:
        df = pd.DataFrame({
            'time': st.session_state.history['time'],
            'water_level': st.session_state.history['water_level'],
            'flow_in': st.session_state.history['flow_in'],
            'flow_out': st.session_state.history['flow_out']
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['water_level'],
            mode='lines',
            name='Water Level',
            line=dict(color='#e65c00', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=[st.session_state.pid_params['setpoint']] * len(df),
            mode='lines',
            name='Setpoint',
            line=dict(color='#ffffff', width=1, dash='dash')
        ))
        
        fig.update_layout(
            paper_bgcolor='#0d0d0d',
            plot_bgcolor='#0d0d0d',
            font=dict(color='#e6e6e6'),
            xaxis=dict(
                showgrid=True,
                gridcolor='#1a1a1a',
                title='time (s)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#1a1a1a',
                title='cm'
            ),
            legend=dict(
                font=dict(color='#e6e6e6'),
                bgcolor='rgba(13,13,13,0.8)'
            ),
            height=300,
            margin=dict(l=0, r=0, t=10, b=30)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # AUTO REFRESH
    time.sleep(0.1)
    st.rerun()

else:
    st.markdown(
        """
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: 400px;
            border: 1px solid #333333;
            border-radius: 8px;
            background-color: #0d0d0d;
        ">
            <p style="
                color: #666666;
                font-size: 18px;
                letter-spacing: 4px;
                text-transform: uppercase;
            ">
                connect to arduino
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
